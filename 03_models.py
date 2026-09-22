"""
Question-specific models for the revised VOC article.

Research question
-----------------
Among contracts with a clearly recorded Death or Repatriated ending, did the
probability of Death differ by occupational rank, and did rank differences change
over time?

This script estimates one explicit historical contrast and reports odds ratios, confidence intervals, and predicted
probabilities.

Primary model
-------------
Binary logit (binomial GLM): Death = 1, Repatriated = 0.
Predictors: rank, decade (linear, centred at 1700), rank x decade, region, and the
pre-existing high-rank indicator. Sea and Dutch Republic are reference categories.
HC1 heteroskedasticity-robust standard errors are reported.

Sensitivity model
-----------------
The same specification is fitted only to records with person_cluster_id. This
checks sensitivity to the 26.6% of records for which first-contract/person-level
linkage is unavailable. The model deliberately does not use first-contract status:
missing identifiers would otherwise be encoded as non-first contracts.

Interpretive limits
-------------------
This is an association model, not a causal or collapse-prediction model. Death and
repatriation are competing recorded endings, but contract duration/exposure is not
modelled here.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent if SCRIPT_DIR.name == "notebooks" else SCRIPT_DIR
DATA_CLEAN = BASE / "data_clean"
TABLES = BASE / "tables"
FIGURES = BASE / "figures"
DOCS = BASE / "docs"

for folder in (TABLES, FIGURES, DOCS):
    folder.mkdir(parents=True, exist_ok=True)

RANK_ORDER = ["Sea", "Military", "Ship", "Other", "Medical", "Trade"]
REFERENCE_REGION = "Dutch Republic"


def save_csv(df, filename):
    path = TABLES / filename
    df.to_csv(path, index=False)
    print(f"[saved] {path}")


def prepare_data(contracts):
    required = {
        "outcome_group_revised", "rank_parent", "region_label",
        "is_high_rank", "person_cluster_id"
    }
    missing = required - set(contracts.columns)
    if missing:
        raise RuntimeError(f"Missing required columns: {sorted(missing)}")

    df = contracts[
        contracts["outcome_group_revised"].isin(["Death", "Repatriated"])
    ].copy()
    df["death"] = (df["outcome_group_revised"] == "Death").astype(int)

    if "decade" not in df.columns:
        if "contract_start_year" not in df.columns:
            raise RuntimeError("Need decade or contract_start_year.")
        df["decade"] = (
            pd.to_numeric(df["contract_start_year"], errors="coerce") // 10 * 10
        )

    df["decade"] = pd.to_numeric(df["decade"], errors="coerce")
    df["decade_since_1700"] = (df["decade"] - 1700) / 10
    df["rank_parent"] = df["rank_parent"].fillna("Unknown").astype(str)
    df["region_label"] = df["region_label"].fillna("Unknown").astype(str)
    df["is_high_rank"] = pd.to_numeric(df["is_high_rank"], errors="coerce")
    df["has_person_cluster_id"] = df["person_cluster_id"].notna()

    return df.dropna(
        subset=["death", "decade", "decade_since_1700", "is_high_rank"]
    )


def fit_model(df, model_name):
    # Linear decade terms make each interaction directly interpretable as the
    # change in a rank's death odds per decade. Descriptive plots should still be
    # checked for non-linearity.
    formula = (
        "death ~ C(rank_parent, Treatment(reference='Sea')) * decade_since_1700 "
        "+ C(region_label, Treatment(reference='Dutch Republic')) + is_high_rank"
    )
    fitted = smf.glm(
        formula=formula,
        data=df,
        family=sm.families.Binomial(),
    ).fit(cov_type="HC1")

    ci = fitted.conf_int()
    results = pd.DataFrame({
        "term": fitted.params.index,
        "log_odds": fitted.params.values,
        "std_error_robust": fitted.bse.values,
        "odds_ratio": np.exp(fitted.params.values),
        "ci_low_95": np.exp(ci[0].values),
        "ci_high_95": np.exp(ci[1].values),
        "p_value": fitted.pvalues.values,
        "model": model_name,
    })
    results["n_records"] = int(fitted.nobs)
    save_csv(results, f"question_specific_logit_{model_name}_odds_ratios.csv")

    fit = pd.DataFrame([{
        "model": model_name,
        "n_records": int(fitted.nobs),
        "n_deaths": int(df["death"].sum()),
        "n_repatriated": int((1 - df["death"]).sum()),
        "death_share": float(df["death"].mean()),
        "aic": float(fitted.aic),
        "deviance": float(fitted.deviance),
        "pseudo_r2_cs": float(fitted.pseudo_rsquared(kind="cs")),
    }])
    save_csv(fit, f"question_specific_logit_{model_name}_fit.csv")
    return fitted


def prediction_grid(fitted, observed_ranks, model_name):
    ranks = [r for r in RANK_ORDER if r in observed_ranks]
    if "Unknown" in observed_ranks:
        ranks.append("Unknown")
    grid = pd.MultiIndex.from_product(
        [ranks, range(1700, 1790, 10)], names=["rank_parent", "decade"]
    ).to_frame(index=False)
    grid["decade_since_1700"] = (grid["decade"] - 1700) / 10
    grid["region_label"] = REFERENCE_REGION
    # This reference-profile prediction isolates rank/time coefficients. It is not
    # a population-standardised estimate.
    grid["is_high_rank"] = 0.0

    pred = fitted.get_prediction(grid).summary_frame(alpha=0.05)
    grid["predicted_death_probability"] = pred["mean"].values
    grid["ci_low_95"] = pred["mean_ci_lower"].values
    grid["ci_high_95"] = pred["mean_ci_upper"].values
    grid["model"] = model_name
    grid["prediction_profile"] = "Dutch Republic; is_high_rank=0"
    save_csv(grid, f"question_specific_logit_{model_name}_predicted_probabilities.csv")
    return grid


def plot_predictions(grid):
    fig, ax = plt.subplots(figsize=(10, 6))
    for rank, part in grid.groupby("rank_parent", sort=False):
        part = part.sort_values("decade")
        #ax.plot(part["decade"], part["predicted_death_probability"], marker="o", label=rank)
        ax.plot(
            part["decade"].to_numpy(),
            part["predicted_death_probability"].to_numpy(),
            marker="o",
            label=rank
        )
        ax.fill_between(part["decade"], part["ci_low_95"], part["ci_high_95"], alpha=0.10)
    ax.set(
        xlabel="Contract-start decade",
        ylabel="Predicted probability of Death\n(among Death or Repatriated endings)",
        title="Rank-specific death probabilities from the interpretable logit model",
        ylim=(0, 1),
    )
    ax.legend(title="Rank", bbox_to_anchor=(1.02, 0.5), loc="center left", frameon=False)
    fig.tight_layout()
    path = FIGURES / "fig_question_specific_rank_death_probabilities.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {path}")


def write_notes(primary, sensitivity, primary_grid):
    path = DOCS / "question_specific_model_notes.txt"
    military_terms = primary.params[
        primary.params.index.str.contains("Military", regex=False)
    ]
    with path.open("w", encoding="utf-8") as f:
        f.write("QUESTION-SPECIFIC MODEL NOTES\n\n")
        f.write("Estimand\n")
        f.write("- Probability that a clearly recorded Death/Repatriated ending was Death.\n")
        f.write("- Death is coded 1; Repatriated is coded 0.\n")
        f.write("- Chamber, Unknown/unclear, Other, and Irregular exit are excluded.\n\n")
        f.write("Specification\n")
        f.write("- Binary logit with rank, linear decade, rank x decade, region, and high-rank status.\n")
        f.write("- Reference rank: Sea. Reference region: Dutch Republic.\n")
        f.write("- HC1 robust standard errors and 95% confidence intervals.\n")
        f.write("- Sensitivity model includes only records with person_cluster_id.\n\n")
        f.write(f"Primary model records: {int(primary.nobs):,}\n")
        f.write(f"Identifiable-only records: {int(sensitivity.nobs):,}\n")
        f.write(f"Primary military-related coefficients estimated: {len(military_terms)}\n\n")
        f.write("Interpretation rules\n")
        f.write("- Rank main effects compare ranks in 1700.\n")
        f.write("- decade_since_1700 is the Sea-rank change in death odds per decade.\n")
        f.write("- Rank x decade terms show how each rank's time trend differs from Sea.\n")
        f.write("- Odds ratios above 1 indicate higher odds; below 1 indicate lower odds.\n")
        f.write("- Predicted probabilities describe a Dutch, non-high-rank reference profile.\n\n")
        f.write("Limits\n")
        f.write("- The model tests associations in contract outcomes, not VOC collapse.\n")
        f.write("- It does not model contract duration, exposure time, active workforce stock, or labor demand.\n")
        f.write("- Repeated contracts may belong to the same person; HC1 errors do not solve within-person dependence.\n")
        f.write("- A competing-risks survival model should be the next step when durations are validated.\n")
    print(f"[saved] {path}")


def main():
    input_path = DATA_CLEAN / "contracts_clean.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Missing {input_path}. Run 01_cleaning.py first. "
            "The repository does not distribute the cleaned data."
        )
    contracts = pd.read_csv(input_path, low_memory=False)
    df = prepare_data(contracts)

    primary = fit_model(df, "all_records")
    primary_grid = prediction_grid(primary, set(df["rank_parent"]), "all_records")

    identifiable = df[df["has_person_cluster_id"]].copy()
    sensitivity = fit_model(identifiable, "identifiable_only")
    prediction_grid(sensitivity, set(identifiable["rank_parent"]), "identifiable_only")

    plot_predictions(primary_grid)
    write_notes(primary, sensitivity, primary_grid)
    print("[done] Question-specific models complete.")


if __name__ == "__main__":
    main()
