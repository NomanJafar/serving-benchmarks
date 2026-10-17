# Methodology

Everything needed to rerun these numbers and to know what they do and do not mean. Written before the GPU run; the Results section of the README refers back to the section numbers here.

## 1. The question

For one model on one GPU, how do three common serving configurations compare on the curves an operator actually sizes against: latency against offered load, throughput against offered load, the load at which the service stops meeting its SLO, and the cost of a million tokens at that point?

- **(a) FP16 baseline.** The model as released, prefix caching off, so every request pays its full prefill. The reference point.
- **(b) AWQ + prefix caching.** 4-bit AWQ weights (the official Qwen checkpoint) with vLLM's automatic prefix caching on. The "cheap serving" configuration: smaller weights for faster memory-bound decode and more KV cache, plus cached prefill of the shared system prompt.
- **(c) Speculative decoding.** FP16 target with a 0.5B draft model proposing one token per step (k=1). The "faster decode at low load" configuration.

A fourth server, **FP16 + prefix caching**, is run so that (b)'s gain can be split into the part prefix caching contributes and the part quantisation contributes. Without it the two would be confounded.

## 2. Configurations

Same model family throughout: Qwen2.5-3B-Instruct, chosen because the portfolio has already measured its quantised checkpoints ([quantlab](https://github.com/NomanJafar/quantlab)) and its draft-model pairing ([specdec](https://github.com/NomanJafar/specdec)) on this GPU, so the configurations here are known-good rather than guessed. `serving-benchmarks configs` prints the exact lines; they are:

| slug | server |
|---|---|
| `fp16` | `vllm serve Qwen/Qwen2.5-3B-Instruct --dtype float16 --max-model-len 4096 --gpu-memory-utilization 0.9 --no-enable-prefix-caching` |
| `fp16-prefix` | same without `--no-enable-prefix-caching` (vLLM 0.31 defaults prefix caching on) |
| `awq-prefix` | `vllm serve Qwen/Qwen2.5-3B-Instruct-AWQ --dtype float16 --max-model-len 4096 --gpu-memory-utilization 0.9` (vLLM reads the quantisation method from the checkpoint and selects the kernel; quantlab saw `MarlinLinearKernel` on the T4) |
| `specdec-k1` | `vllm serve Qwen/Qwen2.5-3B-Instruct ... --speculative-config '{"method":"draft_model","model":"Qwen/Qwen2.5-0.5B-Instruct","num_speculative_tokens":1}'` |

Everything else is vLLM 0.31.0's default: V1 engine, chunked prefill on, `max-num-seqs` 256, CUDA graphs on, `TRITON_ATTN` backend (the only one available on Turing). Each server is started cold, its startup log is kept, and the weights size and KV-cache capacity it reports are recorded next to the sweep.

Why k=1 and not more: specdec measured k = 1, 3, 5 and n-gram on this pair and GPU; k=1 was the only setting that was faster than the baseline at more than one user. Why AWQ and not GPTQ-Int4 or Int8: AWQ is what the project scope named; quantlab's finding that this AWQ checkpoint costs 15 GSM8K points where GPTQ-Int8 costs none is part of the result and is repeated in the README, because a cost curve for a configuration that answers worse is not a free win.

## 3. Workload

One tokenbench command per configuration (`serving-benchmarks sweep-args` prints it):

```
tokenbench sweep --base-url http://127.0.0.1:8000 --model <model> --mode open --levels 0.5,1,2,4,6,8 --duration 60 --warmup 4 \
  --prompts sample --max-tokens 192 --no-ignore-eos --system-prompt "<560-word support policy>" \
  --slo-ttft-ms 1000 --slo-tpot-ms 60 --request-timeout 120 --out results/sweep_<slug>.json
```

- **Open loop.** Requests arrive at the offered rate whether or not earlier ones have finished, so a slow server accumulates a queue instead of slowing the load generator down. This is the only loop that can show the knee; a closed loop hides saturation as lower throughput (tokenbench's primer, coordinated omission).
- **Six levels, 60 s each**, 0.5 to 8 requests per second. At 8 req/s with about 150 output tokens per request the demand (~1,200 tokens/s) exceeds what quantlab measured this model doing at 64 users (960 tokens/s), so the top of the curve is past the knee by design.
- **Four warm-up requests per level, discarded.** The first level additionally absorbs Triton's JIT of attention shapes; its TTFT p99 should be read with that in mind.
- **Prompts: tokenbench's bundled `sample` set** (300 rows with a ShareGPT-like length distribution, generated synthetically and cycled in a seeded order), with the model allowed to stop naturally, capped at 192 output tokens. Natural stopping matters for the speculative configuration: its acceptance rate depends on the text being real continuation, and fixed-length `ignore_eos` output would distort it. It means output lengths vary; throughput is reported in tokens per second, not requests, for that reason.
- **A shared 560-word system prompt** on every request (a fictional support policy, deterministic, in `configs.system_prompt()`). It gives prefix caching something to cache: roughly 700 tokens of identical prefix per request, followed by a distinct user turn. Without it, (b)'s caching would have nothing to do; with it, the FP16-with-caching row shows exactly how much it is worth.
- **Request timeout 120 s.** A request that has not finished by then is counted as an error at that level; errors are reported, never dropped.

## 4. Metrics

Per level, from tokenbench's aggregate:

| metric | definition |
|---|---|
| TTFT | time from sending the request to the first content token; p50, p95, p99 |
| ITL | gap between consecutive streamed tokens, pooled over all tokens of all requests; p50, p99 |
| TPOT | per-request (end − first token) / (tokens − 1); the per-request decode speed used by the SLO |
| output tokens/s | completion tokens produced at that level divided by the level's wall time |
| SLO pass rate | fraction of requests with TTFT ≤ 1,000 ms **and** TPOT ≤ 60 ms |
| goodput | output tokens/s counting only requests that met the SLO |
| knee | the level with the highest goodput; beyond it, extra load produces tokens that arrive too late to count |
| $/M output tokens | `gpu_usd_per_hour / 3600 / tokens_per_s × 1e6`, for all tokens and for SLO-meeting tokens |

The SLO is a choice, stated so it can be disagreed with: 1 s to the first token is the point at which a chat interface starts to feel stuck; 60 ms per token is ~17 tokens/s, faster than people read, and a little above this model's single-stream decode on this GPU (40 ms), so it leaves room for batching but not for a stall. Goodput is reported at this SLO only; `summary.json` has every level's full percentiles so a different SLO can be applied after the fact.

**Addendum after run 1 (18 Oct).** tokenbench's TPOT at the time of the run divided the decode time by the number of *stream chunks*, and a speculative-decoding server emits about 1.7 tokens per chunk, so the speculative configuration's recorded TPOT and SLO pass rate were wrong by that factor (recorded pass rate at 2 req/s: 4 %; per token: 95 %). The report now recomputes TPOT, SLO pass rate and goodput per token from each request's `ttft_s`, `e2e_s` and the server's `completion_tokens`, which the raw JSON carries; `slo_pass_rate_chunks` in `summary.json` keeps the recorded figure. tokenbench itself was fixed the same day. ITL percentiles remain inter-*chunk* gaps for every configuration.

The GPU price is **$0.35 per hour**, an on-demand T4 price at the time of writing; Kaggle's T4 is free. Every dollar figure scales linearly with it.

## 5. Hardware and software

Kaggle, one Tesla T4 (16 GB, Turing, no bfloat16, no FP8, 320 GB/s), vLLM 0.31.0 (cu129 wheel on the Kaggle image's PyTorch cu129 index), Python 3.11. The load generator runs on the same machine's CPU; tokenbench's cross-check (its project 2 results) found the client-side overhead at these rates to be under 2 ms per request. Each configuration is a cold server start inside one notebook session; the four sweeps run back to back.

## 6. Threats to validity

- **One run per configuration, one seed.** No error bars. Differences under ~10% between configurations should be treated as noise until repeated; the README says which conclusions rest on larger gaps.
- **Synthetic prompts.** The sample set has realistic length shape but not realistic content. Speculative acceptance (0.69 at k=1 in specdec on these prompts) could differ on real text in either direction; prefix caching is content-independent.
- **Quality is not measured here.** The AWQ row is faster and cheaper per token; whether the answers are as good is quantlab's measurement (perplexity +8.4%, GSM8K −15 points for this checkpoint), restated in the README, not re-measured.
- **One GPU type, one model size.** The T4's slow prefill and lack of fast INT4 paths shape every curve; on an A100/H100 the ordering can change (specdec's and quantlab's primers explain why).
- **Open-loop saturation is pessimistic about the last level.** A level that starts with a backlog from the previous level reports worse TTFT than a fresh server at the same rate; the knee is therefore conservative.
- **The attribution row isolates prefix caching only under this prompt structure** (long shared prefix, short distinct suffix). A workload without shared prefixes gets nothing from it.

## 7. Rerunning

Full run: open `notebooks/kaggle_serving_benchmarks.ipynb` on Kaggle with a T4 (about 50 minutes: 10 of installs and downloads, then four cold starts and four six-level sweeps). It writes `results/sweep_<slug>.json`, `startup_<slug>.json`, the startup logs, and builds the report.

Partial or local rerun: start one server from section 2, run the section 3 command, then

```
serving-benchmarks report --results results --gpu-usd-per-hour 0.35 --common-rps 2
```

which writes `report/summary.md`, `report/curves.md`, `report/summary.json` and five PNGs. The analysis is pure Python over tokenbench's JSON; 12 tests cover it with synthetic sweeps.

## 8. Raw data

`results/kaggle_runN/` holds, per run: `sweep_<slug>.json` (every level's percentiles, SLO fields, metrics timeline and per-request records), `sweep_<slug>.csv/.md` (tokenbench's own summaries), `startup_<slug>.json` and `startup_<slug>.log`, and `report/`. Nothing is edited after the run; the README's tables are copied from `report/summary.md`.
