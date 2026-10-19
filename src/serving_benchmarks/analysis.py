"""From tokenbench sweep JSON to load curves, knees, $/M tokens and the cross-config summary (METHODOLOGY.md section 4)."""

from __future__ import annotations

import json
from pathlib import Path


def usd_per_m_tokens(gpu_usd_per_hour: float, tokens_per_s: float | None) -> float | None:
    """What a million tokens cost when the GPU produces `tokens_per_s` of them for `gpu_usd_per_hour`."""
    if not tokens_per_s or tokens_per_s <= 0:
        return None
    return gpu_usd_per_hour / 3600 / tokens_per_s * 1e6


def _ms(x) -> float | None:
    return None if x is None else round(x * 1000, 1)


def _pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * q / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def per_token_slo(records: list[dict], wall_s: float, ttft_ms: float, tpot_ms: float) -> dict:
    """SLO pass rate, goodput and TPOT recomputed per *token* from tokenbench's per-request records.

    tokenbench (before its 18 Oct fix) divided TPOT by the number of stream chunks; a speculative server sends
    about 1.7 tokens per chunk, so its recorded TPOT and SLO pass rate were wrong by that factor. The records
    carry ttft_s, e2e_s and the server's completion_tokens, which is enough to redo it: TPOT = (e2e - ttft) /
    (completion_tokens - 1)."""
    tpots, good_tokens, passed = [], 0, 0
    for r in records:
        if r.get("error") is not None or r.get("ttft_s") is None or (r.get("completion_tokens") or 0) < 2:
            continue
        tpot = (r["e2e_s"] - r["ttft_s"]) / (r["completion_tokens"] - 1)
        tpots.append(tpot)
        if r["ttft_s"] * 1000 <= ttft_ms and tpot * 1000 <= tpot_ms:
            passed += 1
            good_tokens += r["completion_tokens"]
    n = len(records)
    return {"tpot_p50_ms": _ms(_pct(tpots, 50)), "tpot_p95_ms": _ms(_pct(tpots, 95)), "slo_pass_rate": passed / n if n else None,
            "goodput_tok_s": round(good_tokens / wall_s, 1) if wall_s else None}


def curve_rows(sweep: dict, gpu_usd_per_hour: float, ttft_ms: float = 1000.0, tpot_ms: float = 60.0) -> list[dict]:
    rows = []
    for lv in sweep["levels"]:
        out = lv["output_tokens_per_s"]
        good = lv.get("goodput_tokens_per_s")
        recomputed = None
        if lv.get("per_request"):
            slo = lv.get("slo") or {}
            recomputed = per_token_slo(lv["per_request"], lv["wall_s"], slo.get("ttft_ms", ttft_ms), slo.get("tpot_ms", tpot_ms))
            good = recomputed["goodput_tok_s"]
        rows.append({
            "offered_rps": lv["level"], "achieved_rps": round(lv["requests_per_s"], 3), "requests": lv["requests"], "errors": lv["errors"],
            "out_tok_s": round(out, 1), "ttft_p50_ms": _ms(lv["ttft"]["p50"]), "ttft_p95_ms": _ms(lv["ttft"]["p95"]), "ttft_p99_ms": _ms(lv["ttft"].get("p99")),
            "tpot_p50_ms": recomputed["tpot_p50_ms"] if recomputed else _ms(lv["tpot"]["p50"]), "itl_p50_ms": _ms(lv["itl"]["p50"]), "itl_p99_ms": _ms(lv["itl"].get("p99")),
            "e2e_p50_s": round(lv["e2e"]["p50"], 2) if lv["e2e"]["p50"] is not None else None,
            "slo_pass_rate": recomputed["slo_pass_rate"] if recomputed else lv.get("slo_pass_rate"),
            "slo_pass_rate_chunks": lv.get("slo_pass_rate") if recomputed else None,
            "goodput_rps": lv.get("goodput_requests_per_s"),
            "goodput_tok_s": round(good, 1) if good is not None else None,
            "usd_per_m_out": usd_per_m_tokens(gpu_usd_per_hour, out), "usd_per_m_good": usd_per_m_tokens(gpu_usd_per_hour, good),
        })
    return rows


def knee(rows: list[dict]) -> dict:
    """The level with the most goodput: past it, offering more load only produces tokens nobody waits for."""
    with_good = [r for r in rows if r.get("goodput_tok_s") is not None]
    if with_good:
        return max(with_good, key=lambda r: r["goodput_tok_s"])
    return max(rows, key=lambda r: r["out_tok_s"])


def load_results(results_dir: Path | str) -> dict[str, dict]:
    """{slug: {"sweep": tokenbench JSON, "startup": startup_<slug>.json or {}}} for every sweep_<slug>.json in the directory."""
    d = Path(results_dir)
    out = {}
    for p in sorted(d.glob("sweep_*.json")):
        slug = p.stem[len("sweep_"):]
        sp = d / f"startup_{slug}.json"
        out[slug] = {"sweep": json.loads(p.read_text()), "startup": json.loads(sp.read_text()) if sp.exists() else {}}
    return out


def _at(rows: list[dict], rps: float) -> dict | None:
    return next((r for r in rows if abs(r["offered_rps"] - rps) < 1e-9), None)


def summary_rows(results: dict[str, dict], gpu_usd_per_hour: float, common_rps: float) -> list[dict]:
    rows = []
    for slug, res in results.items():
        curve = curve_rows(res["sweep"], gpu_usd_per_hour)
        k = knee(curve)
        c = _at(curve, common_rps) or {}
        st = res.get("startup") or {}
        rows.append({
            "config": slug, "weights_gib": st.get("model_load_gib"), "kv_cache_tokens": st.get("kv_cache_tokens"), "startup_s": st.get("startup_s"),
            "knee_rps": k["offered_rps"], "knee_out_tok_s": k["out_tok_s"], "knee_goodput_tok_s": k["goodput_tok_s"], "knee_slo_pass_rate": k["slo_pass_rate"],
            "usd_per_m_out_at_knee": k["usd_per_m_out"], "usd_per_m_good_at_knee": k["usd_per_m_good"],
            "common_rps": common_rps, "ttft_p50_ms_at_common": c.get("ttft_p50_ms"), "ttft_p95_ms_at_common": c.get("ttft_p95_ms"),
            "itl_p50_ms_at_common": c.get("itl_p50_ms"), "itl_p99_ms_at_common": c.get("itl_p99_ms"),
            "out_tok_s_at_common": c.get("out_tok_s"), "slo_pass_rate_at_common": c.get("slo_pass_rate"), "usd_per_m_out_at_common": c.get("usd_per_m_out"),
        })
    return rows


def _spread(vals: list) -> float | None:
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return None
    mean = sum(vals) / len(vals)
    return (max(vals) - min(vals)) / mean if mean else None


def _column(rows: list[dict]):
    return lambda name: [r.get(name) for r in rows]


def compare_runs(results_dirs: list, gpu_usd_per_hour: float, common_rps: float) -> list[dict]:
    """Repeatability across several result directories of the same configurations: per config, the knee and
    the latency at the common level from every run, and the relative spread (max - min over the mean)."""
    per: dict[str, list[dict]] = {}
    for d in results_dirs:
        for row in summary_rows(load_results(d), gpu_usd_per_hour, common_rps):
            per.setdefault(row["config"], []).append(row)
    out = []
    for cfg, rows in per.items():
        col = _column(rows)
        out.append({
            "config": cfg, "runs": len(rows),
            "knee_rps": col("knee_rps"), "knee_goodput_tok_s": col("knee_goodput_tok_s"), "knee_goodput_spread": _spread(col("knee_goodput_tok_s")),
            "usd_per_m_good_at_knee": col("usd_per_m_good_at_knee"),
            "ttft_p50_ms_at_common": col("ttft_p50_ms_at_common"), "ttft_spread": _spread(col("ttft_p50_ms_at_common")),
            "itl_p50_ms_at_common": col("itl_p50_ms_at_common"), "itl_spread": _spread(col("itl_p50_ms_at_common")),
            "out_tok_s_at_common": col("out_tok_s_at_common"), "out_tok_s_spread": _spread(col("out_tok_s_at_common")),
            "slo_pass_rate_at_common": col("slo_pass_rate_at_common"),
        })
    return out


def repeatability_markdown(rows: list[dict]) -> str:
    def lst(v):
        return " / ".join("–" if x is None else (f"{x:.3g}" if isinstance(x, float) else str(x)) for x in v)

    def pc(v):
        return "–" if v is None else f"{v * 100:.0f} %"
    head = "| config | runs | knee req/s | goodput tok/s at knee | spread | $/M good at knee | TTFT p50 ms @common | spread | ITL p50 ms @common | spread | out tok/s @common | spread |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    body = "\n".join(f"| {r['config']} | {r['runs']} | {lst(r['knee_rps'])} | {lst(r['knee_goodput_tok_s'])} | {pc(r['knee_goodput_spread'])} | "
                      f"{lst(r['usd_per_m_good_at_knee'])} | {lst(r['ttft_p50_ms_at_common'])} | {pc(r['ttft_spread'])} | {lst(r['itl_p50_ms_at_common'])} | {pc(r['itl_spread'])} | "
                      f"{lst(r['out_tok_s_at_common'])} | {pc(r['out_tok_s_spread'])} |" for r in rows)
    return head + body + "\n"


def markdown_table(rows: list[dict], columns: list[str], headers: dict[str, str] | None = None) -> str:
    headers = headers or {}

    def cell(v):
        if v is None:
            return "–"
        if isinstance(v, float):
            if abs(v) < 1:
                return f"{v:.3f}"
            return f"{v:.1f}" if abs(v) < 100 else f"{v:,.0f}"
        if isinstance(v, int):
            return f"{v:,}"
        return str(v)
    head = "| " + " | ".join(headers.get(c, c) for c in columns) + " |\n|" + "---|" * len(columns) + "\n"
    return head + "\n".join("| " + " | ".join(cell(r.get(c)) for c in columns) + " |" for r in rows) + "\n"
