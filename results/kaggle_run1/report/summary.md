# Summary (GPU at $0.35/h, common level 2 req/s)

| config | weights GiB | KV cache tokens | knee req/s | out tok/s at knee | goodput tok/s at knee | SLO pass at knee | $/M good at knee | TTFT p50 ms @common | ITL p50 ms @common | ITL p99 ms @common | SLO pass @common |
|---|---|---|---|---|---|---|---|---|---|---|---|
| awq-prefix | 1.9 | 287,072 | 4.0 | 478 | 477 | 0.996 | 0.204 | 68.9 | 17.5 | 33.0 | 1.0 |
| fp16-prefix | 5.8 | 187,744 | 2.0 | 208 | 208 | 1.0 | 0.467 | 137 | 43.4 | 73.0 | 1.0 |
| fp16 | 5.8 | 175,008 | 1.0 | 109 | 67.8 | 0.588 | 1.4 | 896 | 88.3 | 899 | 0.010 |
| specdec-k1 | 6.7 | 110,528 | 2.0 | 212 | 204 | 0.949 | 0.477 | 199 | 78.6 | 141 | 0.949 |
