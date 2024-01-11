#!/bin/sh
DIR="$(dirname "$(readlink -f "$0")")"
experiments_rootdir=$DIR/../../

docker_options=""
if [ -t 0 ]; then
    docker_options="-t"
fi

docker run \
    --rm -i \
    --user "$(id -u):$(id -g)" \
    --env "HOME=/home/user" \
    --env "PYTHON_EGG_CACHE=/tmp/.cache" \
    "$docker_options" \
    --mount type=bind,source="$(realpath "$experiments_rootdir")",target=/home/user/fuzzware/targets \
    "fuzzware:fuzzware-hoedur-eval" "$@"
