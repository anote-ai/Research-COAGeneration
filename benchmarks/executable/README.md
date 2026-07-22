# Executable Meta-Routing Benchmark

This benchmark evaluates route selection from raw task text. Operations execute
against deterministic task state and final answers are machine checked; success
is never sampled from route labels.

The default suite contains 216 training, 72 development, 108 test, and 108
locked lexical-shift challenge tasks, balanced across data analysis,
frozen-corpus research, and document processing. Prompt templates are held out
by split. Cases include filtered computation, multi-hop retrieval, conflicting
evidence, retrieval outages, incorrect invoice totals, locale-dependent dates,
and cross-field validation.

Generate and evaluate the complete suite with:

```bash
python experiments/meta-routing/aaai2027/run_executable.py
python experiments/meta-routing/aaai2027/run_ablations.py
python experiments/meta-routing/aaai2027/plot_executable.py
```

The task generator is `src/metarouter/executable_tasks.py`; operation semantics
and exact grading are in `src/metarouter/executable_executor.py`. Generated CSV
files include prompts and labels for auditability. The repository is released
under the MIT License.
