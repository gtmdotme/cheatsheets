Latest Announcement: https://www.rcac.purdue.edu/news/7275

## SSH Access to Server
Always connect to the same front-end node on Purdue's RCAC cluster to ensure consistent access to your `tmux` sessions. For example, you can link `gilbreth-fe00` to a specific node by updating your `~/.ssh/config` file:

```bash
ssh gilbreth-fe00
```

Sample `~/.ssh/config` entry (assuming SSH keys are set up for passwordless authentication):

```bash
Host gilbreth-fe00
    HostName gilbreth-fe00.rcac.purdue.edu
    User <your_username>
    IdentityFile ~/.ssh/id_rsa
```

## Using `tmux` on Server
1. **Initial Setup**
    ```bash
    # Create a new tmux session
    tmux new -s one
    ```

2. **Subsequent Access**
    ```bash
    # Attach to an existing tmux session
    tmux a
    ```

## Creating windows in `tmux`

Create separate `tmux` windows for the following tasks to keep your workflow organized.

> **💡 Tip:**  
> To create a new tmux window, press `<PREFIX> + c` (default prefix is `Ctrl + b`).  
> To rename a window, press `<PREFIX> + ,`.

1. **RESOURCES** (Monitor Slurm resources)
    ```bash
    # Monitor all partitions (top pane)
    watch -d -c showpartitions

    # Monitor your accounts (bottom pane)
    watch -d slist
    ```

2. **JOBS** (Monitor submitted Slurm jobs)
    ```bash
    # Monitor your jobs
    watch squeue --me
    ```

3. **SLURM** (Submit and manage Slurm jobs)
    ```bash
    # Submit a job
    sbatch job.sh

    # View job details
    jobinfo <job_id>

    # Cancel a running job
    scancel <job_id>
    ```

4. **SRC** (Debug code using interactive sessions)
    ```bash
    # Navigate to your code repository
    cd my_repository

    # Load the conda module
    module load conda

    # Activate your conda environment
    source activate myenv

    # Run the above commands beforehand to avoid re-running them in the interactive session

    # Obtain an interactive session on a V100 GPU with 16 cores for 60 minutes
    sinteractive -N 1 -n 16 --gres=gpu:1 --partition=v100 --mem=10G --account=csml --qos standby --time 60
    # NOTE: Remove `--qos standby` to get priority access (i.e., get resources quicker!)
    ```


## Author
Gautam Choudhary
