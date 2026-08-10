"""
15_model_comparison_summary.py

Creates a compact comparison table for the revised VOC models.

Compares:
- main revised model with first-contract status
- sensitivity model without first-contract status

The goal is to make the modelling results easy to interpret and clearly mark
them as diagnostic rather than central evidence.
"""

import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
TABLES = os.path.join(BASE, "tables")
DOCS = os.path.join(BASE, "docs")

os.makedirs(TABLES, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)


def first_numeric(row, columns):
    for col in columns:
        if col in row.index:
            value = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(value):
                return float(value)
    return None


def extract_metrics(path, model_name, feature_set):
    df = pd.read_csv(path)

    out = {
        "model": model_name,
        "feature_set": feature_set,
        "accuracy": None,
        "macro_precision": None,
        "macro_recall": None,
        "macro_f1": None,
        "weighted_precision": None,
        "weighted_recall": None,
        "weighted_f1": None,
    }

    accuracy_row = df[df["class_or_average"] == "accuracy"]
    if not accuracy_row.empty:
        row = accuracy_row.iloc[0]
        out["accuracy"] = first_numeric(row, ["precision", "recall", "f1-score", "support"])

    macro_row = df[df["class_or_average"] == "macro avg"]
    if not macro_row.empty:
        row = macro_row.iloc[0]
        out["macro_precision"] = pd.to_numeric(row.get("precision"), errors="coerce")
        out["macro_recall"] = pd.to_numeric(row.get("recall"), errors="coerce")
        out["macro_f1"] = pd.to_numeric(row.get("f1-score"), errors="coerce")

    weighted_row = df[df["class_or_average"] == "weighted avg"]
    if not weighted_row.empty:
        row = weighted_row.iloc[0]
        out["weighted_precision"] = pd.to_numeric(row.get("precision"), errors="coerce")
        out["weighted_recall"] = pd.to_numeric(row.get("recall"), errors="coerce")
        out["weighted_f1"] = pd.to_numeric(row.get("f1-score"), errors="coerce")

    return out


rows = [
    extract_metrics(
        os.path.join(TABLES, "model_logit_classification_report_revised.csv"),
        "Logistic Regression",
        "with first-contract status"
    ),
    extract_metrics(
        os.path.join(TABLES, "model_rf_classification_report_revised.csv"),
        "Random Forest",
        "with first-contract status"
    ),
    extract_metrics(
        os.path.join(TABLES, "model_sensitivity_no_first_contract_logit_report.csv"),
        "Logistic Regression",
        "without first-contract status"
    ),
    extract_metrics(
        os.path.join(TABLES, "model_sensitivity_no_first_contract_rf_report.csv"),
        "Random Forest",
        "without first-contract status"
    ),
]

comparison = pd.DataFrame(rows)

metric_cols = [
    "accuracy",
    "macro_precision",
    "macro_recall",
    "macro_f1",
    "weighted_precision",
    "weighted_recall",
    "weighted_f1",
]

for col in metric_cols:
    comparison[col] = pd.to_numeric(comparison[col], errors="coerce").round(3)

comparison_path = os.path.join(TABLES, "model_comparison_summary_revised.csv")
comparison.to_csv(comparison_path, index=False)
print(f"[saved] {comparison_path}")

notes_path = os.path.join(DOCS, "model_comparison_summary_revised.txt")

with open(notes_path, "w", encoding="utf-8") as f:
    f.write("MODEL COMPARISON SUMMARY - Revised VOC outcome prediction\n\n")

    f.write(
        "This table compares the main revised models with the sensitivity models "
        "that exclude first-contract status.\n\n"
    )

    f.write(comparison.to_string(index=False))
    f.write("\n\n")

    f.write("Interpretation:\n")
    f.write(
        "The models have modest predictive performance overall. "
        "The Random Forest models perform slightly better than Logistic Regression, "
        "but neither model separates all revised outcome groups strongly. "
        "The sensitivity model without first-contract status performs similarly to the main model. "
        "This suggests that the modelling results are not driven only by the first-contract variable. "
        "However, the results should remain diagnostic and supplementary rather than central evidence.\n"
    )

print(f"[saved] {notes_path}")
print("[done] Model comparison summary complete.")