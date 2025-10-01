"""
03_models.py

Purpose
- Predict contract outcomes (1700–1780 subset) with simple, reproducible models.
- Handle severe class imbalance robustly.
- Save clear diagnostics (confusion matrices, feature importances) and notes.

Target
  outcome_group in {"Death", "Repatriated", "Attrition", "Unknown"}
  You can optionally exclude "Unknown" for a cleaner 3-class task.

Features (guaranteed by 01_cleaning.py)
  Categorical: region_label, rank_parent
  Numeric:     decade, is_high_rank, is_dutch, is_first_contract
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# ---------------- Settings ----------------
INCLUDE_UNKNOWN_CLASS = True  # <- set to False to drop "Unknown" rows from y

# ---------------- Paths ----------------
BASE   = os.path.dirname(os.path.abspath(__file__))
DATA_C = os.path.join(BASE, "data_clean")
FIGS   = os.path.join(BASE, "figures")
DOCS   = os.path.join(BASE, "docs")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

# ---------------- Load ----------------
csv_path = os.path.join(DATA_C, "contracts_clean.csv")
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Missing {csv_path}. Run 01_cleaning.py first.")
contracts = pd.read_csv(csv_path, low_memory=False)

# ---------------- Build modeling set ----------------
valid_targets = {"Death", "Repatriated", "Attrition", "Unknown"}
if "outcome_group" not in contracts.columns:
    raise RuntimeError("contracts_clean.csv lacks 'outcome_group'.")

df = contracts.copy()
df["outcome_group"] = df["outcome_group"].astype(str)

if INCLUDE_UNKNOWN_CLASS:
    df = df[df["outcome_group"].isin(valid_targets)].copy()
else:
    df = df[df["outcome_group"].isin({"Death", "Repatriated", "Attrition"})].copy()

feat_cols_cat = [c for c in ["region_label", "rank_parent"] if c in df.columns]
feat_cols_num = [c for c in ["decade", "is_high_rank", "is_dutch", "is_first_contract"] if c in df.columns]

if not feat_cols_cat and not feat_cols_num:
    raise RuntimeError("No usable feature columns found.")

# categorical -> 'Unknown'; numeric -> median
for c in feat_cols_cat:
    df[c] = df[c].fillna("Unknown").astype(str)
for c in feat_cols_num:
    df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[c].isna().any():
        df[c] = df[c].fillna(df[c].median())

df = df.dropna(subset=["outcome_group"])
df = df.dropna(subset=feat_cols_cat + feat_cols_num)

if len(df) == 0:
    raise RuntimeError(
        "0 rows for modeling after preprocessing. "
        "Check that decade/is_high_rank/is_dutch/is_first_contract exist and that outcome_group is populated."
    )

X = df[feat_cols_cat + feat_cols_num].copy()
y = df["outcome_group"].copy()

# ---------------- Train/Test split ----------------
do_stratify = y.nunique() > 1
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y if do_stratify else None
)

# ---------------- Preprocess ----------------
prep = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), feat_cols_cat) if feat_cols_cat else ("cat", "drop", []),
        ("num", "passthrough", feat_cols_num) if feat_cols_num else ("num", "drop", []),
    ]
)

# ---------------- (A) Logistic Regression (balanced OvR) ----------------
logit = LogisticRegression(
    multi_class="ovr",          # one-vs-rest helps minority classes
    class_weight="balanced",    # compensate imbalance
    max_iter=2000,
)
logit_pipe = Pipeline(steps=[("prep", prep), ("clf", logit)])
logit_pipe.fit(X_train, y_train)
y_pred_logit = logit_pipe.predict(X_test)
acc_logit = accuracy_score(y_test, y_pred_logit)
report_logit = classification_report(y_test, y_pred_logit, digits=3, zero_division=0)

print("[logit] y_test dist:", dict(y_test.value_counts(normalize=True).round(3)))
print("[logit] y_pred dist:", dict(pd.Series(y_pred_logit).value_counts(normalize=True).round(3)))

# Confusion matrix (logit)
cm_logit = confusion_matrix(y_test, y_pred_logit, labels=logit_pipe.classes_)
plt.figure(figsize=(6, 5))
im = plt.imshow(cm_logit, cmap="Blues")
plt.colorbar(im, fraction=0.046, pad=0.04)
plt.xticks(ticks=np.arange(len(logit_pipe.classes_)), labels=logit_pipe.classes_, rotation=45, ha="right")
plt.yticks(ticks=np.arange(len(logit_pipe.classes_)), labels=logit_pipe.classes_)
for i in range(cm_logit.shape[0]):
    for j in range(cm_logit.shape[1]):
        plt.text(j, i, str(cm_logit[i, j]), ha="center", va="center", fontsize=9)
plt.xlabel("Predicted"); plt.ylabel("Actual")
plt.title("Logistic Regression - Confusion Matrix")
plt.tight_layout()
cm_logit_path = os.path.join(FIGS, "fig_logit_confusion_matrix.png")
plt.savefig(cm_logit_path, dpi=180); plt.close()
print(f"[saved] {cm_logit_path}")

# ---------------- (B) Random Forest (balanced) ----------------
rf = RandomForestClassifier(
    n_estimators=500,
    max_depth=None,
    min_samples_leaf=20,        # a bit of regularization
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"     # stronger than balanced_subsample for minority classes
)
rf_pipe = Pipeline(steps=[("prep", prep), ("rf", rf)])
rf_pipe.fit(X_train, y_train)
y_pred_rf = rf_pipe.predict(X_test)
acc_rf = accuracy_score(y_test, y_pred_rf)
report_rf = classification_report(y_test, y_pred_rf, digits=3, zero_division=0)
cm_rf = confusion_matrix(y_test, y_pred_rf, labels=rf_pipe.classes_)

print("[rf] y_test dist:", dict(y_test.value_counts(normalize=True).round(3)))
print("[rf] y_pred dist:", dict(pd.Series(y_pred_rf).value_counts(normalize=True).round(3)))

# RF feature importances
def get_feature_names(preprocessor, cat_cols, num_cols):
    names = []
    if cat_cols:
        ohe = preprocessor.named_transformers_["cat"]
        names.extend(list(ohe.get_feature_names_out(cat_cols)))
    if num_cols:
        names.extend(num_cols)
    return names

feature_names = get_feature_names(rf_pipe.named_steps["prep"], feat_cols_cat, feat_cols_num)
importances = rf_pipe.named_steps["rf"].feature_importances_
imp_df = pd.DataFrame({"feature": feature_names, "importance": importances}).sort_values("importance", ascending=False)

plt.figure(figsize=(9, 6))
top = imp_df.head(20).iloc[::-1]
plt.barh(top["feature"], top["importance"])
plt.title("Random Forest - Top feature importances")
plt.xlabel("Importance")
plt.tight_layout()
fi_path = os.path.join(FIGS, "fig_rf_feature_importance.png")
plt.savefig(fi_path, dpi=180); plt.close()
print(f"[saved] {fi_path}")

# RF confusion matrix
plt.figure(figsize=(6, 5))
im = plt.imshow(cm_rf, cmap="Blues")
plt.colorbar(im, fraction=0.046, pad=0.04)
plt.xticks(ticks=np.arange(len(rf_pipe.classes_)), labels=rf_pipe.classes_, rotation=45, ha="right")
plt.yticks(ticks=np.arange(len(rf_pipe.classes_)), labels=rf_pipe.classes_)
for i in range(cm_rf.shape[0]):
    for j in range(cm_rf.shape[1]):
        plt.text(j, i, str(cm_rf[i, j]), ha="center", va="center", fontsize=9)
plt.xlabel("Predicted"); plt.ylabel("Actual")
plt.title("Random Forest - Confusion Matrix")
plt.tight_layout()
cm_rf_path = os.path.join(FIGS, "fig_rf_confusion_matrix.png")
plt.savefig(cm_rf_path, dpi=180); plt.close()
print(f"[saved] {cm_rf_path}")

# ---------------- Notes ----------------
notes_path = os.path.join(DOCS, "model_notes.txt")
with open(notes_path, "w", encoding="utf-8") as f:
    f.write("MODEL NOTES - Outcome prediction\n\n")
    f.write("Target classes: Death, Repatriated, Attrition" + (", Unknown\n\n" if INCLUDE_UNKNOWN_CLASS else "\n\n"))
    f.write(f"Train size: {len(X_train):,} | Test size: {len(X_test):,}\n\n")

    f.write("[Logistic Regression]\n")
    f.write(f"Accuracy: {acc_logit:.3f}\n")
    f.write("Classification report (test):\n")
    f.write(report_logit + "\n")

    f.write("[Random Forest]\n")
    f.write(f"Accuracy: {acc_rf:.3f}\n")
    f.write("Classification report (test):\n")
    f.write(report_rf + "\n")

# ---------------- Figure captions (dedup) ----------------
caps_path = os.path.join(DOCS, "figure_captions.txt")
add_lines = [
    "fig_logit_confusion_matrix.png - Logistic Regression: confusion matrix (actual vs predicted outcomes).",
    "fig_rf_feature_importance.png - Random Forest: top features associated with contract outcomes.",
    "fig_rf_confusion_matrix.png - Random Forest: confusion matrix (actual vs predicted outcomes).",
]
existing = set()
if os.path.exists(caps_path):
    with open(caps_path, "r", encoding="utf-8") as f:
        existing = {line.strip() for line in f if line.strip()}
with open(caps_path, "a", encoding="utf-8") as f:
    for line in add_lines:
        if line not in existing:
            f.write(line + "\n")

print(f"[saved] {notes_path}")
print(f"[updated] {caps_path}")
print("[done] Modeling complete.")
