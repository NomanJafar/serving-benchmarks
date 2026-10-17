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


def curve_rows(sweep: dict, gpu_usd_per_hour: float) -> list[dict]:
    rows = []
    for lv in sweep["levels"]:
        out = lv["output_tokens_per_s"]
        good = lv.get("goodput_tokens_per_s")
        rows.append({
            "offered_rps": lv["level"], "achieved_rps": round(lv["requests_per_s"], 3), "requests": lv["requests"], "errors": lv["errors"],
            "out_tok_s": round(out, 1), "ttft_p50_ms": _ms(lv["ttft"]["p50"]), "ttft_p95_ms": _ms(lv["ttft"]["p95"]), "ttft_p99_ms": _ms(lv["ttft"].get("p99")),
            "tpot_p50_ms": _ms(lv["tpot"]["p50"]), "itl_p50_ms": _ms(lv["itl"]["p50"]), "itl_p99_ms": _ms(lv["itl"].get("p99")),
            "e2e_p50_s": round(lv["e2e"]["p50"], 2) if lv["e2e"]["p50"] is not None else None,
            "slo_pass_rate": lv.get("slo_pass_rate"), "goodput_rps": lv.get("goodput_requests_per_s"),
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
