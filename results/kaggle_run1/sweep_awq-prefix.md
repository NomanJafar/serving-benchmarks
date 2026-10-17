**tokenbench run** · model: Qwen/Qwen2.5-3B-Instruct-AWQ · mode: open · server: http://127.0.0.1:8000

| level | req | err | out tok/s | TTFT p50 | TTFT p95 | ITL p50 | ITL p95 | TPOT p50 | SLO pass | goodput req/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 24 | 0 | 56 | 78 ms | 135 ms | 14.2 ms | 16.0 ms | 14.4 ms | 100% | 0.39 |
| 1.0 | 51 | 0 | 113 | 62 ms | 154 ms | 15.4 ms | 17.9 ms | 15.7 ms | 100% | 0.84 |
| 2.0 | 99 | 0 | 219 | 69 ms | 135 ms | 17.5 ms | 24.6 ms | 18.4 ms | 100% | 1.58 |
| 4.0 | 227 | 0 | 478 | 115 ms | 229 ms | 36.2 ms | 57.2 ms | 37.0 ms | 100% | 3.56 |
| 6.0 | 347 | 0 | 653 | 242 ms | 341 ms | 84.3 ms | 117.3 ms | 90.6 ms | 28% | 1.41 |
| 8.0 | 464 | 0 | 752 | 434 ms | 656 ms | 165.7 ms | 229.5 ms | 168.0 ms | 8% | 0.42 |

SLO: TTFT ≤ 1000 ms and TPOT ≤ 60 ms. Goodput counts only requests meeting both.
