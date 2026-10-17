# serving-benchmarks

Public, reproducible latency, throughput and cost benchmarks for three LLM serving configurations, with full methodology and raw data.

Project 15 of 15 in [inference-infra-portfolio](https://github.com/NomanJafar/inference-infra-portfolio).

## What this builds

Load curves for Qwen2.5-3B-Instruct on one T4 under four servers, all measured with the same open-loop [tokenbench](https://github.com/NomanJafar/tokenbench) sweep:

| slug | configuration | why it is here |
|---|---|---|
| `fp16` | FP16, prefix caching off | the reference: every request pays its full prefill |
| `fp16-prefix` | FP16, prefix caching on | attribution: how much of the next row is the cache |
| `awq-prefix` | AWQ 4-bit + prefix caching | the "cheap serving" configuration |
| `specdec-k1` | FP16 + 0.5B draft model, k=1 | the "fast decode at low load" configuration |

For each: TTFT and ITL percentiles against offered load, output tokens per second, goodput under a stated SLO (TTFT ≤ 1 s, TPOT ≤ 60 ms), the knee (the load with the most goodput), and $ per million output tokens at an assumed $0.35/h, for all tokens and for the tokens that met the SLO.

[METHODOLOGY.md](METHODOLOGY.md) is the contract: configurations with exact `vllm serve` lines, the workload and why it is open-loop, the metric definitions, the SLO and price and why those values, threats to validity, and how to rerun. The analysis (`serving-benchmarks report`) is pure Python over tokenbench's JSON and is covered by 12 tests on synthetic sweeps, so the tables can be regenerated from the committed raw data by anyone.

## Why it matters

Public, reproducible benchmarks are the strongest hiring signal in infra, and most published ones fail on one of three counts: closed-loop load that hides saturation, no SLO so throughput counts tokens nobody waited for, or no raw data. This one is open-loop, reports goodput against a stated SLO, and commits every JSON it draws from.

## Status

Methodology, configurations, sweep command, report builder and tests are done. The T4 run is queued on Kaggle; the Results section below is filled from `results/kaggle_run1/report/summary.md` when it finishes.

## Results

Pending the Kaggle run (four cold starts and four six-level sweeps, about 50 minutes). The tables and the five plots (`ttft.png`, `itl.png`, `throughput.png`, `goodput.png`, `cost.png`) will appear here, with the quality caveat for the AWQ row carried over from quantlab (perplexity +8.4%, GSM8K −15 points for this checkpoint).

## Layout

| path | what |
|---|---|
| `METHODOLOGY.md` | sections 1–8: question, configurations, workload, metrics, hardware, threats to validity, rerunning, raw data |
| `src/serving_benchmarks/configs.py` | the four `BenchConfig`s, `serve_command()`, the deterministic 560-word `system_prompt()` |
| `src/serving_benchmarks/analysis.py` | `curve_rows()`, `knee()`, `usd_per_m_tokens()`, `summary_rows()`, Markdown tables |
| `src/serving_benchmarks/report.py` | `build_report()`: summary.md, curves.md, summary.json, five plots |
| `src/serving_benchmarks/cli.py` | `serving-benchmarks report\|configs\|sweep-args`; the tokenbench command every configuration is measured with |
| `tests/` | synthetic sweeps that saturate; cost arithmetic, knee, pairing of sweeps with startup info, report files, CLI |
| `notebooks/kaggle_serving_benchmarks.ipynb` | the T4 run |
| `results/` | one directory per run with the raw JSON and the report |

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
serving-benchmarks configs        # the four vllm serve lines
serving-benchmarks sweep-args     # the tokenbench command
# after a run:
serving-benchmarks report --results results/kaggle_run1 --gpu-usd-per-hour 0.35 --common-rps 2
```

## Hardware notes

Developed against free-tier GPUs (Kaggle and Colab T4, 16 GB). Where a T4 limits what can be measured (no FP8, Turing-era kernels, Triton attention only), the README says so rather than papering over it.

## License

MIT
