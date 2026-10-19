# Summary (GPU at $0.35/h, common level 2 req/s)

| config | weights GiB | KV cache tokens | knee req/s | out tok/s at knee | goodput tok/s at knee | SLO pass at knee | $/M good at knee | TTFT p50 ms @common | ITL p50 ms @common | ITL p99 ms @common | SLO pass @common |
|---|---|---|---|---|---|---|---|---|---|---|---|
| awq-prefix | 1.9 | 287,072 | 4.0 | 480 | 480 | 1.0 | 0.202 | 62.7 | 16.2 | 31.5 | 1.0 |
| fp16-prefix | 5.8 | 187,744 | 2.0 | 211 | 211 | 1.0 | 0.460 | 127 | 41.1 | 66.8 | 1.0 |
| fp16 | 5.8 | 175,008 | 1.0 | 109 | 83.0 | 0.725 | 1.2 | 775 | 74.4 | 742 | 0.030 |
| specdec-k1 | 6.7 | 110,528 | 2.0 | 213 | 212 | 0.990 | 0.460 | 194 | 74.5 | 120 | 0.990 |
