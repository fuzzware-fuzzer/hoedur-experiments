#!/bin/sh
cd "$(dirname $0)" || exit 1
../scripts/run_reproducer.py --results ../../01-bug-finding-ability/results/bug-reproducers l2cap_mtu_6lo_output_packetbuf_oob_write $@
