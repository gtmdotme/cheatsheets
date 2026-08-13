#!/bin/bash
# show-access: list all partitions and QOS accessible to a user
# Usage: show-access [username]   (defaults to $USER)

TARGET_USER=${1:-$USER}

# Step 1: account -> allowed QOS from sacctmgr (user side)
declare -A ACCT_QOS
while IFS='|' read -r account qos; do
    [[ -z "$account" || -z "$qos" || ! "$account" =~ ^[a-zA-Z] ]] && continue
    ACCT_QOS["$account"]="$qos"
done < <(sacctmgr show associations user="$TARGET_USER" format=account,qos -P --noheader 2>/dev/null)

if [[ ${#ACCT_QOS[@]} -eq 0 ]]; then
    echo "No SLURM associations found for user: $TARGET_USER"
    exit 1
fi

# Step 2: partitions (natural/version sort: a10 < a30 < a100-40gb)
PARTITIONS=$(sinfo -h -o "%P" 2>/dev/null | sed 's/\*//' | sort -Vu)

# Step 3: collect rows as "account|partition|qos_str" for sorting by account then partition
ROWS=()
NO_ACCESS=()   # partitions no account can reach
for partition in $PARTITIONS; do
    part_info=$(scontrol show partition "$partition" 2>/dev/null)
    allow_accounts=$(echo "$part_info" | grep -oP 'AllowAccounts=\K\S+')
    allow_qos=$(echo "$part_info"     | grep -oP 'AllowQos=\K\S+')
    deny_qos=$(echo "$part_info"      | grep -oP 'DenyQos=\K\S+')

    any_access=false
    for acct in $(echo "${!ACCT_QOS[@]}" | tr ' ' '\n' | sort); do
        # Check account-level access
        if [[ "$allow_accounts" != "ALL" ]]; then
            echo "$allow_accounts" | tr ',' '\n' | grep -qx "$acct" || continue
        fi

        # Intersect user's QOS with partition's QOS rules
        valid_qos=()
        while IFS= read -r q; do
            [[ -z "$q" ]] && continue
            if [[ -n "$allow_qos" && "$allow_qos" != "ALL" ]]; then
                echo "$allow_qos" | tr ',' '\n' | grep -qx "$q" || continue
            fi
            if [[ -n "$deny_qos" && "$deny_qos" != "N/A" ]]; then
                echo "$deny_qos" | tr ',' '\n' | grep -qx "$q" && continue
            fi
            valid_qos+=("$q")
        done <<< "$(echo "${ACCT_QOS[$acct]}" | tr ',' '\n')"

        if [[ ${#valid_qos[@]} -gt 0 ]]; then
            qos_str=$(IFS=', '; echo "${valid_qos[*]}")
            ROWS+=("$acct|$partition|$qos_str")
            any_access=true
        fi
    done

    $any_access || NO_ACCESS+=("$partition")
done

# Step 4: sort by account (field 1), then by partition with version sort (field 2)
IFS=$'\n' SORTED=($(printf '%s\n' "${ROWS[@]}" | sort -t'|' -k1,1 -k2,2V))
unset IFS

printf "\n%-10s %-16s %-30s\n" "ACCOUNT" "PARTITION" "ACCESSIBLE QOS"
printf "%-10s %-16s %-30s\n" "$(printf '%0.s-' {1..9})" "$(printf '%0.s-' {1..15})" "$(printf '%0.s-' {1..29})"

prev_acct=""
for row in "${SORTED[@]}"; do
    IFS='|' read -r acct partition qos_str <<< "$row"
    if [[ "$acct" == "$prev_acct" ]]; then
        printf "%-10s %-16s %-30s\n" "" "$partition" "$qos_str"
    else
        printf "%-10s %-16s %-30s\n" "$acct" "$partition" "$qos_str"
        prev_acct="$acct"
    fi
done

# Partitions no account has access to, shown at the bottom
for partition in "${NO_ACCESS[@]}"; do
    printf "%-10s %-16s %-30s\n" "(none)" "$partition" "no access"
done
echo ""
