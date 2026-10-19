import json

from serving_benchmarks.cli import main
from serving_benchmarks.configs import CONFIGS, by_slug, serve_command, system_prompt
from serving_benchmarks.report import build_report


def test_the_three_scoped_configs_plus_the_attribution_row_exist():
    slugs = [c.slug for c in CONFIGS]
    assert slugs == ["fp16", "fp16-prefix", "awq-prefix", "specdec-k1"]
    assert "--no-enable-prefix-caching" in by_slug("fp16").extra_args
    assert by_slug("awq-prefix").model.endswith("-AWQ")
    spec = by_slug("specdec-k1")
    cfg = json.loads(spec.extra_args[spec.extra_args.index("--speculative-config") + 1])
    assert cfg["method"] == "draft_model" and cfg["num_speculative_tokens"] == 1


def test_serve_command_is_a_runnable_vllm_line():
    cmd = serve_command(by_slug("awq-prefix"))
    assert cmd[:3] == ["vllm", "serve", "Qwen/Qwen2.5-3B-Instruct-AWQ"] and "--dtype" in cmd and "float16" in cmd


def test_system_prompt_is_deterministic_and_long_enough():
    a, b = system_prompt(), system_prompt()
    assert a == b and 450 <= len(a.split()) <= 700


def test_build_report_writes_tables_json_and_plots(results_dir):
    out = results_dir / "report"
    files = build_report(results_dir, out, gpu_usd_per_hour=0.35, common_rps=2)
    names = {f.name for f in files}
    assert {"summary.md", "curves.md", "summary.json", "ttft.png", "itl.png", "throughput.png", "goodput.png", "cost.png"} <= names
    md = (out / "summary.md").read_text()
    assert "awq-prefix" in md and "fp16" in md
    data = json.loads((out / "summary.json").read_text())
    assert data["gpu_usd_per_hour"] == 0.35 and len(data["summary"]) == 3 and "fp16" in data["curves"]


def test_cli_report_and_configs(results_dir, capsys):
    main(["report", "--results", str(results_dir), "--gpu-usd-per-hour", "0.35", "--common-rps", "2"])
    assert (results_dir / "report" / "summary.md").exists()
    main(["configs"])
    out = capsys.readouterr().out
    assert "vllm serve Qwen/Qwen2.5-3B-Instruct" in out and "--speculative-config" in out


def test_cli_compare_writes_markdown_and_json(results_dir, tmp_path, capsys):
    out = tmp_path / "repeatability.md"
    main(["compare", "--results", str(results_dir), str(results_dir), "--gpu-usd-per-hour", "0.35", "--out", str(out)])
    assert out.exists() and out.with_suffix(".json").exists()
    assert "| awq-prefix | 2 |" in out.read_text()
