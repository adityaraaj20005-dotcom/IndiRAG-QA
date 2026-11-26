"""Reproducible, Unicode-aware QA evaluation without fabricated scores."""
from __future__ import annotations

from collections import Counter, defaultdict
import re
import unicodedata
from statistics import mean
from typing import Any, Callable


def normalize(text: str | None) -> str:
    """Normalize English, Devanagari and Romanized Hindi safely for EM."""
    text = unicodedata.normalize("NFC", text or "").casefold()
    return " ".join("".join(c if unicodedata.category(c)[0] in "LMN" else " " for c in text).split())


def tokens(text: str | None) -> list[str]:
    return normalize(text).split()


def exact_match(prediction: str | None, references: list[str]) -> float:
    predicted = normalize(prediction)
    return float(bool(references) and any(predicted == normalize(ref) for ref in references))


def token_f1(prediction: str | None, references: list[str]) -> float:
    predicted = tokens(prediction)
    if not references:
        return 0.0
    scores = []
    for reference in references:
        expected = tokens(reference)
        overlap = sum((Counter(predicted) & Counter(expected)).values())
        if not predicted and not expected:
            scores.append(1.0)
        elif not overlap:
            scores.append(0.0)
        else:
            precision = overlap / len(predicted)
            recall = overlap / len(expected)
            scores.append(2 * precision * recall / (precision + recall))
    return max(scores)


def _answerability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(r["gold_answerable"] and r["pred_answerable"] for r in rows)
    tn = sum(not r["gold_answerable"] and not r["pred_answerable"] for r in rows)
    fp = sum(not r["gold_answerable"] and r["pred_answerable"] for r in rows)
    fn = sum(r["gold_answerable"] and not r["pred_answerable"] for r in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "accuracy": (tp + tn) / len(rows) if rows else None,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "true_positives": tp, "true_negatives": tn,
        "false_positives": fp, "false_negatives": fn,
        "confusion_matrix": {"actual_answerable": {"pred_answerable": tp, "pred_unanswerable": fn}, "actual_unanswerable": {"pred_answerable": fp, "pred_unanswerable": tn}},
    }


def summarize(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate successful predictions; failures remain visible, not abstentions."""
    completed = [p for p in predictions if p.get("status") == "ok"]
    failures = [p for p in predictions if p.get("status") != "ok"]
    assessed = []
    for item in completed:
        gold = bool(item["answerable"])
        pred = item.get("answerability") == "ANSWERABLE"
        assessed.append({"gold_answerable": gold, "pred_answerable": pred})
        item["exact_match"] = exact_match(item.get("answer"), item.get("reference_answers", [])) if gold else None
        item["token_f1"] = token_f1(item.get("answer"), item.get("reference_answers", [])) if gold else None
    answerable = [p for p in completed if p["answerable"]]
    cited = [p for p in completed if p.get("answerability") == "ANSWERABLE"]
    citation_valid = [p for p in cited if p.get("citation_valid") is not None]
    return {
        "n": len(predictions), "completed": len(completed), "generation_failures": len(failures),
        "exact_match": mean([p["exact_match"] for p in answerable]) if answerable else None,
        "token_f1": mean([p["token_f1"] for p in answerable]) if answerable else None,
        "mean_latency_ms": mean([p["latency_ms"] for p in completed]) if completed else None,
        "citation_validity_rate": mean([float(p["citation_valid"]) for p in citation_valid]) if citation_valid else None,
        "citation_evaluable": len(citation_valid),
        "answerability": _answerability(assessed),
    }


def by_language(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prediction in predictions:
        groups[prediction.get("language", "Unknown")].append(prediction)
    return {language: summarize(rows) for language, rows in groups.items()}


def run_pipeline(rows: list[dict[str, Any]], runner: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    predictions = []
    for row in rows:
        try:
            result = runner(row)
            predictions.append({**row, **result, "status": "ok"})
        except Exception as exc:  # Preserve operational failures separately.
            predictions.append({**row, "status": "error", "error_type": type(exc).__name__, "error": str(exc)[:300]})
    return {"aggregate": summarize(predictions), "language_wise": by_language(predictions), "predictions": predictions}
