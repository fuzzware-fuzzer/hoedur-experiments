#!/bin/sh

DIR="$(dirname "$(readlink -f "$0")")"

experiment_dir=$DIR/..
scripts_dir=$experiment_dir/../scripts
bug_discovery_timing_dir=$experiment_dir/results/bug-discovery-timings

$scripts_dir/summarize_bug_discovery_timings.py --bug-combination-base-dir=$bug_discovery_timing_dir
