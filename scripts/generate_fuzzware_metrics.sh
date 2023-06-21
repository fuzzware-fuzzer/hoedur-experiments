#!/bin/sh

DIR="$(dirname "$(readlink -f "$0")")"

docker_wrapper=$DIR/fuzzware/run_fuzzware_docker.sh

$docker_wrapper -c scripts/fuzzware/generate_all_fuzzware_experiment_metrics.sh
