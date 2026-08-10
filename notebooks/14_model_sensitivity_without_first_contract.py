"""
14_model_sensitivity_without_first_contract.py

Sensitivity model for the revised VOC article analysis.

Purpose
- Repeats the revised outcome prediction task from 03_models.py.
- Excludes first-contract status from the feature set.
- Checks whether rank, region, decade, Dutch/non-Dutch status, and high-rank status
  still help separate revised outcome groups when first-contract status is removed.

Target
- outcome_group_revised, with classes:
  * Death
  * Repatriated
  * Chamber
  * Unknown / unclear
  * Other
  * Irregular exit

Features used
- Categorical:
  * region_label
  * rank_parent

- Numeric:
  * decade
  * is_high_rank
  * is_dutch

Important notes
- This is a sensitivity check.
- First-contract status is deliberately excluded because it is a derived workforce-entry variable.
- These models are diagnostic and descriptive. They should not be interpreted as causal models.
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
TARGET_CLASSES = [
    "Death",
    "Repatriated",
    "Chamber",
    "Unknown / unclear",
    "Other",
    "Irregular exit",
]

DROP_UNKNOWN_UNCLEAR = False


# ---------------- Paths ----------------
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_C = os.path.join(BASE, "data_clean")
TABLES = os.path.join(BASE, "tables")
FIGS = os.path.join(BASE, "figures")
DOCS = os.path.join(BASE, "docs")

for folder in [TABLES, FIGS, DOCS]:
    os.makedirs(folder, exist_ok=True)


# ---------------- Helpers ----------------
def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f"[saved] {path}")


def append_caption_once(path, line):
    existing = set()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = {x.strip() for x in f.readlines()}

    if line.strip() not in existing:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line.strip() + "\n")


def make_one_hot_encoder():
    """
    Create a OneHotEncoder that works across different scikit-learn versions.
    """
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def plot_confusion_matrix(cm, labels, title, output_path):
    fig_size = max(6, len(labels) * 1.2)
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))

    im = ax.imshow(cm)

    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)

    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"[saved] {output_path}")


def get_feature_names(preprocessor, cat_cols, num_cols):
    names = []

    if cat_cols:
        encoder = preprocessor.named_transformers_["cat"]
        names.extend(encoder.get_feature_names_out(cat_cols).tolist())

    names.extend(num_cols)

    return names


# ---------------- Load ----------------
csv_path = os.path.join(DATA_C, "contracts_clean.csv")

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Missing {csv_path}. Run 01_cleaning.py first.")

contracts = pd.read_csv(csv_path, low_memory=False)

# Create decade if it was not saved by the cleaning script.
if "decade" not in contracts.columns:
    if "contract_start_year" in contracts.columns:
        contracts["decade"] = (
            pd.to_numeric(contracts["contract_start_year"], errors="coerce") // 10 * 10
        )
        print("[info] Created decade from contract_start_year.")
    elif "date_begin_contract" in contracts.columns:
        contracts["date_begin_contract"] = pd.to_datetime(
            contracts["date_begin_contract"],
            errors="coerce"
        )
        contracts["decade"] = contracts["date_begin_contract"].dt.year // 10 * 10
        print("[info] Created decade from date_begin_contract.")
    else:
        print("[warn] No decade, contract_start_year, or date_begin_contract column found.")


# ---------------- Build modelling set ----------------
if "outcome_group_revised" in contracts.columns:
    OUTCOME_COL = "outcome_group_revised"
elif "outcome_group" in contracts.columns:
    OUTCOME_COL = "outcome_group"
else:
    raise RuntimeError("contracts_clean.csv lacks an outcome grouping column.")

print(f"[info] Using outcome column: {OUTCOME_COL}")
print("[info] Excluding first-contract status from this sensitivity model.")

df = contracts.copy()

df["model_outcome"] = df[OUTCOME_COL].astype(str)

valid_targets = TARGET_CLASSES.copy()

if DROP_UNKNOWN_UNCLEAR:
    valid_targets = [x for x in valid_targets if x != "Unknown / unclear"]

df = df[df["model_outcome"].isin(valid_targets)].copy()

feat_cols_cat = [c for c in ["region_label", "rank_parent"] if c in df.columns]
feat_cols_num = [
    c for c in [
        "decade",
        "is_high_rank",
        "is_dutch",
    ]
    if c in df.columns
]

if not feat_cols_cat and not feat_cols_num:
    raise RuntimeError("No usable feature columns found.")

for c in feat_cols_cat:
    df[c] = df[c].fillna("Unknown").astype(str)

for c in feat_cols_num:
    df[c] = pd.to_numeric(df[c], errors="coerce")

    if df[c].isna().all():
        df[c] = df[c].fillna(0)
    else:
        df[c] = df[c].fillna(df[c].median())

df = df.dropna(subset=["model_outcome"])
df = df.dropna(subset=feat_cols_cat + feat_cols_num)

if df.empty:
    raise RuntimeError(
        "0 rows for modelling after preprocessing. "
        "Check that revised outcomes and feature columns exist."
    )

X = df[feat_cols_cat + feat_cols_num].copy()
y = df["model_outcome"].copy()

class_distribution = (
    y.value_counts()
    .rename_axis("outcome_group_revised")
    .reset_index(name="n")
)

class_distribution["share_pct"] = (
    class_distribution["n"] / class_distribution["n"].sum() * 100
).round(2)

save_csv(
    class_distribution,
    os.path.join(TABLES, "model_sensitivity_no_first_contract_class_distribution.csv")
)


# ---------------- Train/test split ----------------
class_counts = y.value_counts()
do_stratify = y.nunique() > 1 and class_counts.min() >= 2

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y if do_stratify else None
)


# ---------------- Preprocess ----------------
prep = ColumnTransformer(
    transformers=[
        ("cat", make_one_hot_encoder(), feat_cols_cat) if feat_cols_cat else ("cat", "drop", []),
        ("num", "passthrough", feat_cols_num) if feat_cols_num else ("num", "drop", []),
    ]
)


# ---------------- Logistic Regression ----------------
logit = LogisticRegression(
    class_weight="balanced",
    max_iter=1000,
)

logit_pipe = Pipeline(steps=[("prep", prep), ("clf", logit)])
logit_pipe.fit(X_train, y_train)

y_pred_logit = logit_pipe.predict(X_test)
acc_logit = accuracy_score(y_test, y_pred_logit)

report_logit = classification_report(
    y_test,
    y_pred_logit,
    digits=3,
    zero_division=0,
)

report_logit_df = pd.DataFrame(
    classification_report(
        y_test,
        y_pred_logit,
        digits=3,
        zero_division=0,
        output_dict=True,
    )
).transpose().reset_index().rename(columns={"index": "class_or_average"})

save_csv(
    report_logit_df,
    os.path.join(TABLES, "model_sensitivity_no_first_contract_logit_report.csv")
)

print("[logit sensitivity] y_test dist:", dict(y_test.value_counts(normalize=True).round(3)))
print("[logit sensitivity] y_pred dist:", dict(pd.Series(y_pred_logit).value_counts(normalize=True).round(3)))

cm_logit = confusion_matrix(y_test, y_pred_logit, labels=logit_pipe.classes_)

cm_logit_df = pd.DataFrame(
    cm_logit,
    index=[f"actual_{x}" for x in logit_pipe.classes_],
    columns=[f"predicted_{x}" for x in logit_pipe.classes_],
)

save_csv(
    cm_logit_df.reset_index().rename(columns={"index": "actual"}),
    os.path.join(TABLES, "model_sensitivity_no_first_contract_logit_confusion_matrix.csv")
)

cm_logit_path = os.path.join(
    FIGS,
    "fig_logit_confusion_matrix_sensitivity_no_first_contract.png"
)

plot_confusion_matrix(
    cm_logit,
    logit_pipe.classes_,
    "Logistic Regression sensitivity: no first-contract feature",
    cm_logit_path,
)


# ---------------- Random Forest ----------------
rf = RandomForestClassifier(
    n_estimators=500,
    max_depth=None,
    min_samples_leaf=20,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced_subsample",
)

rf_pipe = Pipeline(steps=[("prep", prep), ("rf", rf)])
rf_pipe.fit(X_train, y_train)

y_pred_rf = rf_pipe.predict(X_test)
acc_rf = accuracy_score(y_test, y_pred_rf)

report_rf = classification_report(
    y_test,
    y_pred_rf,
    digits=3,
    zero_division=0,
)

report_rf_df = pd.DataFrame(
    classification_report(
        y_test,
        y_pred_rf,
        digits=3,
        zero_division=0,
        output_dict=True,
    )
).transpose().reset_index().rename(columns={"index": "class_or_average"})

save_csv(
    report_rf_df,
    os.path.join(TABLES, "model_sensitivity_no_first_contract_rf_report.csv")
)

cm_rf = confusion_matrix(y_test, y_pred_rf, labels=rf_pipe.classes_)

cm_rf_df = pd.DataFrame(
    cm_rf,
    index=[f"actual_{x}" for x in rf_pipe.classes_],
    columns=[f"predicted_{x}" for x in rf_pipe.classes_],
)

save_csv(
    cm_rf_df.reset_index().rename(columns={"index": "actual"}),
    os.path.join(TABLES, "model_sensitivity_no_first_contract_rf_confusion_matrix.csv")
)

print("[rf sensitivity] y_test dist:", dict(y_test.value_counts(normalize=True).round(3)))
print("[rf sensitivity] y_pred dist:", dict(pd.Series(y_pred_rf).value_counts(normalize=True).round(3)))


# ---------------- Random Forest feature importances ----------------
feature_names = get_feature_names(
    rf_pipe.named_steps["prep"],
    feat_cols_cat,
    feat_cols_num,
)

importances = rf_pipe.named_steps["rf"].feature_importances_

fi = (
    pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importances,
        }
    )
    .sort_values("importance", ascending=False)
    .reset_index(drop=True)
)

save_csv(
    fi,
    os.path.join(TABLES, "model_sensitivity_no_first_contract_rf_feature_importances.csv")
)

top = fi.head(20).copy()

fig, ax = plt.subplots(figsize=(9, 7))
ax.barh(top["feature"].iloc[::-1], top["importance"].iloc[::-1])
ax.set_xlabel("Importance")
ax.set_title("Random Forest sensitivity: top feature importances")
fig.tight_layout()

fi_path = os.path.join(
    FIGS,
    "fig_rf_feature_importance_sensitivity_no_first_contract.png"
)

fig.savefig(fi_path, dpi=180, bbox_inches="tight")
plt.close(fig)

print(f"[saved] {fi_path}")


# ---------------- Random Forest confusion matrix ----------------
cm_rf_path = os.path.join(
    FIGS,
    "fig_rf_confusion_matrix_sensitivity_no_first_contract.png"
)

plot_confusion_matrix(
    cm_rf,
    rf_pipe.classes_,
    "Random Forest sensitivity: no first-contract feature",
    cm_rf_path,
)


# ---------------- Notes ----------------
notes_path = os.path.join(DOCS, "model_sensitivity_no_first_contract_notes.txt")

with open(notes_path, "w", encoding="utf-8") as f:
    f.write("MODEL NOTES - Sensitivity model without first-contract status\n\n")

    f.write("Target column used:\n")
    f.write(f"- {OUTCOME_COL}\n\n")

    f.write("Target classes included:\n")
    for cls in valid_targets:
        f.write(f"- {cls}\n")
    f.write("\n")

    f.write("Feature columns used:\n")
    for col in feat_cols_cat + feat_cols_num:
        f.write(f"- {col}\n")
    f.write("\n")

    f.write("Feature deliberately excluded:\n")
    f.write("- first-contract status\n\n")

    f.write(f"Rows used for modelling: {len(df):,}\n")
    f.write(f"Train size: {len(X_train):,}\n")
    f.write(f"Test size: {len(X_test):,}\n\n")

    f.write("Class distribution:\n")
    f.write(class_distribution.to_string(index=False))
    f.write("\n\n")

    f.write(f"Logistic Regression accuracy: {acc_logit:.3f}\n")
    f.write(report_logit)
    f.write("\n\n")

    f.write(f"Random Forest accuracy: {acc_rf:.3f}\n")
    f.write(report_rf)
    f.write("\n\n")

    f.write("Interpretation note:\n")
    f.write(
        "This sensitivity model excludes first-contract status. "
        "It checks whether rank, region, decade, Dutch/non-Dutch status, and high-rank status "
        "still help separate revised outcome groups without the derived workforce-entry variable. "
        "The model remains diagnostic and descriptive, not causal.\n"
    )

print(f"[saved] {notes_path}")


# ---------------- Revised figure captions ----------------
caps_path = os.path.join(DOCS, "figure_captions_revised.txt")

append_caption_once(
    caps_path,
    "fig_logit_confusion_matrix_sensitivity_no_first_contract.png - Logistic Regression sensitivity confusion matrix without first-contract status."
)

append_caption_once(
    caps_path,
    "fig_rf_feature_importance_sensitivity_no_first_contract.png - Random Forest sensitivity feature importances without first-contract status."
)

append_caption_once(
    caps_path,
    "fig_rf_confusion_matrix_sensitivity_no_first_contract.png - Random Forest sensitivity confusion matrix without first-contract status."
)

print(f"[updated] {caps_path}")
print("[done] Sensitivity model without first-contract status complete.")