**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 55 | 145 ms | 212 ms | 47.2 ms | 52.5 ms | 29.0 ms | 100% | 0.38 |
| 1.0 | 51 | 0 | 111 | 148 ms | 231 ms | 50.3 ms | 61.8 ms | 32.8 ms | 100% | 0.81 |
| 2.0 | 99 | 0 | 213 | 194 ms | 268 ms | 74.5 ms | 93.1 ms | 43.0 ms | 99% | 1.50 |
| 4.0 | 227 | 0 | 444 | 278 ms | 453 ms | 103.5 ms | 148.9 ms | 65.4 ms | 37% | 1.19 |
| 6.0 | 347 | 0 | 617 | 489 ms | 689 ms | 191.2 ms | 242.8 ms | 116.4 ms | 6% | 0.28 |
| 8.0 | 464 | 0 | 706 | 791 ms | 1339 ms | 328.4 ms | 468.5 ms | 202.0 ms | 2% | 0.11 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
