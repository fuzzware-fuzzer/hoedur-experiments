#!/bin/bash

cd "$(dirname $0)" || exit 1

docker run --rm --user "$(id -u):$(id -g)" --mount src="$PWD/..",target=/home/user/hoedur-experiments,type=bind --mount src="$PWD/../targets",target=/home/user/hoedur-targets,type=bind -it hoedur-fuzzware $@