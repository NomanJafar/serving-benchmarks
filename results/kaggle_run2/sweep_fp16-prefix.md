**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 55 | 120 ms | 147 ms | 32.7 ms | 36.3 ms | 33.2 ms | 100% | 0.38 |
| 1.0 | 51 | 0 | 110 | 115 ms | 188 ms | 34.6 ms | 37.9 ms | 35.2 ms | 100% | 0.80 |
| 2.0 | 99 | 0 | 211 | 127 ms | 179 ms | 41.1 ms | 52.4 ms | 42.2 ms | 100% | 1.50 |
| 4.0 | 227 | 0 | 446 | 204 ms | 330 ms | 72.1 ms | 98.9 ms | 73.8 ms | 15% | 0.48 |
| 6.0 | 347 | 0 | 623 | 306 ms | 404 ms | 117.3 ms | 138.4 ms | 117.1 ms | 3% | 0.15 |
| 8.0 | 464 | 0 | 742 | 473 ms | 679 ms | 180.1 ms | 231.4 ms | 179.9 ms | 1% | 0.07 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
