"""
Environment smoke-test for PyTorch, PyTorch Geometric, and TensorFlow.
Run:  python initial_test.py
"""

import os
import sys
import tempfile
import traceback

# ── colour helpers ────────────────────────────────────────────────────────────

_tty = sys.stdout.isatty()

def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _tty else text

PASS  = _c(32, "PASS")
FAIL  = _c(31, "FAIL")
SKIP  = _c(33, "SKIP")

# ── result tracking ───────────────────────────────────────────────────────────

_results: list[tuple[str, str, str]] = []   # (section, name, status)


def _section(title: str):
    bar = "─" * 60
    print(f"\n{bar}\n  {title}\n{bar}")


def _check(section: str, name: str, fn):
    try:
        detail = fn() or ""
        tag = PASS
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"
        tag = FAIL
        traceback.print_exc()
    raw = "PASS" if "PASS" in tag else ("FAIL" if "FAIL" in tag else "SKIP")
    _results.append((section, name, raw))
    suffix = f"  [{detail}]" if detail else ""
    print(f"  {tag}  {name}{suffix}")


def _skip(section: str, name: str, reason: str):
    print(f"  {SKIP}  {name}  ({reason})")
    _results.append((section, name, "SKIP"))


def _summary():
    bar = "═" * 60
    print(f"\n{bar}\n  SUMMARY\n{bar}")
    passed  = sum(1 for *_, s in _results if s == "PASS")
    failed  = sum(1 for *_, s in _results if s == "FAIL")
    skipped = sum(1 for *_, s in _results if s == "SKIP")
    print(f"  {PASS}: {passed}   {FAIL}: {failed}   {SKIP}: {skipped}   total: {len(_results)}")
    if failed:
        print(f"\n  {_c(31, 'Failed tests:')}")
        for sec, name, s in _results:
            if s == "FAIL":
                print(f"    [{sec}] {name}")
    print(bar)
    return failed == 0


# ── suppress framework noise ──────────────────────────────────────────────────

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# ── imports ───────────────────────────────────────────────────────────────────

try:
    import numpy as np
    import pandas as pd
    import scipy
    import sklearn
    import networkx as nx
    import torch
    import torch.nn as nn
    import torch_geometric as pyg
    from torch_geometric.data import Data
    from torch_geometric.loader import DataLoader
    from torch_geometric.nn import GCNConv, SAGEConv, GATConv, GINConv
    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")
except ImportError as e:
    sys.exit(f"[FATAL] import failed: {e}")

# ── global fixtures ───────────────────────────────────────────────────────────

CUDA   = torch.cuda.is_available()
MPS    = torch.backends.mps.is_available()
DEVICE = torch.device("cuda:0") if CUDA else torch.device("mps") if MPS else torch.device("cpu")
if MPS:
    tf.config.set_visible_devices([], "GPU")  # prevent tensorflow-metal from intercepting CPU ops
TF_GPU = bool(tf.config.list_physical_devices("GPU"))

# small graph shared across PyG tests
_EDGE = torch.tensor([[0,1,1,2,2,3],[1,0,2,1,3,2]], dtype=torch.long)
_X    = torch.randn(4, 16)
_DATA = Data(x=_X, edge_index=_EDGE)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Versions
# ─────────────────────────────────────────────────────────────────────────────

_section("Package Versions")

_rows = [
    ("python",          sys.version.split()[0]),
    ("numpy",           np.__version__),
    ("pandas",          pd.__version__),
    ("scipy",           scipy.__version__),
    ("scikit-learn",    sklearn.__version__),
    ("networkx",        nx.__version__),
    ("torch",           torch.__version__),
    ("torch-geometric", pyg.__version__),
    ("tensorflow",      tf.__version__),
    ("CUDA available",  str(CUDA) + (f" ({torch.cuda.get_device_name(0)})" if CUDA else "")),
    ("MPS available",   str(MPS)),
    ("TF GPU visible",  str(TF_GPU)),
]
for name, ver in _rows:
    print(f"  {'INFO':4}  {name:<20} {ver}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Core ML stack
# ─────────────────────────────────────────────────────────────────────────────

_section("Core ML Stack")


def test_numpy():
    a = np.random.randn(64, 64)
    b = a @ a.T
    assert b.shape == (64, 64)
    return f"matmul {b.shape}"

def test_scipy():
    m = scipy.sparse.random_array((50, 50), density=0.1, format="csr")
    return f"sparse nnz={m.nnz}"

def test_pandas():
    df = pd.DataFrame(np.random.randn(20, 4), columns=list("ABCD"))
    assert df.shape == (20, 4)
    return f"DataFrame {df.shape}"

def test_sklearn():
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=3, n_init=3, random_state=0).fit(np.random.randn(60, 4))
    return f"KMeans inertia {km.inertia_:.2f}"

def test_networkx():
    G = nx.path_graph(10)
    length = nx.shortest_path_length(G, 0, 9)
    return f"shortest path length {length}"


_check("Core", "numpy — matmul",           test_numpy)
_check("Core", "scipy — sparse matrix",    test_scipy)
_check("Core", "pandas — DataFrame",       test_pandas)
_check("Core", "scikit-learn — KMeans",    test_sklearn)
_check("Core", "networkx — shortest path", test_networkx)

# ─────────────────────────────────────────────────────────────────────────────
# 3. PyTorch — CPU
# ─────────────────────────────────────────────────────────────────────────────

_section("PyTorch — CPU")


def test_pt_tensor_ops():
    x = torch.randn(64, 32)
    y = x @ x.T
    assert y.shape == (64, 64)
    return f"matmul {y.shape}"

def test_pt_autograd():
    x = torch.randn(4, 4, requires_grad=True)
    loss = (x ** 2).sum()
    loss.backward()
    assert x.grad is not None
    return f"grad shape {x.grad.shape}"

def test_pt_nn_linear():
    layer = nn.Linear(32, 16)
    out = layer(torch.randn(8, 32))
    assert out.shape == (8, 16)
    return f"output {out.shape}"

def test_pt_nn_lstm():
    lstm = nn.LSTM(16, 32, batch_first=True)
    out, _ = lstm(torch.randn(4, 10, 16))
    assert out.shape == (4, 10, 32)
    return f"output {out.shape}"

def test_pt_dataloader():
    ds = torch.utils.data.TensorDataset(torch.randn(100, 8))
    dl = torch.utils.data.DataLoader(ds, batch_size=16, shuffle=True)
    batch = next(iter(dl))[0]
    assert batch.shape == (16, 8)
    return f"batch {batch.shape}"

def test_pt_numpy_interop():
    t = torch.randn(5, 5)
    n = t.numpy()
    t2 = torch.from_numpy(n)
    assert torch.allclose(t, t2)
    return "round-trip OK"

def test_pt_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "model.pt")
        data = {"w": torch.randn(4, 4)}
        torch.save(data, path)
        loaded = torch.load(path, weights_only=True)
        assert torch.allclose(data["w"], loaded["w"])
    return "save/load round-trip OK"


_check("PyTorch/CPU", "tensor ops",     test_pt_tensor_ops)
_check("PyTorch/CPU", "autograd",       test_pt_autograd)
_check("PyTorch/CPU", "nn.Linear",      test_pt_nn_linear)
_check("PyTorch/CPU", "nn.LSTM",        test_pt_nn_lstm)
_check("PyTorch/CPU", "DataLoader",     test_pt_dataloader)
_check("PyTorch/CPU", "tensor ↔ numpy", test_pt_numpy_interop)
_check("PyTorch/CPU", "save / load",    test_pt_save_load)

# ─────────────────────────────────────────────────────────────────────────────
# 4. PyTorch — GPU
# ─────────────────────────────────────────────────────────────────────────────

if CUDA:
    _section("PyTorch — GPU")

    def test_gpu_info():
        return (f"{torch.cuda.get_device_name(0)}, "
                f"CUDA {torch.version.cuda}, "
                f"devices={torch.cuda.device_count()}")

    def test_gpu_matmul():
        a = torch.randn(512, 512, device=DEVICE)
        b = torch.mm(a, a.T)
        torch.cuda.synchronize()
        assert b.device.type == "cuda"
        return f"shape {b.shape} on {b.device}"

    def test_gpu_transfer():
        cpu_t = torch.randn(128, 128)
        gpu_t = cpu_t.to(DEVICE)
        back  = gpu_t.cpu()
        assert torch.allclose(cpu_t, back)
        return "CPU → GPU → CPU values match"

    def test_gpu_autograd():
        x = torch.randn(32, 32, device=DEVICE, requires_grad=True)
        (x ** 2).sum().backward()
        assert x.grad is not None
        return f"grad norm {x.grad.norm():.4f}"

    def test_gpu_memory():
        alloc = torch.cuda.memory_allocated(DEVICE) / 1e6
        reserv = torch.cuda.memory_reserved(DEVICE) / 1e6
        return f"allocated {alloc:.1f} MB, reserved {reserv:.1f} MB"

    _check("PyTorch/GPU", "GPU info",         test_gpu_info)
    _check("PyTorch/GPU", "GPU matmul",       test_gpu_matmul)
    _check("PyTorch/GPU", "CPU↔GPU transfer", test_gpu_transfer)
    _check("PyTorch/GPU", "GPU autograd",     test_gpu_autograd)
    _check("PyTorch/GPU", "GPU memory",       test_gpu_memory)

# ─────────────────────────────────────────────────────────────────────────────
# 5. PyTorch — MPS
# ─────────────────────────────────────────────────────────────────────────────

if MPS:
    _section("PyTorch — MPS")

    def test_mps_info():
        return "Apple Metal (MPS) backend available"

    def test_mps_matmul():
        a = torch.randn(512, 512, device="mps")
        b = torch.mm(a, a.T)
        torch.mps.synchronize()
        assert b.device.type == "mps"
        return f"shape {b.shape} on {b.device}"

    def test_mps_transfer():
        cpu_t = torch.randn(128, 128)
        mps_t = cpu_t.to("mps")
        back  = mps_t.cpu()
        assert torch.allclose(cpu_t, back)
        return "CPU → MPS → CPU values match"

    def test_mps_autograd():
        x = torch.randn(32, 32, device="mps", requires_grad=True)
        (x ** 2).sum().backward()
        assert x.grad is not None
        return f"grad norm {x.grad.norm():.4f}"

    def test_mps_memory():
        alloc  = torch.mps.current_allocated_memory() / 1e6
        driver = torch.mps.driver_allocated_memory() / 1e6
        return f"current {alloc:.1f} MB, driver {driver:.1f} MB"

    _check("PyTorch/MPS", "MPS info",         test_mps_info)
    _check("PyTorch/MPS", "MPS matmul",       test_mps_matmul)
    _check("PyTorch/MPS", "CPU↔MPS transfer", test_mps_transfer)
    _check("PyTorch/MPS", "MPS autograd",     test_mps_autograd)
    _check("PyTorch/MPS", "MPS memory",       test_mps_memory)

# ─────────────────────────────────────────────────────────────────────────────
# 6. PyTorch Geometric — CPU
# ─────────────────────────────────────────────────────────────────────────────

_section("PyTorch Geometric — CPU")


def test_pyg_data():
    assert _DATA.num_nodes == 4
    assert _DATA.num_edges == 6
    return f"|V|={_DATA.num_nodes} |E|={_DATA.num_edges} x={list(_DATA.x.shape)}"

def test_pyg_gcnconv():
    out = GCNConv(16, 32)(_DATA.x, _DATA.edge_index)
    assert out.shape == (4, 32)
    return f"out {out.shape}"

def test_pyg_sageconv():
    out = SAGEConv(16, 32)(_DATA.x, _DATA.edge_index)
    assert out.shape == (4, 32)
    return f"out {out.shape}"

def test_pyg_gatconv():
    out = GATConv(16, 32, heads=2, concat=False)(_DATA.x, _DATA.edge_index)
    assert out.shape == (4, 32)
    return f"out {out.shape}"

def test_pyg_ginconv():
    out = GINConv(nn.Linear(16, 32))(_DATA.x, _DATA.edge_index)
    assert out.shape == (4, 32)
    return f"out {out.shape}"

def test_pyg_dataloader():
    graphs = [
        Data(x=torch.randn(5, 16), edge_index=torch.tensor([[0,1,2,3],[1,2,3,4]]))
        for _ in range(8)
    ]
    loader = DataLoader(graphs, batch_size=4)
    batch = next(iter(loader))
    assert batch.num_graphs == 4
    return f"batch graphs={batch.num_graphs} x={list(batch.x.shape)}"

def test_pyg_full_forward():
    class GCN_CPU(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = GCNConv(16, 8)
            self.conv2 = GCNConv(8, 2)
        def forward(self, x, edge_index):
            return self.conv2(torch.relu(self.conv1(x, edge_index)), edge_index)

    model = GCN_CPU()
    out   = model(_DATA.x, _DATA.edge_index)
    loss  = nn.CrossEntropyLoss()(out, torch.randint(0, 2, (4,)))
    loss.backward()
    return f"loss {loss.item():.4f}"


_check("PyG/CPU", "Data object",      test_pyg_data)
_check("PyG/CPU", "GCNConv",          test_pyg_gcnconv)
_check("PyG/CPU", "SAGEConv",         test_pyg_sageconv)
_check("PyG/CPU", "GATConv",          test_pyg_gatconv)
_check("PyG/CPU", "GINConv",          test_pyg_ginconv)
_check("PyG/CPU", "DataLoader/Batch", test_pyg_dataloader)
_check("PyG/CPU", "full GCN forward", test_pyg_full_forward)

# ─────────────────────────────────────────────────────────────────────────────
# 7. PyTorch Geometric — GPU
# ─────────────────────────────────────────────────────────────────────────────

if CUDA:
    _section("PyTorch Geometric — GPU")
    _DATA_GPU = _DATA.to(DEVICE)

    def test_pyg_gpu_data():
        assert _DATA_GPU.x.device.type == "cuda"
        return f"x on {_DATA_GPU.x.device}, edge_index on {_DATA_GPU.edge_index.device}"

    def test_pyg_gpu_gcnconv():
        out = GCNConv(16, 32).to(DEVICE)(_DATA_GPU.x, _DATA_GPU.edge_index)
        assert out.device.type == "cuda"
        return f"out {out.shape} on {out.device}"

    def test_pyg_gpu_sageconv():
        out = SAGEConv(16, 32).to(DEVICE)(_DATA_GPU.x, _DATA_GPU.edge_index)
        assert out.device.type == "cuda"
        return f"out {out.shape} on {out.device}"

    def test_pyg_gpu_gatconv():
        out = GATConv(16, 32, heads=2, concat=False).to(DEVICE)(_DATA_GPU.x, _DATA_GPU.edge_index)
        assert out.device.type == "cuda"
        return f"out {out.shape} on {out.device}"

    def test_pyg_gpu_full_forward():
        class GCN_GPU(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = GCNConv(16, 8)
                self.conv2 = GCNConv(8, 2)
            def forward(self, x, edge_index):
                return self.conv2(torch.relu(self.conv1(x, edge_index)), edge_index)

        model = GCN_GPU().to(DEVICE)
        out   = model(_DATA_GPU.x, _DATA_GPU.edge_index)
        loss  = nn.CrossEntropyLoss()(out, torch.randint(0, 2, (4,), device=DEVICE))
        loss.backward()
        return f"loss {loss.item():.4f}"

    _check("PyG/GPU", "Data → GPU",       test_pyg_gpu_data)
    _check("PyG/GPU", "GCNConv",          test_pyg_gpu_gcnconv)
    _check("PyG/GPU", "SAGEConv",         test_pyg_gpu_sageconv)
    _check("PyG/GPU", "GATConv",          test_pyg_gpu_gatconv)
    _check("PyG/GPU", "full GCN forward", test_pyg_gpu_full_forward)

# ─────────────────────────────────────────────────────────────────────────────
# 8. PyTorch Geometric — MPS
# ─────────────────────────────────────────────────────────────────────────────

if MPS:
    _section("PyTorch Geometric — MPS")
    _DATA_MPS = _DATA.to("mps")

    def test_pyg_mps_data():
        assert _DATA_MPS.x.device.type == "mps"
        return f"x on {_DATA_MPS.x.device}, edge_index on {_DATA_MPS.edge_index.device}"

    def test_pyg_mps_gcnconv():
        out = GCNConv(16, 32).to("mps")(_DATA_MPS.x, _DATA_MPS.edge_index)
        assert out.device.type == "mps"
        return f"out {out.shape} on {out.device}"

    def test_pyg_mps_sageconv():
        out = SAGEConv(16, 32).to("mps")(_DATA_MPS.x, _DATA_MPS.edge_index)
        assert out.device.type == "mps"
        return f"out {out.shape} on {out.device}"

    def test_pyg_mps_gatconv():
        out = GATConv(16, 32, heads=2, concat=False).to("mps")(_DATA_MPS.x, _DATA_MPS.edge_index)
        assert out.device.type == "mps"
        return f"out {out.shape} on {out.device}"

    def test_pyg_mps_full_forward():
        class GCN_MPS(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = GCNConv(16, 8)
                self.conv2 = GCNConv(8, 2)
            def forward(self, x, edge_index):
                return self.conv2(torch.relu(self.conv1(x, edge_index)), edge_index)

        model = GCN_MPS().to("mps")
        out   = model(_DATA_MPS.x, _DATA_MPS.edge_index)
        loss  = nn.CrossEntropyLoss()(out, torch.randint(0, 2, (4,), device="mps"))
        loss.backward()
        return f"loss {loss.item():.4f}"

    _check("PyG/MPS", "Data → MPS",       test_pyg_mps_data)
    _check("PyG/MPS", "GCNConv",          test_pyg_mps_gcnconv)
    _check("PyG/MPS", "SAGEConv",         test_pyg_mps_sageconv)
    _check("PyG/MPS", "GATConv",          test_pyg_mps_gatconv)
    _check("PyG/MPS", "full GCN forward", test_pyg_mps_full_forward)

# ─────────────────────────────────────────────────────────────────────────────
# 9. TensorFlow — CPU
# ─────────────────────────────────────────────────────────────────────────────

_section("TensorFlow — CPU")


def test_tf_tensor_ops():
    a = tf.random.normal([64, 64])
    b = tf.linalg.matmul(a, a)
    assert b.shape == (64, 64)
    return f"matmul {b.shape}"

def test_tf_keras_layer():
    layer = tf.keras.layers.Dense(32)
    out = layer(tf.random.normal([16, 64]))
    assert out.shape == (16, 32)
    return f"Dense output {out.shape}"

def test_tf_keras_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    out = model(tf.random.normal([8, 16]))
    assert out.shape == (8, 1)
    return f"output {out.shape}"

def test_tf_gradient_tape():
    x = tf.Variable(tf.random.normal([8, 8]))
    with tf.GradientTape() as tape:
        y = tf.reduce_sum(x ** 2)
    grad = tape.gradient(y, x)
    assert grad.shape == x.shape
    return f"grad shape {grad.shape}"

def test_tf_data_pipeline():
    options = tf.data.Options()
    options.threading.private_threadpool_size = 1
    ds = (tf.data.Dataset
          .from_tensor_slices(tf.random.normal([100, 8]))
          .batch(16)
          .with_options(options))
    batch = next(iter(ds))
    assert batch.shape == (16, 8)
    return f"batch {batch.shape}"

def test_tf_numpy_interop():
    t = tf.random.normal([4, 4])
    n = t.numpy()
    t2 = tf.constant(n)
    assert t2.shape == t.shape
    return "round-trip OK"

def test_tf_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "model.keras")
        model = tf.keras.Sequential([tf.keras.layers.Dense(4)])
        model.compile(optimizer="adam", loss="mse")
        model(tf.random.normal([2, 8]))          # build
        model.save(path)
        loaded = tf.keras.models.load_model(path)
        out = loaded(tf.random.normal([2, 8]))
        assert out.shape == (2, 4)
    return f"loaded output {out.shape}"


_check("TF/CPU", "tensor ops",        test_tf_tensor_ops)
_check("TF/CPU", "Keras Dense layer", test_tf_keras_layer)
_check("TF/CPU", "Keras Sequential",  test_tf_keras_model)
_check("TF/CPU", "GradientTape",      test_tf_gradient_tape)
if MPS:
    _skip("TF/CPU", "tf.data pipeline", "hangs on macOS/MPS")
else:
    _check("TF/CPU", "tf.data pipeline", test_tf_data_pipeline)
_check("TF/CPU", "tensor ↔ numpy",    test_tf_numpy_interop)
_check("TF/CPU", "save / load",       test_tf_save_load)

# ─────────────────────────────────────────────────────────────────────────────
# 10. TensorFlow — GPU
# ─────────────────────────────────────────────────────────────────────────────

_section("TensorFlow — GPU")

if not TF_GPU:
    for _name in ["GPU info", "GPU matmul", "Keras model on GPU", "GradientTape on GPU"]:
        _skip("TF/GPU", _name, "no GPU visible to TF")
else:
    def test_tf_gpu_info():
        gpus = tf.config.list_physical_devices("GPU")
        return f"{len(gpus)} GPU(s): " + ", ".join(g.name for g in gpus)

    def test_tf_gpu_matmul():
        with tf.device("/GPU:0"):
            a = tf.random.normal([256, 256])
            b = tf.linalg.matmul(a, a)
        assert b.shape == (256, 256)
        return f"shape {b.shape}"

    def test_tf_gpu_keras_model():
        with tf.device("/GPU:0"):
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(32, activation="relu"),
                tf.keras.layers.Dense(1),
            ])
            model.compile(optimizer="adam", loss="mse")
            out = model(tf.random.normal([8, 16]))
        assert out.shape == (8, 1)
        return f"output {out.shape}"

    def test_tf_gpu_gradient_tape():
        with tf.device("/GPU:0"):
            x = tf.Variable(tf.random.normal([32, 32]))
            with tf.GradientTape() as tape:
                y = tf.reduce_sum(x ** 2)
            grad = tape.gradient(y, x)
        assert grad.shape == x.shape
        return f"grad shape {grad.shape}"

    _check("TF/GPU", "GPU info",            test_tf_gpu_info)
    _check("TF/GPU", "GPU matmul",          test_tf_gpu_matmul)
    _check("TF/GPU", "Keras model on GPU",  test_tf_gpu_keras_model)
    _check("TF/GPU", "GradientTape on GPU", test_tf_gpu_gradient_tape)

# ─────────────────────────────────────────────────────────────────────────────
# 11. Cross-framework interop
# ─────────────────────────────────────────────────────────────────────────────

_section("Cross-framework Interop")


def test_torch_to_tf():
    t = torch.randn(6, 6)
    n = t.numpy()
    tf_t = tf.constant(n)
    assert tf_t.shape == t.shape
    return f"torch {t.shape} → numpy → tf {tf_t.shape}"

def test_tf_to_torch():
    t = tf.random.normal([6, 6])
    n = t.numpy()
    pt_t = torch.from_numpy(n)
    assert pt_t.shape == torch.Size([6, 6])
    return f"tf {t.shape} → numpy → torch {pt_t.shape}"

def test_sklearn_to_torch():
    from sklearn.preprocessing import StandardScaler
    X = np.random.randn(50, 8)
    X_scaled = StandardScaler().fit_transform(X)
    t = torch.from_numpy(X_scaled).float()
    assert t.shape == (50, 8)
    return f"sklearn scaled → torch {t.shape}"


_check("Interop", "torch → numpy → tf", test_torch_to_tf)
_check("Interop", "tf → numpy → torch", test_tf_to_torch)
_check("Interop", "sklearn → torch",    test_sklearn_to_torch)

# ─────────────────────────────────────────────────────────────────────────────

ok = _summary()
sys.exit(0 if ok else 1)
