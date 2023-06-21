#!/bin/bash

cd "$(dirname $0)" || exit 1
source config.sh

# --privileged needed for chromium :)
docker run --privileged --rm -e "USER_UID=$(id -u)" -e "USER_GID=$(id -g)" -v $PWD/../:/plotting -w /plotting --mount "src=$BASEDIR,target=/home/user/hoedur-experiments,type=bind" $IMAGE_NAME $@