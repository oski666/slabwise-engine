#!/bin/bash
# Protocol runs: 5 seeds at base contamination (mode A), mode B on the same seeds,
# robustness on 3 seeds at 0/10/35/50 % contamination. Two jobs at a time.
cd "$(dirname "$0")/.."
export PYTHONPATH=.
jobs_list=()
for s in 1 2 3 4 5; do jobs_list+=("$s 0.15 A"); done
for s in 1 2 3; do for c in 0.0 0.10 0.35 0.50; do jobs_list+=("$s $c A"); done; done
for s in 1 2 3; do jobs_list+=("$s 0.15 B"); done
for s in 1 2 3; do jobs_list+=("$s 0.15 A - alt"); done
printf '%s\n' "${jobs_list[@]}" | xargs -P 2 -L 1 sh -c 'python3 scripts/run_seed.py $0 $1 $2 $3 $4 > results/log_$0_$1_$2_$4.txt 2>&1; echo done $0 $1 $2 $4'
