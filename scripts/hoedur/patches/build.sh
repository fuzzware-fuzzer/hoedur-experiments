#!/bin/sh
set -ex

# reset previously applied patches
git reset --hard origin/main

# apply patches
variant=""
for dir in "$@"; do
    if [ "$variant" = "" ]
    then
        variant="$dir"
    else
        variant="$variant-$dir"
    fi
    
    git am patches/"$dir"/*.patch
done

# build hoedur variant
mkdir -p /tmp/bin
cargo install --path "$HOEDUR/hoedur" \
    --bin hoedur-arm \
    --root /tmp \
    --no-track
mv /tmp/bin/hoedur-arm "/home/user/.cargo/bin/hoedur-$variant-arm"