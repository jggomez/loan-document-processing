import collections

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_recall_fscore_support


def calculate_tagging_metrics(docs_data: list) -> dict:
    """
    docs_data: dictionary [{'predicted_type': 'w9', 'actual_type': 'w9'}, ...]
    """
    df = pd.DataFrame(docs_data)
    y_pred = df["predicted_type"]
    y_true = df["actual_type"]

    labels = sorted(list(set(y_true.unique()) | set(y_pred.unique())))
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, _, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    cm = confusion_matrix(y_true, y_pred, labels=labels)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": cm,
        "labels": labels,
    }


def _normalize_text(text):
    if text is None:
        return ""
    return str(text).lower().strip()


def _calculate_exact_match(pred, truth):
    return 1.0 if _normalize_text(pred) == _normalize_text(truth) else 0.0


def _calculate_f1_token(pred, truth):
    """
    Calculate F1 based on tokens or words.
    """

    pred_tokens = _normalize_text(pred).split()
    truth_tokens = _normalize_text(truth).split()

    if not pred_tokens and not truth_tokens:
        return 1.0

    if not pred_tokens or not truth_tokens:
        return 0.0

    common = collections.Counter(pred_tokens) & collections.Counter(truth_tokens)
    num_same = sum(common.values())

    if num_same == 0:
        return 0.0

    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)

    return f1


def calculate_extraction_metrics(reviewed_docs):
    """
    reviewed_docs:
    [
      {
        "doc_type": "w9_form",
        "predicted_data": {"legal_name": "Acme Corp", "ein": "12-345"},
        "corrected_data": {"legal_name": "Acme Corporation", "ein": "12-345"}
      },
      ...
    ]
    """

    field_metrics = {}

    for doc in reviewed_docs:
        truth_json = doc["corrected_data"]
        pred_json = doc["predicted_data"]

        for field, true_val in truth_json.items():
            pred_val = pred_json.get(field, None)

            if field not in field_metrics:
                field_metrics[field] = {"exact": [], "f1": []}

            field_metrics[field]["exact"].append(
                _calculate_exact_match(pred_val, true_val)
            )
            field_metrics[field]["f1"].append(_calculate_f1_token(pred_val, true_val))

    # Macro-Average per field
    results = []
    for field, scores in field_metrics.items():
        results.append(
            {
                "field_name": field,
                "exact_match_rate": sum(scores["exact"]) / len(scores["exact"]),
                "token_f1_score": sum(scores["f1"]) / len(scores["f1"]),
                "samples": len(scores["exact"]),
            }
        )

    return results


def calculate_cost(usage_metadata):
    """
    Calculate the cost based on Gemini 2.5 Flash Pricing.
    Prices per 1 million tokens: entry $0.30, exit $2.50.
    https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-flash
    """
    PRICE_PER_1M_INPUT = 0.30
    PRICE_PER_1M_OUTPUT = 2.50

    if not usage_metadata:
        return 0.0

    prompt_tokens = usage_metadata.prompt_token_count
    candidate_tokens = usage_metadata.candidates_token_count
    thinking_tokens = usage_metadata.thoughts_token_count or 0
    total_output_tokens = candidate_tokens + thinking_tokens

    input_cost = (prompt_tokens / 1_000_000) * PRICE_PER_1M_INPUT
    output_cost = (total_output_tokens / 1_000_000) * PRICE_PER_1M_OUTPUT

    total_cost = input_cost + output_cost

    return total_cost


def calculate_ops_metrics(ops_data: list):
    """
    ops_data:
    Ej: [{'latency_seconds': 2.1, 'cost_usd': 0.0002, 'status': 'auto_approved'}, ...]
    """
    if not ops_data:
        return None

    df = pd.DataFrame(ops_data)

    latencies = df["latency_seconds"].values
    p50_latency = np.percentile(latencies, 50)
    p95_latency = np.percentile(latencies, 95)

    avg_cost = df["cost_usd"].mean()
    total_cost = df["cost_usd"].sum()

    total_docs = len(df)
    auto_approved_count = len(df[df["status"] == "auto_approved"])

    auto_approve_rate = auto_approved_count / total_docs
    human_review_rate = 1.0 - auto_approve_rate

    return {
        "p50_latency": p50_latency,
        "p95_latency": p95_latency,
        "cost_per_doc": avg_cost,
        "auto_approve_rate": auto_approve_rate,
        "human_review_rate": human_review_rate,
        "total_cost": total_cost,
        "total_docs": total_docs,
    }
