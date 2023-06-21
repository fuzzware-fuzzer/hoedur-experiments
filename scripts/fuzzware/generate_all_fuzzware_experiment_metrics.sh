#!/bin/sh
DIR="$(dirname "$(readlink -f "$0")")"

# This script needs to be run in the fuzzware eval docker (via ./run_fuzzware_docker.sh)

# We execute all metric generation scripts in the experiments directory
for scr in 0*/scripts/fuzzware/fuzzware_collect_*; do
    $scr
done