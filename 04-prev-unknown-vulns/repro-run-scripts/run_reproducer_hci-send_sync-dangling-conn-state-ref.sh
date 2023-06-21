#!/bin/sh
cd "$(dirname $0)" || exit 1
../scripts/run_reproducer.py --results ../../01-bug-finding-ability/results/bug-reproducers hci-send_sync-dangling-conn-state-ref $@
