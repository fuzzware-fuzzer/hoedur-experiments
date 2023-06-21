#!/bin/sh

DIR="$(dirname "$(readlink -f "$0")")"

experiment_dir=$DIR/../..
fuzzware_scripts_dir=$experiment_dir/../scripts/fuzzware
fuzzware_runs_dir=$experiment_dir/results/fuzzing-runs/fuzzware
fuzzware_bug_discovery_timing_dir=$experiment_dir/results/statistics

$fuzzware_scripts_dir/statistics/gather_statistics.py --basedir=$fuzzware_runs_dir --outdir=$fuzzware_bug_discovery_timing_dir
