import json

from serving_benchmarks.analysis import curve_rows, knee, load_results, summary_rows, usd_per_m_tokens
from tests.conftest import fake_sweep


def test_usd_per_million_tokens_is_price_over_throughput():
    # $0.35/h at 1,000 tok/s: 3.6 M tokens per hour -> $0.0972 per M
    assert abs(usd_per_m_tokens(0.35, 1000) - 0.0972) < 1e-3
    assert usd_per_m_tokens(0.35, 0) is None


def test_curve_rows_carry_latency_in_ms_goodput_and_cost():
    rows = curve_rows(fake_sweep("fp16"), gpu_usd_per_hour=0.35)
    assert [r["offered_rps"] for r in rows] == [0.5, 1, 2, 4, 8]
    r = rows[1]
    assert r["ttft_p50_ms"] == 90 and r["itl_p50_ms"] == 42 and r["itl_p99_ms"] == 105
    assert r["out_tok_s"] == 140 and r["slo_pass_rate"] == 1.0 and r["goodput_tok_s"] == 140
    assert abs(r["usd_per_m_out"] - 0.35 / 3600 / 140 * 1e6) < 1e-6
    assert abs(r["usd_per_m_good"] - r["usd_per_m_out"]) < 1e-9          # everything met the SLO at this level
    assert abs(rows[-1]["usd_per_m_good"] - 10 * rows[-1]["usd_per_m_out"]) < 1e-9   # 10% pass rate: good tokens cost 10x


def test_knee_is_the_level_with_the_most_goodput():
    rows = curve_rows(fake_sweep("fp16"), 0.35)
    k = knee(rows)
    assert k["offered_rps"] == 4 and k["goodput_tok_s"] == 400


def test_load_results_pairs_sweeps_with_startup_info(results_dir):
    res = load_results(results_dir)
    assert sorted(res) == ["awq-prefix", "fp16", "specdec-k1"]
    assert res["fp16"]["startup"]["kv_cache_tokens"] == 175008 and res["fp16"]["sweep"]["levels"]


def test_summary_rows_compare_configs_at_their_knee_and_at_a_common_level(results_dir):
    res = load_results(results_dir)
    rows = summary_rows(res, gpu_usd_per_hour=0.35, common_rps=2)
    by = {r["config"]: r for r in rows}
    assert by["awq-prefix"]["knee_goodput_tok_s"] > by["fp16"]["knee_goodput_tok_s"]
    assert by["awq-prefix"]["usd_per_m_good_at_knee"] < by["fp16"]["usd_per_m_good_at_knee"]
    assert by["fp16"]["ttft_p50_ms_at_common"] == 120 and by["fp16"]["weights_gib"] == 5.75
    assert all(r["common_rps"] == 2 for r in rows)


def test_missing_startup_file_is_tolerated(tmp_path):
    (tmp_path / "sweep_x.json").write_text(json.dumps(fake_sweep("x")))
    res = load_results(tmp_path)
    assert res["x"]["startup"] == {}
