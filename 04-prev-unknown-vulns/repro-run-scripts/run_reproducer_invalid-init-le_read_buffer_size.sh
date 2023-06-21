#!/bin/sh
cd "$(dirname $0)" || exit 1
../scripts/run_reproducer.py --results ../../01-bug-finding-ability/results/bug-reproducers invalid-init-le_read_buffer_size $@
