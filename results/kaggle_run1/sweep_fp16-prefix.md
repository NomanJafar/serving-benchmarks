**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 53 | 128 ms | 188 ms | 33.9 ms | 50.9 ms | 34.8 ms | 100% | 0.36 |
| 1.0 | 51 | 0 | 109 | 119 ms | 206 ms | 36.0 ms | 40.1 ms | 37.1 ms | 100% | 0.79 |
| 2.0 | 99 | 0 | 208 | 137 ms | 213 ms | 43.4 ms | 57.0 ms | 44.4 ms | 100% | 1.48 |
| 4.0 | 227 | 0 | 440 | 220 ms | 359 ms | 77.5 ms | 107.9 ms | 81.0 ms | 10% | 0.33 |
| 6.0 | 347 | 0 | 611 | 333 ms | 457 ms | 127.7 ms | 156.7 ms | 130.8 ms | 2% | 0.09 |
| 8.0 | 464 | 0 | 717 | 529 ms | 766 ms | 198.0 ms | 261.2 ms | 202.7 ms | 1% | 0.03 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
