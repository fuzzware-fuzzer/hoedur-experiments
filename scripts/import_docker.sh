#!/bin/bash

cd "$(dirname $0)" || exit 1

INSTALL="$PWD/../install"

echo Importing fuzzware docker...
zstd -dk --stdout "$INSTALL/fuzzware.docker.tar.zst" | docker load

echo Importing hoedur docker...
zstd -dk --stdout "$INSTALL/hoedur-fuzzware.docker.tar.zst" | docker load

echo Importing hoedur-plotting-env docker...
zstd -dk --stdout "$INSTALL/hoedur-plotting-env.docker.tar.zst" | docker load