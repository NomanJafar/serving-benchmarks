**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 54 | 404 ms | 475 ms | 32.0 ms | 35.3 ms | 35.8 ms | 100% | 0.37 |
| 1.0 | 51 | 0 | 109 | 444 ms | 799 ms | 36.9 ms | 44.4 ms | 51.9 ms | 73% | 0.58 |
| 2.0 | 99 | 0 | 202 | 775 ms | 1538 ms | 74.4 ms | 499.1 ms | 138.5 ms | 3% | 0.04 |
| 4.0 | 227 | 0 | 248 | 12368 ms | 37524 ms | 210.5 ms | 992.0 ms | 488.6 ms | 0% | 0.00 |
| 6.0 | 347 | 71 | 188 | 29347 ms | 95341 ms | 856.0 ms | 999.6 ms | 675.0 ms | 0% | 0.00 |
| 8.0 | 464 | 274 | 118 | 23447 ms | 86346 ms | 894.3 ms | 1009.3 ms | 728.8 ms | 0% | 0.00 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
