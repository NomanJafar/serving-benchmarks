"""`serving-benchmarks report|configs|sweep-args`."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

from serving_benchmarks.configs import CONFIGS, serve_command, system_prompt
from serving_benchmarks.report import build_report

SWEEP_LEVELS = "0.5,1,2,4,6,8"
SWEEP_DURATION = 60
SLO_TTFT_MS = 1000
SLO_TPOT_MS = 60


def sweep_args(base_url: str, model: str, out: str, levels: str = SWEEP_LEVELS, duration: int = SWEEP_DURATION) -> list[str]:
    """The tokenbench command every configuration is measured with (METHODOLOGY.md section 3)."""
    return ["tokenbench", "sweep", "--base-url", base_url, "--model", model, "--mode", "open", "--levels", levels,
            "--duration", str(duration), "--warmup", "4", "--prompts", "sample", "--max-tokens", "192", "--no-ignore-eos",
            "--system-prompt", system_prompt(), "--slo-ttft-ms", str(SLO_TTFT_MS), "--slo-tpot-ms", str(SLO_TPOT_MS),
            "--request-timeout", "120", "--out", out]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="latency, throughput and cost report for the three serving configurations")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="build tables and plots from a results directory of tokenbench sweeps")
    r.add_argument("--results", type=Path, required=True)
    r.add_argument("--out", type=Path, default=None, help="default: <results>/report")
    r.add_argument("--gpu-usd-per-hour", type=float, required=True)
    r.add_argument("--common-rps", type=float, default=2.0, help="the offered load at which configs are compared side by side")
    r.add_argument("--no-plots", action="store_true")
    sub.add_parser("configs", help="print the vllm serve line for each configuration")
    s = sub.add_parser("sweep-args", help="print the tokenbench command (without the long system prompt)")
    s.add_argument("--base-url", default="http://127.0.0.1:8000")
    s.add_argument("--model", default=CONFIGS[0].model)
    a = p.parse_args(argv)
    if a.cmd == "report":
        files = build_report(a.results, a.out or a.results / "report", a.gpu_usd_per_hour, a.common_rps, plots=not a.no_plots)
        print("\n".join(str(f) for f in files))
    elif a.cmd == "configs":
        for c in CONFIGS:
            print(f"# {c.slug}: {c.name}\n{shlex.join(serve_command(c))}\n")
    else:
        args = sweep_args(a.base_url, a.model, "results/sweep_<slug>.json")
        i = args.index("--system-prompt")
        args[i + 1] = "<system_prompt()>"
        print(shlex.join(args))


if __name__ == "__main__":
    main()
