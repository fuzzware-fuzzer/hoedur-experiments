#!/bin/bash

cd "$(dirname $0)" || exit 1

INSTALL="$PWD/../install"

mkdir -p "$INSTALL"

echo Exporting fuzzware docker...
docker save fuzzware:fuzzware-hoedur-eval | zstd > "$INSTALL/fuzzware.docker.tar.zst"

echo Exporting hoedur docker...
docker save hoedur-fuzzware:latest | zstd > "$INSTALL/hoedur-fuzzware.docker.tar.zst"

echo Exporting hoedur-plotting-env docker...
docker save hoedur-plotting-env:latest | zstd > "$INSTALL/hoedur-plotting-env.docker.tar.zst"