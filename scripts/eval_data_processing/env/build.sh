#!/bin/bash

cd "$(dirname $0)" || exit 1
source config.sh

docker build "$@" -t $IMAGE_NAME .