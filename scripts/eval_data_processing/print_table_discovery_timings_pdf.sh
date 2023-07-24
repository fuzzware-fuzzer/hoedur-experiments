#!/bin/bash

cd "$(dirname $0)" || exit 1

env/run.sh pdflatex /home/user/hoedur-experiments/01-bug-finding-ability/results/table_1_cve_discovery_timings.tex
env/run.sh pdflatex /home/user/hoedur-experiments/01-bug-finding-ability/results/table_2_add_bugs_discovery_timings.tex

mv *.pdf ../../01-bug-finding-ability/results/