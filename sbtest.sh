#!/bin/bash
# sbtest — wrapper around sbatch --test-only that shows wait time in human-readable form
# Usage: sbtest --account csml --partition a30 --qos standby -N1 -n4 --mem=16G --gres=gpu:1 --time=04:00:00

OUTPUT=$(sbatch --test-only "$@" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "$OUTPUT"
    exit $EXIT_CODE
fi

echo "$OUTPUT"

# Parse the timestamp (format: 2026-05-20T07:37:59)
START_TS=$(echo "$OUTPUT" | grep -oP '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
if [ -z "$START_TS" ]; then
    exit 0
fi

NOW=$(date +%s)
START=$(date -d "$START_TS" +%s)
DELTA=$(( START - NOW ))

if [ $DELTA -le 0 ]; then
    echo "  => Starts immediately (or already eligible)"
    exit 0
fi

DAYS=$(( DELTA / 86400 ))
HOURS=$(( (DELTA % 86400) / 3600 ))
MINS=$(( (DELTA % 3600) / 60 ))

if [ $DAYS -gt 0 ]; then
    echo "  => Starts in: ${DAYS}d ${HOURS}h ${MINS}m  (at ${START_TS} EDT)"
else
    echo "  => Starts in: ${HOURS}h ${MINS}m  (at ${START_TS} EDT)"
fi
