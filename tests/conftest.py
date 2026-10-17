"""Synthetic tokenbench sweep results shaped like the real ones, so the analysis is tested without a GPU."""

import json

import pytest


def fake_level(level: float, out_tok_s: float, ttft_p50: float, itl_p50: float, slo_pass: float, errors: int = 0) -> dict:
    requests = int(level * 60)
    good = int(requests * slo_pass)
    return {"mode": "open", "level": level, "warmup_requests": 4, "requests": requests, "errors": errors, "wall_s": 60.0,
            "completion_tokens": int(out_tok_s * 60), "prompt_tokens": requests * 600,
            "requests_per_s": requests / 60.0, "output_tokens_per_s": out_tok_s, "total_tokens_per_s": out_tok_s + requests * 10,
            "ttft": {"n": requests, "p50": ttft_p50, "p95": ttft_p50 * 2, "p99": ttft_p50 * 3, "max": ttft_p50 * 4, "mean": ttft_p50},
            "tpot": {"n": requests, "p50": itl_p50 * 1.1, "p95": itl_p50 * 1.5, "p99": itl_p50 * 2, "max": itl_p50 * 3, "mean": itl_p50},
            "itl": {"n": requests * 100, "p50": itl_p50, "p95": itl_p50 * 1.5, "p99": itl_p50 * 2.5, "max": itl_p50 * 10, "mean": itl_p50},
            "e2e": {"n": requests, "p50": 5.0, "p95": 8.0, "p99": 9.0, "max": 10.0, "mean": 5.5},
            "slo": {"ttft_ms": 1000, "tpot_ms": 60}, "slo_pass_rate": slo_pass,
            "goodput_requests_per_s": good / 60.0, "goodput_tokens_per_s": out_tok_s * slo_pass,
            "metrics_timeline": [], "per_request": []}


def fake_sweep(name: str, scale: float = 1.0) -> dict:
    """A load curve that saturates: throughput flattens, TTFT explodes, SLO pass rate collapses."""
    levels = []
    for level, out, ttft, itl, ok in ((0.5, 70, 0.08, 0.040, 1.0), (1, 140, 0.09, 0.042, 1.0), (2, 270, 0.12, 0.046, 0.98),
                                      (4, 500, 0.30, 0.055, 0.80), (8, 620, 6.0, 0.070, 0.10)):
        levels.append(fake_level(level, out * scale, ttft / scale, itl / scale, ok))
    return {"config": {"base_url": "http://x", "model": "m", "mode": "open", "prompts": "sample", "label": name}, "levels": levels}


@pytest.fixture
def results_dir(tmp_path):
    for slug, scale in (("fp16", 1.0), ("awq-prefix", 1.3), ("specdec-k1", 1.1)):
        (tmp_path / f"sweep_{slug}.json").write_text(json.dumps(fake_sweep(slug, scale)))
        (tmp_path / f"startup_{slug}.json").write_text(json.dumps({"model_load_gib": 5.75 / scale, "kv_cache_tokens": 175008, "startup_s": 90}))
    return tmp_path
