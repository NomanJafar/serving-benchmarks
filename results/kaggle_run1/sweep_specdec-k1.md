**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 55 | 146 ms | 203 ms | 48.6 ms | 53.1 ms | 49.2 ms | 100% | 0.38 |
| 1.0 | 51 | 0 | 111 | 162 ms | 220 ms | 56.7 ms | 64.1 ms | 57.0 ms | 65% | 0.52 |
| 2.0 | 99 | 0 | 212 | 199 ms | 266 ms | 78.6 ms | 97.2 ms | 79.0 ms | 4% | 0.06 |
| 4.0 | 227 | 0 | 438 | 305 ms | 497 ms | 113.5 ms | 168.3 ms | 120.0 ms | 0% | 0.00 |
| 6.0 | 347 | 0 | 599 | 556 ms | 825 ms | 216.4 ms | 296.2 ms | 227.3 ms | 0% | 0.00 |
| 8.0 | 464 | 0 | 675 | 868 ms | 1540 ms | 361.4 ms | 548.5 ms | 385.1 ms | 0% | 0.00 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
