**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct-AWQ · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 56 | 74 ms | 132 ms | 13.6 ms | 15.3 ms | 13.7 ms | 100% | 0.39 |
| 1.0 | 51 | 0 | 113 | 58 ms | 142 ms | 14.5 ms | 16.4 ms | 14.7 ms | 100% | 0.84 |
| 2.0 | 99 | 0 | 220 | 63 ms | 127 ms | 16.2 ms | 22.7 ms | 16.8 ms | 100% | 1.59 |
| 4.0 | 227 | 0 | 481 | 99 ms | 229 ms | 32.4 ms | 51.9 ms | 33.0 ms | 100% | 3.60 |
| 6.0 | 347 | 0 | 669 | 203 ms | 294 ms | 72.4 ms | 98.9 ms | 77.8 ms | 35% | 1.79 |
| 8.0 | 464 | 0 | 778 | 387 ms | 572 ms | 147.6 ms | 198.2 ms | 150.1 ms | 9% | 0.54 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
