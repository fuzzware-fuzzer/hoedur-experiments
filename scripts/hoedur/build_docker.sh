#!/bin/sh

DIR="$(dirname "$(readlink -f "$0")")"

docker build --no-cache -t hoedur-fuzzware:latest $DIR -f $DIR/hoedur-fuzzware.dockerfile
