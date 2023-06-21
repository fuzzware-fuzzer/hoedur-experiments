#!/bin/sh

DIR="$(dirname "$(readlink -f "$0")")"

experiment_dir=$DIR/../..
fuzzware_scripts_dir=$experiment_dir/../scripts/fuzzware
fuzzware_runs_dir=$experiment_dir/results/fuzzing-runs/fuzzware
coverage_results_dir=$experiment_dir/results/coverage

$fuzzware_scripts_dir/coverage/gather_coverage.py --basedir=$fuzzware_runs_dir --outdir=$coverage_results_dir
