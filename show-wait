#!/bin/bash
# show-wait — test every account/partition/QOS combo and show a wait-time matrix
#
# Usage:
#   show-wait                     # test your own account
#   show-wait <username>          # test another user
#   show-wait [<username>] -v     # also show hidden rows/cols, accessible list, blocked list

VERBOSE=false
TARGET_USER=""
for arg in "$@"; do
    case "$arg" in
        --verbose|-v) VERBOSE=true ;;
        *) TARGET_USER="$arg" ;;
    esac
done
TARGET_USER=${TARGET_USER:-$USER}
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT   # clean up temp files when script exits

# Resource config used for all test jobs (small dummy job — only the wait estimate matters)
# Shorthand flags: -A=--account, -p=--partition, -q=--qos, -N=--nodes, -n=--ntasks, -t=--time
# --mem/--gres/--wrap have no short form.
JOB_ARGS="-N1 -n4 --mem=16G --gres=gpu:1 -t 01:00:00"

# ─── Step 1: Discover which accounts and QOS this user is allowed ────────────
# sacctmgr reads the scheduler's association table.
# -P gives pipe-delimited output; --noheader drops the column title row.
declare -A ACCT_QOS   # maps account name → comma-separated list of allowed QOS
while IFS='|' read -r account qos; do
    # Skip blank entries, numeric IDs (parent association rows), and entries with no QOS
    [[ -z "$account" || -z "$qos" || ! "$account" =~ ^[a-zA-Z] ]] && continue
    ACCT_QOS["$account"]="$qos"
done < <(sacctmgr show associations user="$TARGET_USER" format=account,qos -P --noheader 2>/dev/null)

[[ ${#ACCT_QOS[@]} -eq 0 ]] && { echo "No SLURM associations found for: $TARGET_USER"; exit 1; }

# ─── Step 2: Discover all partitions on this cluster ────────────────────────
# sinfo -h drops the header; %P = partition name; sort -Vu = natural version sort
# so a10 < a30 < a100-40gb instead of alphabetic a10 < a100 < a30.
PARTITIONS=$(sinfo -h -o "%P" 2>/dev/null | sed 's/\*//' | sort -Vu)

# ─── Step 3: Set display order ───────────────────────────────────────────────
qos_order=("normal" "standby" "training")
# Extra grep '^[a-zA-Z]' is a belt-and-suspenders guard against numeric phantom accounts
ACCTS_ORDERED=$(echo "${!ACCT_QOS[@]}" | tr ' ' '\n' | grep '^[a-zA-Z]' | sort)

# ─── Step 4: Build VALID_COMBOS from scontrol × sacctmgr ────────────────────
# Cross-reference the user side (sacctmgr: which accounts/QOS) with the partition
# side (scontrol: AllowAccounts, AllowQos, DenyQos). Only test combos that both
# sides agree are valid — makes BLOCKED table show only genuine surprises.
VALID_COMBOS=()   # each entry: "acct|part|qos"
declare -A PART_INFO_CACHE

for part in $PARTITIONS; do
    PART_INFO_CACHE["$part"]=$(scontrol show partition "$part" 2>/dev/null)
done

for acct in $ACCTS_ORDERED; do
    for part in $PARTITIONS; do
        part_info="${PART_INFO_CACHE[$part]}"
        allow_accounts=$(echo "$part_info" | grep -oP 'AllowAccounts=\K\S+')
        allow_qos=$(echo "$part_info"      | grep -oP 'AllowQos=\K\S+')
        deny_qos=$(echo "$part_info"       | grep -oP 'DenyQos=\K\S+')

        if [[ "$allow_accounts" != "ALL" ]]; then
            echo "$allow_accounts" | tr ',' '\n' | grep -qx "$acct" || continue
        fi

        for q in "${qos_order[@]}"; do
            echo "${ACCT_QOS[$acct]}" | tr ',' '\n' | grep -qx "$q" || continue
            if [[ -n "$allow_qos" && "$allow_qos" != "ALL" ]]; then
                echo "$allow_qos" | tr ',' '\n' | grep -qx "$q" || continue
            fi
            if [[ -n "$deny_qos" && "$deny_qos" != "N/A" ]]; then
                echo "$deny_qos" | tr ',' '\n' | grep -qx "$q" && continue
            fi
            VALID_COMBOS+=("$acct|$part|$q")
        done
    done
done

# ─── Build VALID_SET and COLUMNS from VALID_COMBOS ───────────────────────────
# VALID_SET: O(1) lookup used when drawing matrix cells.
# COLUMNS: only acct:qos pairs that appear in at least one valid combo — prevents
# phantom accounts (like "129") from appearing as matrix columns, and prevents
# QOS sub-columns for QOS that aren't valid on any partition.
declare -A VALID_SET   # "acct|part|qos" → 1
for combo in "${VALID_COMBOS[@]}"; do
    IFS='|' read -r acct part qos <<< "$combo"
    VALID_SET["$acct|$part|$qos"]=1
done

COLUMNS=()
for acct in $ACCTS_ORDERED; do
    for q in "${qos_order[@]}"; do
        for combo in "${VALID_COMBOS[@]}"; do
            IFS='|' read -r ca cp cq <<< "$combo"
            if [[ "$ca" == "$acct" && "$cq" == "$q" ]]; then
                col="$acct:$q"
                [[ " ${COLUMNS[*]} " =~ " $col " ]] || COLUMNS+=("$col")
                break
            fi
        done
    done
done

TOTAL=${#VALID_COMBOS[@]}

echo ""
echo "  User: $TARGET_USER"
echo ""

if $VERBOSE; then
    # Summary table — grouped by acct+part, showing all QOS on one row
    printf "  %-10s %-16s %s\n" "ACCOUNT" "PARTITION" "ACCESSIBLE QOS"
    printf "  %-10s %-16s %s\n" "-------" "---------" "--------------"
    prev_key=""
    for combo in "${VALID_COMBOS[@]}"; do
        IFS='|' read -r acct part qos <<< "$combo"
        key="${acct}|${part}"
        [[ "$key" == "$prev_key" ]] && continue
        qos_list=()
        for c in "${VALID_COMBOS[@]}"; do
            IFS='|' read -r ca cp cq <<< "$c"
            [[ "$ca" == "$acct" && "$cp" == "$part" ]] && qos_list+=("$cq")
        done
        qos_str=$(IFS=', '; echo "${qos_list[*]}")
        printf "  %-10s %-16s %s\n" "$acct" "$part" "$qos_str"
        prev_key="$key"
    done
    echo ""
    echo "  Test command: sbatch --test-only --account <ACCOUNT> --partition <PARTITION> --qos <QOS> -N1 -n4 --mem=16G --gres=gpu:1 --time=01:00:00 --wrap=\"hostname\""
fi
echo ""

# ─── Step 5: Fire only pre-validated combos in parallel ──────────────────────
for combo in "${VALID_COMBOS[@]}"; do
    IFS='|' read -r acct part qos <<< "$combo"
    (
        result=$(sbatch --test-only -A "$acct" -p "$part" -q "$qos" \
            $JOB_ARGS --wrap="hostname" 2>&1)
        echo "$acct|$part|$qos|$result" > "$TMPDIR/${acct}_${part}_${qos}.txt"
    ) &
done

# ─── Progress bar ────────────────────────────────────────────────────────────
while true; do
    DONE=$(ls "$TMPDIR"/*.txt 2>/dev/null | wc -l)
    PCT=$(( DONE * 100 / TOTAL ))
    FILLED=$(( PCT / 4 ))
    EMPTY=$(( 25 - FILLED ))
    BAR=$(printf '%*s' "$FILLED" '' | tr ' ' '#')
    SPC=$(printf '%*s' "$EMPTY" '')
    printf "\r  [%s%s] %d/%d done" "$BAR" "$SPC" "$DONE" "$TOTAL"
    [[ $DONE -eq $TOTAL ]] && break
    sleep 0.5
done
wait
echo ""; echo ""

# ─── Helper: convert ISO timestamp → human-readable "Xh Ym" or "Xd Yh" ─────
starts_in() {
    local ts="$1"
    local now delta
    now=$(date +%s)
    start=$(date -d "$ts" +%s 2>/dev/null) || { echo "?"; return; }
    delta=$(( start - now ))
    [[ $delta -le 0 ]] && { echo "now"; return; }
    local d=$(( delta / 86400 ))
    local h=$(( (delta % 86400) / 3600 ))
    local m=$(( (delta % 3600) / 60 ))
    [[ $d -gt 0 ]] && echo "${d}d ${h}h" || echo "${h}h ${m}m"
}

# ─── Load results into associative arrays ────────────────────────────────────
declare -A RESULTS     # key = "part|acct|qos" → wait string or "BLOCKED"
declare -A START_EPOCH # key = "part|acct|qos" → epoch seconds

for f in "$TMPDIR"/*.txt; do
    IFS='|' read -r acct part qos raw < "$f"
    key="${part}|${acct}|${qos}"
    if echo "$raw" | grep -q "to start at"; then
        ts=$(echo "$raw" | grep -oP 'start at \K\S+')
        START_EPOCH["$key"]=$(date -d "$ts" +%s 2>/dev/null || echo "0")
        RESULTS["$key"]=$(starts_in "$ts")
    else
        START_EPOCH["$key"]=99999999999
        RESULTS["$key"]="BLOCKED"
    fi
done

# ─── Determine which rows/cols to hide ───────────────────────────────────────
# "—" cells (not in VALID_SET) don't count — only tested cells determine block status.
# Rows/cols are hidden when: (a) no valid combos exist at all (policy blocks all),
# or (b) every valid combo was BLOCKED by the scheduler.
declare -A SKIP_ROW
declare -A SKIP_COL
declare -A SKIP_ROW_REASON
declare -A SKIP_COL_REASON

for part in $PARTITIONS; do
    has_valid=false
    all_blocked=true
    for col in "${COLUMNS[@]}"; do
        IFS=':' read -r acct qos <<< "$col"
        [[ -z "${VALID_SET["$acct|$part|$qos"]}" ]] && continue
        has_valid=true
        [[ "${RESULTS["${part}|${acct}|${qos}"]}" != "BLOCKED" ]] && { all_blocked=false; break; }
    done
    if ! $has_valid; then
        SKIP_ROW["$part"]=1
        SKIP_ROW_REASON["$part"]="no access (excluded by policy)"
    elif $all_blocked; then
        SKIP_ROW["$part"]=1
        for col in "${COLUMNS[@]}"; do
            IFS=':' read -r a0 q0 <<< "$col"
            [[ -n "${VALID_SET["$a0|$part|$q0"]}" ]] || continue
            raw=$(cat "$TMPDIR/${a0}_${part}_${q0}.txt" 2>/dev/null)
            SKIP_ROW_REASON["$part"]=$(echo "$raw" | sed 's/.*|\(.*\)/\1/' | sed 's/sbatch: error: //;s/sbatch: //' | head -1 | cut -c1-60)
            break
        done
    fi
done

for col in "${COLUMNS[@]}"; do
    IFS=':' read -r acct qos <<< "$col"
    has_valid=false
    all_blocked=true
    for part in $PARTITIONS; do
        [[ -z "${VALID_SET["$acct|$part|$qos"]}" ]] && continue
        has_valid=true
        [[ "${RESULTS["${part}|${acct}|${qos}"]}" != "BLOCKED" ]] && { all_blocked=false; break; }
    done
    if ! $has_valid; then
        SKIP_COL["$col"]=1
        SKIP_COL_REASON["$col"]="no access (excluded by policy)"
    elif $all_blocked; then
        SKIP_COL["$col"]=1
        for part in $PARTITIONS; do
            [[ -n "${VALID_SET["$acct|$part|$qos"]}" ]] || continue
            raw=$(cat "$TMPDIR/${acct}_${part}_${qos}.txt" 2>/dev/null)
            SKIP_COL_REASON["$col"]=$(echo "$raw" | sed 's/.*|\(.*\)/\1/' | sed 's/sbatch: error: //;s/sbatch: //' | head -1 | cut -c1-60)
            break
        done
    fi
done

# Build visible column list (filtered)
VIS_COLS=()
for col in "${COLUMNS[@]}"; do
    [[ -z "${SKIP_COL[$col]}" ]] && VIS_COLS+=("$col")
done

# ─── Print MATRIX TABLE ───────────────────────────────────────────────────────
PART_W=16    # partition name column width
COL_W=12     # data cell width
SEP=2        # spaces before each cell

echo "=== Estimated Wait Times ==="
echo ""

# Header line 1: account names, each spanning its visible QOS sub-columns
printf "%-${PART_W}s" ""
prev_acct=""
for col in "${VIS_COLS[@]}"; do
    IFS=':' read -r acct qos <<< "$col"
    if [[ "$acct" != "$prev_acct" ]]; then
        n=0
        for c in "${VIS_COLS[@]}"; do [[ "$c" == "$acct:"* ]] && (( n++ )); done
        span=$(( n * (COL_W + SEP) ))
        printf "%${SEP}s%-$((span - SEP))s" "" "$acct"
        prev_acct="$acct"
    fi
done
echo ""

# Header line 2: QOS sub-column names
printf "%-${PART_W}s" "PARTITION"
for col in "${VIS_COLS[@]}"; do
    IFS=':' read -r acct qos <<< "$col"
    printf "%${SEP}s%-${COL_W}s" "" "$qos"
done
echo ""

# Separator line
printf "%-${PART_W}s" "$(printf '%.0s-' $(seq 1 $((PART_W - 1))))"
for col in "${VIS_COLS[@]}"; do
    printf "%${SEP}s%-${COL_W}s" "" "$(printf '%.0s-' $(seq 1 $COL_W))"
done
echo ""

# Sort visible partitions by minimum wait across their valid cells
> "$TMPDIR/part_min.dat"
for part in $PARTITIONS; do
    [[ -n "${SKIP_ROW[$part]}" ]] && continue
    min_epoch=99999999999
    for col in "${VIS_COLS[@]}"; do
        IFS=':' read -r acct qos <<< "$col"
        [[ -z "${VALID_SET["$acct|$part|$qos"]}" ]] && continue   # skip — cells
        epoch="${START_EPOCH["${part}|${acct}|${qos}"]:-99999999999}"
        [[ "$epoch" -lt "$min_epoch" ]] && min_epoch=$epoch
    done
    echo "$min_epoch|$part" >> "$TMPDIR/part_min.dat"
done
SORTED_PARTS=$(sort -t'|' -k1,1n "$TMPDIR/part_min.dat" | cut -d'|' -f2)

# Data rows — sorted by min wait, best cell(s) bold
HAS_TIMES=false; HAS_BLOCKED=false; HAS_DASH=false
for part in $SORTED_PARTS; do
    # Find the best (lowest) epoch for this row, ignoring — cells
    min_epoch=99999999999
    for col in "${VIS_COLS[@]}"; do
        IFS=':' read -r acct qos <<< "$col"
        [[ -z "${VALID_SET["$acct|$part|$qos"]}" ]] && continue
        epoch="${START_EPOCH["${part}|${acct}|${qos}"]:-99999999999}"
        [[ "$epoch" -lt 99999999999 && "$epoch" -lt "$min_epoch" ]] && min_epoch=$epoch
    done

    printf "%-${PART_W}s" "$part"
    for col in "${VIS_COLS[@]}"; do
        IFS=':' read -r acct qos <<< "$col"
        key="${part}|${acct}|${qos}"

        if [[ -z "${VALID_SET["$acct|$part|$qos"]}" ]]; then
            printf "%${SEP}s—%-$((COL_W - 1))s" "" ""
            HAS_DASH=true
        else
            cell="${RESULTS["$key"]:-?}"
            epoch="${START_EPOCH["$key"]:-99999999999}"
            [[ "$cell" == "BLOCKED" ]] && HAS_BLOCKED=true || HAS_TIMES=true
            if [[ "$epoch" == "$min_epoch" && "$min_epoch" -lt 99999999999 ]]; then
                pad=$(( COL_W - ${#cell} ))
                [[ $pad -lt 0 ]] && pad=0
                printf "%${SEP}s\033[1m%s\033[0m%*s" "" "$cell" "$pad" ""
            else
                printf "%${SEP}s%-${COL_W}s" "" "$cell"
            fi
        fi
    done
    echo ""
done

echo ""
$HAS_TIMES   && echo "  Times = estimated wait until job starts (EDT). Backfill-based — may start earlier."
$HAS_BLOCKED && echo "  BLOCKED = scheduler rejected this combo despite policy allowing it."
$HAS_DASH    && echo "  — = no access by policy (not tested)."
echo ""

if $VERBOSE; then
    # ─── Notes on hidden rows/cols ────────────────────────────────────────────
    HIDDEN_ANY=false
    for part in $PARTITIONS; do
        [[ -n "${SKIP_ROW[$part]}" ]] || continue
        if ! $HIDDEN_ANY; then
            echo "  Hidden rows:"
            HIDDEN_ANY=true
        fi
        printf "    %-16s — %s\n" "$part" "${SKIP_ROW_REASON[$part]}"
    done
    for col in "${COLUMNS[@]}"; do
        [[ -n "${SKIP_COL[$col]}" ]] || continue
        if ! $HIDDEN_ANY; then
            echo "  Hidden cols:"
            HIDDEN_ANY=true
        fi
        printf "    %-16s — %s\n" "$col" "${SKIP_COL_REASON[$col]}"
    done
    $HIDDEN_ANY && echo ""

    # ─── ACCESSIBLE (sorted by wait time) ────────────────────────────────────
    echo "=== ACCESSIBLE (sorted by wait time) ==="
    printf "  %-8s  %-14s  %-10s  %-12s  %s\n" "ACCOUNT" "PARTITION" "QOS" "STARTS IN" "EST. START"
    printf "  %-8s  %-14s  %-10s  %-12s  %s\n" "-------" "---------" "---" "---------" "----------"

    > "$TMPDIR/accessible.dat"
    for f in "$TMPDIR"/*.txt; do
        IFS='|' read -r acct part qos raw < "$f"
        echo "$raw" | grep -q "to start at" || continue
        ts=$(echo "$raw" | grep -oP 'start at \K\S+')
        epoch=$(date -d "$ts" +%s 2>/dev/null || echo "0")
        si=$(starts_in "$ts")
        echo "$epoch|$acct|$part|$qos|$si|$ts" >> "$TMPDIR/accessible.dat"
    done

    sort -t'|' -k1,1n "$TMPDIR/accessible.dat" | while IFS='|' read -r epoch acct part qos si ts; do
        printf "  %-8s  %-14s  %-10s  %-12s  %s\n" "$acct" "$part" "$qos" "$si" "$ts"
    done

    # ─── BLOCKED ─────────────────────────────────────────────────────────────
    echo ""
    echo "=== BLOCKED ==="
    printf "  %-8s  %-14s  %-10s  %s\n" "ACCOUNT" "PARTITION" "QOS" "OUTPUT"
    printf "  %-8s  %-14s  %-10s  %s\n" "-------" "---------" "---" "------"

    for f in $(ls "$TMPDIR"/*.txt | sort); do
        IFS='|' read -r acct part qos raw < "$f"
        echo "$raw" | grep -q "to start at" && continue
        output=$(echo "$raw" | sed 's/^sbatch: error: //;s/^sbatch: //')
        printf "  %-8s  %-14s  %-10s  %s\n" "$acct" "$part" "$qos" "$output"
    done

    echo ""
fi
