"""The serving configurations under test, as data, and the exact `vllm serve` line for each (METHODOLOGY.md section 2)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

TARGET = "Qwen/Qwen2.5-3B-Instruct"
AWQ = "Qwen/Qwen2.5-3B-Instruct-AWQ"
DRAFT = "Qwen/Qwen2.5-0.5B-Instruct"


@dataclass(frozen=True)
class BenchConfig:
    slug: str
    name: str
    model: str
    extra_args: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


def _spec(k: int) -> tuple[str, ...]:
    return ("--speculative-config", json.dumps({"method": "draft_model", "model": DRAFT, "num_speculative_tokens": k}))


CONFIGS: list[BenchConfig] = [
    BenchConfig("fp16", "FP16 baseline (prefix caching off)", TARGET, ("--no-enable-prefix-caching",),
                "the plain server: every prompt pays its full prefill"),
    BenchConfig("fp16-prefix", "FP16 + prefix caching", TARGET, (),
                "attribution row: isolates the prefix-caching gain from the quantisation gain in the next config"),
    BenchConfig("awq-prefix", "AWQ + prefix caching", AWQ, (),
                "4-bit AWQ weights (official Qwen checkpoint; vLLM picks the kernel), prefix caching on"),
    BenchConfig("specdec-k1", "FP16 + speculative decoding (draft 0.5B, k=1)", TARGET, _spec(1),
                "k=1 was the only speculation setting that paid off on this GPU in specdec"),
]


def by_slug(slug: str) -> BenchConfig:
    for c in CONFIGS:
        if c.slug == slug:
            return c
    raise KeyError(slug)


def serve_command(cfg: BenchConfig, port: int = 8000, max_model_len: int = 4096, gpu_memory_utilization: float = 0.9) -> list[str]:
    return ["vllm", "serve", cfg.model, "--dtype", "float16", "--max-model-len", str(max_model_len),
            "--gpu-memory-utilization", str(gpu_memory_utilization), "--port", str(port), *cfg.extra_args]


_POLICY = [
    "You are the support assistant for Northwind Cloud, a managed hosting provider.",
    "Answer only questions about Northwind products: virtual machines, managed databases, object storage, load balancers and DNS.",
    "If a question is outside that scope, say so in one sentence and point the customer to the community forum.",
    "Never quote prices from memory; direct the customer to the pricing page and offer to explain how a line item is computed.",
    "When a customer reports an outage, first ask for the region, the resource identifier and the time the problem started, then explain the status page.",
    "Use plain language, short paragraphs and at most one list per answer.",
    "Do not promise refunds, credits or timelines; escalate billing disputes to a human agent by telling the customer how to open a ticket.",
    "For security questions, explain the shared-responsibility model: Northwind secures the platform, the customer secures their workloads, keys and access policies.",
    "If asked to run commands, give the exact command, explain each flag briefly and warn about anything destructive.",
    "Keep a calm tone, acknowledge frustration once, and move to the next concrete step.",
]


def system_prompt(target_words: int = 560) -> str:
    """A deterministic, realistic system prompt of about `target_words` words: the shared prefix every request carries."""
    out: list[str] = ["Northwind Cloud support policy, version 7."]
    i = 0
    while sum(len(s.split()) for s in out) < target_words:
        out.append(f"Rule {i + 1}. {_POLICY[i % len(_POLICY)]}")
        i += 1
    return " ".join(out)
