## ⚡ Quick Reference

| Section | Key commands covered |
|---------|----------------------|
| [🌿 Git](#-git) | clone, status, commit, push, pull, reset, diff |
| [🔐 SSH](#-ssh) | ssh, scp, rsync, ssh-keygen, ssh config |
| [💻 Bash Essentials](#-bash-essentials) | env vars, nav, file ops, grep/find, process, chmod |
| [📊 System Monitoring](#-system-monitoring) | htop, du, df, free, nvidia-smi, ps |

---

### 🌿 Git

```bash
# Clone a repository
git clone https://github.com/user/repo.git

# Check status and recent log
git status

# Stage, commit, and push
git add .
git commit -m "your message"
git push

# Pull latest changes
git pull

# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Discard all local changes
git checkout -- .

# View diff of staged changes
git diff --cached
```

---

### 🔐 SSH

```bash
# Basic SSH login
ssh username@hostname

# SSH with a specific identity file
ssh -i ~/.ssh/id_rsa username@hostname

# SSH with port forwarding (e.g., Jupyter)
ssh -L 8888:localhost:8888 username@hostname

# Copy files to/from remote (scp)
scp local_file.txt username@hostname:/remote/path/
scp username@hostname:/remote/file.txt ./local/

# Sync a directory to remote (rsync)
rsync -avz ./local_dir/ username@hostname:/remote/dir/

# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy public key to remote host (enable passwordless login)
ssh-copy-id username@hostname

# Sample ~/.ssh/config entry for easy access
Host myserver
    HostName myserver.example.com
    User username
    IdentityFile ~/.ssh/id_rsa
```

---

### 💻 Bash Essentials

```bash
# --- Identity / Environment ---
echo $USER                      # current username
echo $SHELL                     # current shell
printenv                        # print all environment variables
export MY_VAR=value             # set env var for current shell session
echo $MY_VAR                    # read variable value

# --- Navigation ---
cd                              # go to home
pwd                             # current directory
ls -ltrh                        # list files sorted by time
tree -L 2                       # directory tree (if installed)

# --- File / Text ---
cat file.txt                    # print file contents
less file.txt                   # scroll file safely
head -n 20 file.txt             # first 20 lines
tail -n 20 file.txt             # last 20 lines
grep -R "TODO" .                # recursive text search
find . -name "*.py"             # find files by pattern
wc -l file.txt                  # count lines
touch notes.md                  # create empty file / update timestamp
mkdir new_folder                # create directory
mkdir -p path/to/dir            # create directory
cp source.txt dest.txt          # copy file
mv old_name.txt new_name.txt    # move/rename file
rm file.txt                     # remove file
rm -rf dir_to_delete            # force remove directory
tar -czvf archive.tar.gz dir/   # create tar.gz archive
tar -xzvf archive.tar.gz        # extract tar.gz archive

# --- Process / System ---
history                         # command history
ps aux | grep python            # find running process
kill -9 <pid>                   # force stop process
date                            # current date and time
uname -a                        # OS/kernel info
which python                    # path of executable
which -a python                 # all paths of executable in $PATH

# --- Permissions ---
chmod +x script.sh              # make script executable

# --- Quality-of-life ---
clear                           # clear terminal
source ~/.bashrc                # reload shell config
```

---

### 📊 System & Resource Monitoring

```bash
# Monitor CPU/memory usage interactively
htop

# Check disk usage of current directory
du -achd1
du -achd1 | sort -h     # sort by size
du -sh                  # summary of total size

# Check available disk space
df -h

# Show available memory
free -h

# Monitor GPU usage (NVIDIA)
nvidia-smi
watch -d nvidia-smi     # refresh every 2 seconds

# List running processes by user
ps aux | grep $USER
```
