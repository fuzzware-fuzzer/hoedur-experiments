# Fuzzer Throughput Statistics

This directory contains the overall executions per second numbers of each fuzzer for this experiment.

## Interpreting Firmware Fuzzer Throughput

It is worth mentioning that the executions per second metric is hard to interpret for firmware fuzzers. The reason for this is that firmware reads input continously in a streaming manner. Firmware is also designed to run indefinitely. While longer inputs take longer to run, they may also carry multiple logical inputs (e.g., network packets, over-the-air frames, ...). As such, a more meaningful metric might be `logical inputs per second`. Such metric, however, is target-specific and thus harder to collect.

We provide these `execution per second` numbers for completeness for the interested reader, but overall we note that it requires a lot of context to interpret these numbers correctly.
