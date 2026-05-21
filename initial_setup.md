# Initial Setup

Setup guide for the conda environment on the Gilbreth HPC cluster. For local installs, skip the `ssh` and `module` commands.

---

## Version Selection

When selecting package versions, work in this order:

1. **Python** — Check [devguide.python.org/versions](https://devguide.python.org/versions/) for stable, non-EOL releases. We use **Python 3.12**: released Oct 2023, EOL ~2028, well-supported across the entire ML stack.

2. **PyG first** — PyG lags PyTorch releases by 1–3 months, so start here to find the PyTorch ceiling. We use **PyG 2.7.0** (latest). Check [github.com/pyg-team/pytorch_geometric/releases](https://github.com/pyg-team/pytorch_geometric/releases) for which PyTorch versions it supports.

3. **PyTorch** — Use the latest PyTorch version PyG officially supports. PyG 2.7.0 → **PyTorch 2.8.0**. Check [pytorch.org/get-started/previous-versions](https://pytorch.org/get-started/previous-versions/). Note: PyTorch dropped conda distribution after 2.5 — install via pip with the CUDA wheel index.

4. **TensorFlow** — Independently versioned, but both torch and TF bundle CUDA libraries that can conflict. **TF 2.21.0 conflicts with torch 2.8.0**: TF requires `nvidia-nccl-cu12>=2.27.7`, torch pins `nvidia-nccl-cu12==2.27.3`. Resolve by using a TF version compatible with torch's nccl pin. See `environment.yml` for the resolved version.

---

## Login to Gilbreth

```bash
# Connect to any front-end node
ssh username@gilbreth.rcac.purdue.edu

# Connect to a specific front-end node (required for tmux session continuity)
ssh username@gilbreth-fe00.rcac.purdue.edu
```

> **Note**: Always connect to the same `-feXX` node where your `tmux` session is running.

---

## Environment Setup

Skip to **Environment Usage** if you already have the environment set up.

### Quickstart (via environment.yml)

```bash
module load conda
conda env create -f environment.yml
```

> **Note**: If you encounter "Network is unreachable" errors during package metadata collection, simply retry.

### Manual Install

Use this for step-by-step setup or troubleshooting individual packages.

#### 1. Create environment

```bash
module load conda

# Recommended: install in home directory (~/.conda/envs/) for faster imports
conda create -n myenv python=3.12 -y

# Alternative: install in scratch (if home quota is tight — but slower imports)
conda create -p ~/scratch/copy-myenv python=3.12 -y
```

Activate:
```bash
conda activate myenv                  # home dir install
conda activate ~/scratch/copy-myenv   # scratch install
```

#### 2. Install conda packages

```bash
conda install -c conda-forge \
    ipykernel ipython ipywidgets \
    numpy pandas scipy matplotlib seaborn scikit-learn \
    catboost gensim networkx python-igraph pymetis tqdm tabulate -y
```

#### 3. Install PyTorch

PyTorch dropped conda distribution after 2.5 — install via pip with the CUDA wheel index.
Reference: [pytorch.org/get-started/previous-versions](https://pytorch.org/get-started/previous-versions/)

```bash
# Linux / Gilbreth (CUDA 12.6)
pip install torch==2.8.0+cu126 --extra-index-url https://download.pytorch.org/whl/cu126

# macOS Apple Silicon (MPS built into the standard PyPI wheel)
pip install torch==2.8.0
```

Verify:
```bash
# Linux
python -c "
import torch
print('Torch version :', torch.__version__)
print('CUDA version  :', torch.version.cuda)
print('CUDA available:', torch.cuda.is_available())
print('Device name   :', torch.cuda.get_device_name() if torch.cuda.is_available() else 'N/A')
"

# macOS
python -c "
import torch
print('Torch version:', torch.__version__)
print('MPS available:', torch.backends.mps.is_available())
"
```

#### 4. Install PyTorch Geometric

PyG is a pure-Python package with no CPU/CUDA variants — the same wheel works everywhere.
Reference: [pytorch-geometric.readthedocs.io/install](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html)

```bash
pip install torch-geometric==2.7.0
```

Verify:
```bash
python -c "import torch_geometric; print('PyG version:', torch_geometric.__version__)"
```

> **Optional extensions** (`pyg_lib`, `torch_scatter`, `torch_sparse`): not needed for this project. PyG 2.x falls back to native PyTorch ops, and the project uses precomputed embeddings at inference time.

#### 5. Install TensorFlow

TF bundles its own CUDA runtime via the `[and-cuda]` extra — no separate CUDA module needed.
Reference: [tensorflow.org/install/pip](https://www.tensorflow.org/install/pip) | [github.com/tensorflow/tensorflow/releases](https://github.com/tensorflow/tensorflow/releases)

```bash
# Linux (CUDA bundled)
# Note: TF 2.21.0 conflicts with torch 2.8.0 on nvidia-nccl-cu12 — see environment.yml for resolved version
pip install "tensorflow[and-cuda]==<see environment.yml>"

# macOS (CPU only — standard TF has no Metal/MPS support)
pip install tensorflow==2.21.0
```

Verify:
```bash
python -c "
import tensorflow as tf
print('TF version :', tf.__version__)
print('GPUs found :', tf.config.list_physical_devices('GPU'))
"
```

#### 6. Other pip packages

```bash
pip install pecanpy
```

---

## Cleanup

**One-shot (recommended after environment creation):**
```bash
conda clean --all -y && pip cache purge
```

**Conda cache** (`~/.conda/pkgs/`):
```bash
conda clean --all --dry-run          # preview what will be removed
conda clean --all -y                 # remove tarballs, unused packages, index cache
conda clean --all --force-pkgs-dirs  # also remove extracted pkg dirs (only frees space if env is deleted)
```

> **Note**: `--force-pkgs-dirs` removes hardlinks from the pkg cache but does **not** free disk space while the environment still exists — the data is kept alive via hardlinks in `~/.conda/envs/`.

**Pip cache** (`~/.cache/pip/`):
```bash
pip cache info      # show cache size and location
pip cache list      # list cached packages
pip cache purge     # wipe entire cache
```

**Reset modules to default:**
```bash
module load rcac
```

---

## Environment Usage

```bash
module load conda
conda activate myenv
```

Register as a Jupyter kernel (one-time):
```bash
python -m ipykernel install --user --name myenv --display-name "Python (myenv)"
# Installs kernel to: /home/username/.local/share/jupyter/kernels/myenv
```

---

## Notes

- **Home dir vs scratch**: conda envs in `~/.conda/envs/` import ~2× faster than scratch — NFS handles many small files better than Lustre (measured: ~7s vs ~13s for `import torch`). Scratch is also not backed up.
- **CUDA module**: No need to `module load cuda/12.6` — torch bundles its own CUDA runtime inside the pip wheel; the system driver just needs to be compatible (it is).
- **PyTorch conda channel**: deprecated after 2.5. Always install torch via pip with `--extra-index-url https://download.pytorch.org/whl/cuXXX` going forward.
- **Network errors**: retry `conda env create` if you hit "Network is unreachable" during metadata collection.
