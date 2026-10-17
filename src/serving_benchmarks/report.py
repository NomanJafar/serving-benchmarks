"""Write the report directory: per-config curves, the cross-config summary, and five plots."""

from __future__ import annotations

import json
from pathlib import Path

from serving_benchmarks.analysis import curve_rows, load_results, markdown_table, summary_rows

CURVE_COLS = ["offered_rps", "achieved_rps", "requests", "errors", "out_tok_s", "ttft_p50_ms", "ttft_p95_ms", "tpot_p50_ms", "itl_p50_ms", "itl_p99_ms",
              "slo_pass_rate", "goodput_tok_s", "usd_per_m_out", "usd_per_m_good"]
CURVE_HEADERS = {"offered_rps": "offered req/s", "achieved_rps": "achieved req/s", "out_tok_s": "out tok/s", "ttft_p50_ms": "TTFT p50 ms",
                 "ttft_p95_ms": "TTFT p95 ms", "tpot_p50_ms": "TPOT p50 ms", "itl_p50_ms": "ITL p50 ms", "itl_p99_ms": "ITL p99 ms", "slo_pass_rate": "SLO pass",
                 "goodput_tok_s": "goodput tok/s", "usd_per_m_out": "$/M out", "usd_per_m_good": "$/M good"}
SUMMARY_COLS = ["config", "weights_gib", "kv_cache_tokens", "knee_rps", "knee_out_tok_s", "knee_goodput_tok_s", "knee_slo_pass_rate",
                "usd_per_m_good_at_knee", "ttft_p50_ms_at_common", "itl_p50_ms_at_common", "itl_p99_ms_at_common", "slo_pass_rate_at_common"]
SUMMARY_HEADERS = {"weights_gib": "weights GiB", "kv_cache_tokens": "KV cache tokens", "knee_rps": "knee req/s", "knee_out_tok_s": "out tok/s at knee",
                   "knee_goodput_tok_s": "goodput tok/s at knee", "knee_slo_pass_rate": "SLO pass at knee", "usd_per_m_good_at_knee": "$/M good at knee",
                   "ttft_p50_ms_at_common": "TTFT p50 ms @common", "itl_p50_ms_at_common": "ITL p50 ms @common", "itl_p99_ms_at_common": "ITL p99 ms @common",
                   "slo_pass_rate_at_common": "SLO pass @common"}


def _plots(out: Path, curves: dict[str, list[dict]], gpu_usd_per_hour: float) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    files = []

    def fig_for(name, ylabel, series, logy=False, title=None):
        fig, ax = plt.subplots(figsize=(7, 4.2))
        for slug, rows in curves.items():
            for key, ls, label in series:
                xs = [r["offered_rps"] for r in rows if r.get(key) is not None]
                ys = [r[key] for r in rows if r.get(key) is not None]
                ax.plot(xs, ys, marker="o", ls=ls, label=f"{slug} {label}".strip())
        ax.set_xlabel("offered load (requests / s)"); ax.set_ylabel(ylabel); ax.grid(alpha=.3); ax.legend(fontsize=8)
        if logy:
            ax.set_yscale("log")
        ax.set_title(title or name)
        fig.tight_layout(); p = out / f"{name}.png"; fig.savefig(p, dpi=130); plt.close(fig); files.append(p)

    fig_for("ttft", "TTFT (ms)", [("ttft_p50_ms", "-", "p50"), ("ttft_p95_ms", ":", "p95")], logy=True, title="Time to first token vs offered load")
    fig_for("itl", "inter-token latency (ms)", [("itl_p50_ms", "-", "p50"), ("itl_p99_ms", ":", "p99")], title="Inter-token latency vs offered load")
    fig_for("throughput", "output tokens / s", [("out_tok_s", "-", "")], title="Output throughput vs offered load")
    fig_for("goodput", "tokens / s inside the SLO", [("goodput_tok_s", "-", "")], title="Goodput vs offered load")
    fig_for("cost", f"USD per M output tokens at USD {gpu_usd_per_hour}/h", [("usd_per_m_out", "-", "all tokens"), ("usd_per_m_good", ":", "SLO-meeting tokens")],
            logy=True, title="Cost per million output tokens vs offered load")
    return files


def build_report(results_dir: Path | str, out_dir: Path | str, gpu_usd_per_hour: float, common_rps: float, plots: bool = True) -> list[Path]:
    results = load_results(results_dir)
    if not results:
        raise FileNotFoundError(f"no sweep_*.json in {results_dir}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    curves = {slug: curve_rows(res["sweep"], gpu_usd_per_hour) for slug, res in results.items()}
    summary = summary_rows(results, gpu_usd_per_hour, common_rps)
    files = []
    md = [f"# Summary (GPU at ${gpu_usd_per_hour}/h, common level {common_rps:g} req/s)\n\n",
          markdown_table(summary, SUMMARY_COLS, SUMMARY_HEADERS)]
    (out / "summary.md").write_text("".join(md)); files.append(out / "summary.md")
    cm = []
    for slug, rows in curves.items():
        cm += [f"## {slug}\n\n", markdown_table(rows, CURVE_COLS, CURVE_HEADERS), "\n"]
    (out / "curves.md").write_text("".join(cm)); files.append(out / "curves.md")
    data = {"gpu_usd_per_hour": gpu_usd_per_hour, "common_rps": common_rps, "summary": summary, "curves": curves,
            "startup": {slug: res["startup"] for slug, res in results.items()}}
    (out / "summary.json").write_text(json.dumps(data, indent=1)); files.append(out / "summary.json")
    if plots:
        files += _plots(out, curves, gpu_usd_per_hour)
    return files
