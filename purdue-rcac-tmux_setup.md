Latest Announcement: https://www.rcac.purdue.edu/news/7275

Documentation: https://www.rcac.purdue.edu/knowledge/gilbreth/run/slurm?all=true

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

    # Monitor accounts/partitions you have access to (bottom pane)
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

4. **GIT** (Optional, for Git commands)
    ```bash
    # Navigate to your code repository
    cd my_repository
    ```

5. **SRC** (Debug code using interactive sessions)
    ```bash
    # Navigate to your code repository
    cd my_repository

    # Load the conda module
    module load conda

    # Activate your conda environment
    source activate myenv

    ################
    # Run the above commands beforehand to avoid re-running them in the interactive session
    ################

    # Obtain an interactive session on a A30 GPU with 8 cores for 5 minutes
    sinteractive -N 1 -n 8 --gres=gpu:1 --partition=a30 --mem=10G --account=csml --qos standby --time 5
    # NOTE: `--qos standby` gives you low priority access to idle resources (max walltime 4 hours).
    # NOTE: Remove `--qos standby` to get priority access (i.e., get resources quicker!)
    ```

> **💡 Notes for Gilbreth:**  
> * Once Slurm has allocated resources to your standby job, you'll have access until the job completes or the walltime is reached, i.e., Gilbreth at this point, does not preempt your standby jobs.  
> * Standby jobs run identically to normal QOS jobs once the resources have been allocated. The only thing that's different is the scheduling priority and maximum runtime allowed.  
> * Standby jobs on Gilbreth are not charged (i.e., resources requested with the "standby" QOS are not pulled from your group's dedicated resources).  

## Author
Gautam Choudhary
