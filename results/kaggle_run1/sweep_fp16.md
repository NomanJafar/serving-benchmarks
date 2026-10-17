**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 54 | 418 ms | 464 ms | 32.6 ms | 36.9 ms | 36.5 ms | 100% | 0.37 |
| 1.0 | 51 | 0 | 109 | 472 ms | 820 ms | 39.2 ms | 47.0 ms | 56.6 ms | 59% | 0.47 |
| 2.0 | 99 | 0 | 196 | 896 ms | 2061 ms | 88.3 ms | 568.3 ms | 164.9 ms | 1% | 0.01 |
| 4.0 | 227 | 0 | 230 | 16284 ms | 45615 ms | 227.1 ms | 1059.2 ms | 530.3 ms | 0% | 0.00 |
| 6.0 | 347 | 179 | 101 | 21010 ms | 73849 ms | 976.6 ms | 1081.8 ms | 779.6 ms | 0% | 0.00 |
| 8.0 | 464 | 305 | 93 | 24914 ms | 83115 ms | 975.3 ms | 1085.9 ms | 786.8 ms | 0% | 0.00 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
