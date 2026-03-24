# Cheatsheets

> "The faintest ink 🖋 is better than the strongest memory 🧠." ― Chinese Proverb

Personal cheatsheets, guides, and notes — things I don't want to forget.

Free to use or adapt under the [MIT License](./LICENSE).


---

## 📚 Guides

| Guide | Description |
|---|---|
| [Initial Setup](./initial_setup.md) | PyTorch & PyTorch Geometric setup on Purdue Gilbreth HPC |
| [Purdue RCAC + tmux](./purdue-rcac-tmux_setup.md) | SSH, tmux, and Slurm workflow on RCAC clusters |
| [Tailscale Exit Node](./tailscale_setup.md) | Free private VPN via Oracle Cloud + Tailscale |
| [Bash 101](./bash_101.md) | Basic Bash commands |

## ⚡ Quick Reference

| Section | Commands covered |
|---|---|
| [🖥️ Slurm (Purdue RCAC)](#️-slurm-purdue-rcac) | sbatch, squeue, scancel, sinteractive, seff, sacct |
| [🪟 tmux](#-tmux) | new/attach/list/kill session, pane/window shortcuts |
| [🐍 Conda](#-conda) | env create/activate/export/remove, install, clean |

---

### 🖥️ Slurm (Purdue RCAC)

```bash
# Load RCAC modules
module load rcac        # Load default RCAC environment
module list             # List loaded modules
module load conda       # Load conda module

# Submit a batch job
sbatch job.sh

# List your running/pending jobs
squeue --me

# Watch job queue live (updates every 2s)
watch -d squeue --me

# Cancel a job
scancel <job_id>

# Cancel all your jobs
scancel -u $USER

# View detailed job info
jobinfo <job_id>

# Show all partitions
showpartitions

# List your Slurm accounts (partitions you can use)
slist

# Request an interactive GPU session for 5 minutes (RCAC)
## Default Quality of Service (QoS) is "normal" which gives you higher priority and longer max walltime (2 weeks)
sinteractive -N 1 -n 4 --gres=gpu:1 --partition=a30 --mem=10G --account=<account> --time 5
## For low priority access to idle resources, use `--qos standby` (max walltime 4 hours)
sinteractive -N 1 -n 4 --gres=gpu:1 --partition=a30 --mem=10G --account=<account> --qos standby --time 5

# Show job efficiency after completion
seff <job_id>

# Show last jobs
sacct
# or
sacct -u $USER
```

---

### 🪟 tmux

```bash
# Start a new named session
tmux new -s mysession

# Attach to an existing session
tmux a
tmux a -t mysession

# List all sessions
tmux ls

# Kill a session
tmux kill-session -t mysession
```

| Shortcut | Action |
|---|---|
| `Ctrl+b c` | New window |
| `Ctrl+b ,` | Rename window |
| `Ctrl+b r` | Reload config |
| `Ctrl+b n` | Next window |
| `Ctrl+b p` | Previous window |
| `Ctrl+b l` | Last window |
| `Ctrl+b |` | Split pane vertically |
| `Ctrl+b _` | Split pane horizontally |
| `Ctrl+b arrow` | Move between panes |
| `Shift arrow` | Move between windows |
| `Ctrl+b [` | Enter scroll/copy mode (`q` to exit, `Option + up/down` to navigate faster) |

NOTE: These keybindings are based of my personal `~/.tmux.conf` and may differ from the default tmux keybindings. You can customize them as needed.

---

<a id="conda"></a>

### 🐍 Conda

```bash
# List all environments
conda info --envs

# Create a new environment with Python 3.10
conda create -n myenv python=3.10 -y

# Activate / deactivate
conda activate myenv
conda deactivate

# List installed packages in active env
conda list

# Install packages
conda install numpy pandas matplotlib -y
pip install torch_geometric

# Export environment to a file (exclude build info and prefix)
conda env export --from-history --no-builds | grep -v "^prefix: " > environment.yml

# Recreate environment from file
conda env create -f environment.yml

# Remove an environment
conda remove -n myenv --all

# Clean cache to free disk space
conda clean --all
pip cache purge

# Check Python
python --version
```
