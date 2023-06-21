#!/bin/sh
cd "$(dirname $0)" || exit 1
../scripts/run_reproducer.py --results ../../01-bug-finding-ability/results/bug-reproducers unchecked_sdu_length $@
