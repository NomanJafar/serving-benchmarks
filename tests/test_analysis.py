import json

from serving_benchmarks.analysis import compare_runs, curve_rows, knee, load_results, summary_rows, usd_per_m_tokens
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


def test_slo_is_recomputed_per_token_from_the_request_records():
    """tokenbench's run-time TPOT divided by stream chunks; a speculative server sends ~1.7 tokens per chunk, so its
    recorded SLO pass rate is too low. When per_request records are present, curve_rows must recompute TPOT as
    (e2e - ttft) / (completion_tokens - 1) and the SLO pass rate and goodput from that."""
    from serving_benchmarks.analysis import per_token_slo
    recs = [{"ttft_s": 0.1, "e2e_s": 0.1 + 0.05 * 99, "completion_tokens": 100, "error": None},     # 50 ms/token: passes
            {"ttft_s": 0.1, "e2e_s": 0.1 + 0.07 * 99, "completion_tokens": 100, "error": None},     # 70 ms/token: fails TPOT
            {"ttft_s": 1.5, "e2e_s": 1.5 + 0.05 * 99, "completion_tokens": 100, "error": None},     # fails TTFT
            {"ttft_s": None, "e2e_s": 2.0, "completion_tokens": 0, "error": "timeout"}]
    s = per_token_slo(recs, wall_s=10.0, ttft_ms=1000, tpot_ms=60)
    assert s["slo_pass_rate"] == 0.25 and s["goodput_tok_s"] == 10.0 and abs(s["tpot_p50_ms"] - 50.0) < 1e-6
    sweep = fake_sweep("x")
    lv = sweep["levels"][0]
    lv["per_request"] = recs
    lv["wall_s"] = 10.0
    lv["slo_pass_rate"] = 0.9            # the chunk-based figure the run recorded
    rows = curve_rows(sweep, 0.35)
    assert rows[0]["slo_pass_rate"] == 0.25 and rows[0]["slo_pass_rate_chunks"] == 0.9 and rows[0]["goodput_tok_s"] == 10.0
    assert rows[1]["slo_pass_rate_chunks"] is None       # levels without records keep the recorded figures


def test_compare_runs_reports_per_config_spread_across_result_dirs(results_dir, tmp_path):
    """Repeatability: the same configurations measured twice. For each config, the knee goodput and the
    latency at the common level from every run, plus the relative spread (max-min over mean)."""
    import json
    import shutil

    run2 = tmp_path / "run2"
    shutil.copytree(results_dir, run2, ignore=shutil.ignore_patterns("report"))
    sweep = json.loads((run2 / "sweep_fp16.json").read_text())
    for lv in sweep["levels"]:
        lv["output_tokens_per_s"] *= 1.1
        lv["goodput_tokens_per_s"] *= 1.1
    (run2 / "sweep_fp16.json").write_text(json.dumps(sweep))
    rows = compare_runs([results_dir, run2], gpu_usd_per_hour=0.35, common_rps=2)
    by = {r["config"]: r for r in rows}
    assert by["fp16"]["runs"] == 2 and by["fp16"]["knee_rps"] == [4, 4]
    assert abs(by["fp16"]["knee_goodput_spread"] - (440 - 400) / 420) < 1e-6
    assert by["awq-prefix"]["knee_goodput_spread"] == 0.0
    t = by["awq-prefix"]["ttft_p50_ms_at_common"]
    assert len(t) == 2 and t[0] == t[1] and abs(t[0] - 92.3) < 0.1
