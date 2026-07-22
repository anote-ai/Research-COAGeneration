# AAAI 2027 Results

`executable/` contains the held-out main evaluation: generated split CSVs,
task-level traces, aggregate summaries, paired bootstrap/sign-test comparisons,
calibration details, and the tradeoff figure. `ablations/` contains the matched
router ablations. `challenge/` contains the locked lexical-shift evaluation,
which is reported separately from the standard test. `sensitivity/` contains
training-size and threshold sweeps.

All outcomes are produced by deterministic local operations and exact answer
checking. Cost is normalized operation usage, not API dollars. Latency is local
CPU wall-clock time and is not representative of live LLM or network latency.
