"""
03_models.py
Purpose: build a simple predictive model (Random Forest) for contract outcomes,
report basic performance, and save modeling figures.

Target:
  outcome_group with classes: Death / Repatriated / Attrition / Unknown

Features (example, easy to explain):
  - region_label (one-hot)
  - rank_parent (one-hot)
  - is_high_rank (0/1)
  - decade (numeric)

Outputs:
  - figures/fig_rf_feature_importance.png
  - figures/fig_rf_confusion_matrix.png
  - docs/model_notes.txt (accuracy, class report)
  - docs/figure_captions.txt (appended)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
import seaborn as sns

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_CLEAN = os.path.join(BASE, "data_clean")
FIGURES    = os.path.join(BASE, "figures")
DOCS       = os.path.join(BASE, "docs")
os.makedirs(FIGURES, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

contracts = pd.read_csv(os.path.join(DATA_CLEAN, "contracts_clean.csv"), low_memory=False)

# ---------- Build modeling dataset ----------
df = contracts.copy()

# Keep only rows with a valid target
df = df[df["outcome_group"].isin(["Death","Repatriated","Attrition","Unknown"])].copy()

# Simple feature set (transparent and reproducible)
feat_cols_cat = ["region_label", "rank_parent"]
feat_cols_num = ["is_high_rank", "decade"]

# Drop rows with missing in required columns
needed_cols = feat_cols_cat + feat_cols_num + ["outcome_group"]
df = df.dropna(subset=needed_cols)

X = df[feat_cols_cat + feat_cols_num].copy()
y = df["outcome_group"].copy()

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# Encoder + model
preprocess = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), feat_cols_cat),
        ("num", "passthrough", feat_cols_num),
    ]
)

rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced_subsample"
)

pipe = Pipeline(steps=[("prep", preprocess), ("rf", rf)])
pipe.fit(X_train, y_train)

# ---------- Evaluation ----------
y_pred = pipe.predict(X_test)
report = classification_report(y_test, y_pred, digits=3)
cm = confusion_matrix(y_test, y_pred, labels=pipe.classes_)

# Save confusion matrix plot
plt.figure(figsize=(6,5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=pipe.classes_, yticklabels=pipe.classes_)
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Random Forest - Confusion Matrix")
cm_path = os.path.join(FIGURES, "fig_rf_confusion_matrix.png")
plt.tight_layout(); plt.savefig(cm_path, dpi=180); plt.close()
print(f"[saved] {cm_path}")

# ---------- Feature importances ----------
# Get feature names from the OneHotEncoder + numeric passthrough
ohe = pipe.named_steps["prep"].named_transformers_["cat"]
cat_names = ohe.get_feature_names_out(feat_cols_cat)
feature_names = list(cat_names) + feat_cols_num

importances = pipe.named_steps["rf"].feature_importances_
imp_df = pd.DataFrame({"feature": feature_names, "importance": importances}).sort_values("importance", ascending=False)

plt.figure(figsize=(8,6))
top = imp_df.head(20).iloc[::-1]  # top 20, flipped for horizontal bars
plt.barh(top["feature"], top["importance"])
plt.title("Random Forest - Top feature importances")
plt.xlabel("Importance")
plt.tight_layout()
fi_path = os.path.join(FIGURES, "fig_rf_feature_importance.png")
plt.savefig(fi_path, dpi=180); plt.close()
print(f"[saved] {fi_path}")

# ---------- Model notes & captions ----------
notes_path = os.path.join(DOCS, "model_notes.txt")
with open(notes_path, "w", encoding="utf-8") as f:
    f.write("MODEL NOTES - Random Forest for outcome_group\n\n")
    f.write("Target classes: Death, Repatriated, Attrition, Unknown\n")
    f.write(f"Train size: {len(X_train):,}  |  Test size: {len(X_test):,}\n\n")
    f.write("Classification report (test):\n")
    f.write(report)
print(f"[saved] {notes_path}")

caps = os.path.join(DOCS, "figure_captions.txt")
with open(caps, "a", encoding="utf-8") as f:  # append to the captions written by 02_descriptives.py
    f.write("fig_rf_feature_importance.png - Random Forest: top features associated with contract outcomes.\n")
    f.write("fig_rf_confusion_matrix.png - Random Forest: confusion matrix (actual vs predicted outcomes).\n")
print(f"[updated] {caps}")

print("[done] Modeling complete.")
