# SLURM on Purdue Gilbreth — Quick Reference

Gilbreth is a **community cluster**: research groups purchased GPU nodes that are pooled under SLURM. You own your slice but can opportunistically use idle capacity from others.

## The Three Axes of a Job

Every job needs three aligned parameters:

```
PARTITION  →  which physical machines (hardware type)
ACCOUNT    →  which group's allocation is charged
QOS        →  priority level + time limit
```

A job is accepted only when all three are compatible.

---

## Partitions — Hardware Groups

A **partition** is a named group of nodes by GPU type. A node belongs to one partition.

| Partition | GPU | VRAM | Notes |
|-----------|-----|------|-------|
| `a30` | A30 | 24 GB | owned by `csml` |
| `a10` | A10 | 24 GB | owned by `csit` |
| `a100-40gb` | A100 | 40 GB | multi-group |
| `a100-80gb` | A100 | 80 GB | multi-group |
| `training` | A100 80GB | 80 GB | `csit` only |
| `h100` | H100 | 80 GB | currently down |
| `araghu` | H100 | 80 GB | private, no access |

```bash
showpartitions     # Purdue-specific partition summary
sinfo              # show all partitions
sinfo -p a30       # show nodes in a partition
```

---

## Accounts — Billing Units

An **account** is a resource allocation bucket shared by a group. One person can belong to multiple accounts.

| Account | Owns | QOS available |
|---------|------|---------------|
| `csml` | A30 nodes | `normal`, `standby` |
| `csit` | A10 + training nodes | `normal`, `standby`, `training` |

```bash
slist                                    # your eligible accounts + QOS
sacctmgr show associations user=$USER   # all account/partition/QOS combos
```

There is no hard 1:1 mapping between accounts and partitions. `csml` (which owns A30s) can submit to `a100-40gb` opportunistically via `standby` QOS — the constraint is what each account is authorized to use, configured by admins.

---

## QOS — Priority + Time Limit

| QOS | Priority | Max time | Cost | Notes |
|-----|----------|----------|------|-------|
| `normal` | High | 2 weeks | Charged | Production runs; high-priority, guaranteed on your group's nodes |
| `standby` | Low | 4 hours | **Free** | Borrows idle nodes cluster-wide; preemptible if owner reclaims |
| `training` | Low | 24 hours | Varies | `csit` only; long multi-GPU training |

**Use `standby` whenever your job fits in 4h** — it's free and can use any idle node, including partitions your group doesn't own (e.g. `csml` running on A100s). Best during off-peak hours (nights, weekends).

---

## Valid Combinations (verified)

| Account | Partition | QOS | |
|---------|-----------|-----|-|
| `csml` | `a30` | `normal` / `standby` | ✅ |
| `csml` | `a10` | `normal` / `standby` | ✅ |
| `csml` | `a100-40gb` | `normal` / `standby` | ✅ |
| `csml` | `a100-80gb` | `normal` / `standby` | ✅ |
| `csit` | `a10` | `normal` / `standby` | ✅ |
| `csit` | `a100-40gb` | `normal` / `standby` | ✅ |
| `csit` | `training` | `training` | ✅ |
| `csml` | `training` | `training` | ❌ no access |
| any | `araghu` / `h100` | any | ❌ |

**Standby example** — `csml` borrowing A100s for free:
```bash
#SBATCH --account csml
#SBATCH --partition a100-40gb
#SBATCH --qos standby
#SBATCH --time 04:00:00    # must fit within 4h cap
```

---

## Standby vs Normal — When to Use Which

| Situation | Use |
|-----------|-----|
| Job ≤ 4h, idle nodes available (nights/weekends) | `standby` — free, often starts immediately |
| Long queue, all nodes busy | `normal` — higher priority over standby |
| Job > 4h | `normal` only (standby capped at 4h) |

When unsure, run `sbtest` on both and compare estimated start times.

---

## Custom Tools

All scripts live in `~/.local/bin/` (on `$PATH`).

### `sbtest`

Wraps `sbatch --test-only`; same syntax as `sbatch`, prints estimated start time without submitting:

```bash
sbtest --account=csml --partition=a100-40gb --qos=normal \
  -N1 -n4 --mem=16G --gres=gpu:1 --time=04:00:00 --wrap="hostname"
# => Starts in: 1h 52m  (at 2026-05-20T21:43:16 EDT)
```

Timestamps are EDT (UTC-4). Estimates are backfill-based — jobs often start earlier. `standby` QOS capped at 4h — `sbtest` will error if `--time` exceeds that.

### `show-access`

Cross-references `sacctmgr` + `scontrol` to list every partition/QOS combo accessible to a user.

### `show-wait`

Tests every valid account/partition/QOS combo in parallel and prints a **wait-time matrix** (partitions × account:qos, best cell bolded) plus a **sorted accessible list**.

```bash
show-wait              # your own account
show-wait <username>   # another user
show-wait [-v]         # add -v / --verbose for hidden rows/cols, accessible list, and blocked list
```

Cell values: estimated wait (EDT, backfill-based) · **bold** = fastest option in that row · `BLOCKED` = scheduler rejected despite policy · `—` = no access by policy.

