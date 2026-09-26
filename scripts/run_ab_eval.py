"""Run the reproducible dense-only versus hybrid RAGAS evaluation."""

import argparse
import json
import math
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.run_config import RunConfig

from src.task9_retrieval_pipeline import SCORE_THRESHOLD, retrieve
from src.task10_generation import (
    LLM_MODEL,
    SAFE_REFUSAL,
    SYSTEM_PROMPT,
    call_llm,
    format_context,
    reorder_for_llm,
)


ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT_PATH = ROOT / "group_project" / "evaluation" / "ab_results.json"
TOP_K = 5
METRIC_NAMES = (
    "faithfulness",
    "answer_relevancy",
    "context_recall",
    "context_precision",
)


def mean_finite(values: list[float | None]) -> float | None:
    """Average completed RAGAS scores without disguising timed-out samples."""
    completed = [value for value in values if value is not None and math.isfinite(value)]
    return round(fmean(completed), 4) if completed else None


def load_golden_dataset(path: Path = GOLDEN_PATH) -> list[dict[str, str]]:
    """Load the hand-grounded questions used by both configurations."""
    items = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(items, list) or not items:
        raise ValueError("golden dataset must be a non-empty JSON list")
    return items


def run_one(question: str, use_reranking: bool) -> dict[str, Any]:
    """Retrieve and answer one question without changing the public API."""
    started_at = time.perf_counter()
    chunks = retrieve(question, top_k=TOP_K, use_reranking=use_reranking)
    if not chunks:
        return {
            "answer": SAFE_REFUSAL,
            "contexts": [],
            "source_ids": [],
            "latency_seconds": 0.0,
        }

    context = format_context(reorder_for_llm(chunks))
    user_message = f"Context:\n{context}\n\nCâu hỏi: {question}"
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message).strip()
    except Exception:
        answer = SAFE_REFUSAL

    return {
        "answer": answer or SAFE_REFUSAL,
        "contexts": [chunk["content"] for chunk in chunks],
        "source_ids": [chunk["id"] for chunk in chunks],
        "latency_seconds": round(time.perf_counter() - started_at, 3),
    }


def build_samples(
    items: list[dict[str, str]], use_reranking: bool
) -> tuple[EvaluationDataset, list[dict[str, Any]]]:
    """Generate answers and convert them to the RAGAS input schema."""
    samples: list[SingleTurnSample] = []
    rows: list[dict[str, Any]] = []
    for item in items:
        output = run_one(item["question"], use_reranking)
        rows.append({**item, **output})
        samples.append(
            SingleTurnSample(
                user_input=item["question"],
                response=output["answer"],
                retrieved_contexts=output["contexts"],
                reference=item["expected_answer"],
            )
        )
    return EvaluationDataset(samples=samples), rows


def make_evaluator() -> tuple[LangchainLLMWrapper, LangchainEmbeddingsWrapper]:
    """Pin the online evaluator to the configured OpenAI models."""
    evaluator_model = os.getenv("EVALUATOR_MODEL", LLM_MODEL or "gpt-4o-mini")
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    llm = LangchainLLMWrapper(
        ChatOpenAI(model=evaluator_model, temperature=0, timeout=60, max_retries=2)
    )
    embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model=embedding_model, timeout=60, max_retries=2)
    )
    return llm, embeddings


def score_config(
    items: list[dict[str, str]], use_reranking: bool
) -> dict[str, Any]:
    """Run one retrieval configuration and retain aggregate and row scores."""
    dataset, rows = build_samples(items, use_reranking)
    llm, embeddings = make_evaluator()
    answer_relevancy.strictness = 1
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=embeddings,
        run_config=RunConfig(timeout=20, max_retries=0, max_workers=16),
        raise_exceptions=False,
        show_progress=True,
    )
    for row, score in zip(rows, result.scores, strict=True):
        row["metrics"] = {
            name: float(value) if math.isfinite(value := float(score[name])) else None
            for name in METRIC_NAMES
        }

    aggregates = {
        name: mean_finite([row["metrics"][name] for row in rows])
        for name in METRIC_NAMES
    }
    aggregates["average"] = mean_finite(list(aggregates.values()))
    return {
        "aggregates": aggregates,
        "average_latency_seconds": round(
            fmean(row["latency_seconds"] for row in rows), 3
        ),
        "rows": rows,
    }


def current_commit() -> str:
    """Return the corpus code revision without requiring GitPython."""
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
    ).strip()


def run_evaluation(
    output_path: Path = OUTPUT_PATH,
    *,
    config: str = "all",
    start: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    """Evaluate selected retrieval strategies and write machine-readable evidence."""
    load_dotenv(ROOT / ".env")
    items = load_golden_dataset()
    items = items[start:] if limit is None else items[start : start + limit]
    if not items:
        raise ValueError("the selected evaluation slice is empty")
    run = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "corpus_commit": current_commit(),
        "dataset_size": len(items),
        "top_k": TOP_K,
        "score_threshold": SCORE_THRESHOLD,
        "generator_model": LLM_MODEL or "gpt-4o-mini",
        "evaluator_model": os.getenv("EVALUATOR_MODEL", LLM_MODEL or "gpt-4o-mini"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        "start": start,
        "config": config,
    }
    if config in {"all", "dense"}:
        run["config_a_dense_only"] = score_config(items, use_reranking=False)
    if config in {"all", "hybrid"}:
        run["config_b_hybrid_rrf"] = score_config(items, use_reranking=True)
    output_path.write_text(
        json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return run


def merge_partial_runs(paths: list[Path], output_path: Path) -> dict[str, Any]:
    """Merge sliced runs into one full, reproducible A/B artifact."""
    partials = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if not partials:
        raise ValueError("provide at least one partial result file")

    merged: dict[str, Any] = {
        key: partials[0][key]
        for key in (
            "run_at_utc",
            "corpus_commit",
            "top_k",
            "score_threshold",
            "generator_model",
            "evaluator_model",
            "embedding_model",
        )
    }
    for config_name in ("config_a_dense_only", "config_b_hybrid_rrf"):
        rows = [
            row
            for partial in partials
            for row in partial.get(config_name, {}).get("rows", [])
        ]
        if not rows:
            continue
        rows.sort(key=lambda row: row["question"])
        aggregates = {
            name: mean_finite([row["metrics"][name] for row in rows])
            for name in METRIC_NAMES
        }
        aggregates["average"] = mean_finite(list(aggregates.values()))
        merged[config_name] = {
            "aggregates": aggregates,
            "average_latency_seconds": round(
                fmean(row["latency_seconds"] for row in rows), 3
            ),
            "rows": rows,
        }
    merged["dataset_size"] = len(
        merged.get("config_a_dense_only", merged["config_b_hybrid_rrf"])["rows"]
    )
    output_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return merged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--config", choices=("all", "dense", "hybrid"), default="all")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--merge", type=Path, nargs="+")
    args = parser.parse_args()
    completed = (
        merge_partial_runs(args.merge, args.output)
        if args.merge
        else run_evaluation(
            args.output, config=args.config, start=args.start, limit=args.limit
        )
    )
    for name in ("config_a_dense_only", "config_b_hybrid_rrf"):
        if name not in completed:
            continue
        print(f"{name}: {completed[name]['aggregates']}")
    print(f"Wrote {args.output}")
