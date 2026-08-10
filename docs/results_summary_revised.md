# Revised VOC analysis summary

This document summarizes the current revised analysis after updating the outcome grouping, first-contract logic, descriptive outputs, and modelling scripts.

## 1. Main methodological updates

The analysis now uses a revised outcome grouping instead of the earlier broad outcome categories.

The revised outcome groups are:

- Death
- Repatriated
- Chamber
- Unknown / unclear
- Other
- Irregular exit

The old "Attrition" category was removed because it mixed different types of contract endings that should not be interpreted in the same way.

First contracts are now calculated on the full dataset before filtering to the 1700s-1780s. This makes the first-contract variable methodologically cleaner, because it avoids incorrectly treating a person's first observed contract inside the filtered period as their first contract overall.

First contracts are treated as a proxy for new workforce entry, not as a direct hiring rate.

## 2. Data scope

The main analysis still uses the 1700s-1780s period.

The filtered analysis dataset contains:

- 676,934 contract records

The revised outcome distribution is:

| Outcome group | Count | Share |
|---|---:|---:|
| Death | 351,404 | 51.91% |
| Repatriated | 203,890 | 30.12% |
| Chamber | 43,231 | 6.39% |
| Unknown / unclear | 41,686 | 6.16% |
| Other | 19,327 | 2.86% |
| Irregular exit | 17,396 | 2.57% |

## 3. Missing person identifiers

A methodological issue is that many records have missing `person_cluster_id`.

In the 1700s-1780s subset:

- 179,991 records have missing `person_cluster_id`
- this is 26.59% of the filtered dataset

Because first contracts can only be identified reliably for records with a person identifier, I checked both:

- an all-records benchmark
- an identifiable-only sensitivity benchmark

This makes the first-contract interpretation more cautious.

## 4. First contracts versus exits by rank

The revised analysis compares first-contract shares with major exit outcome shares by rank.

The most important pattern is not a simple overall shortage of new workforce entry. Instead, the clearer result is a rank-specific mismatch.

Military ranks are consistently overrepresented among Death outcomes compared with their first-contract share.

In the all-records benchmark:

| Rank | First-contract share | Death share | Repatriated share | Death + Repatriated share |
|---|---:|---:|---:|---:|
| Sea | 53.42% | 44.86% | 69.09% | 53.75% |
| Military | 34.56% | 43.24% | 16.45% | 33.40% |

This means:

- Military ranks have a lower first-contract share than death share.
- Sea ranks have a higher first-contract share than death share, but a much higher repatriated share.
- Repatriation follows a different rank pattern than mortality.
- Combining Death and Repatriated makes the overall pattern less straightforward.

The stronger interpretation is therefore that mortality and repatriation should be discussed separately, rather than assuming they both indicate the same workforce-pressure mechanism.

## 5. Descriptive outputs

The updated descriptive script is:

- `02_descriptives.py`

The main revised descriptive outputs include:

- `tables/trend_by_decade_revised.csv`
- `tables/first_contracts_vs_exits_by_rank_revised.csv`
- `tables/outcome_rates_and_first_contract_share_by_decade_rank_revised.csv`
- `figures/fig_trend_over_time_revised.png`
- `figures/fig_death_rate_and_first_contract_rate_by_decade.png`
- `figures/fig_first_contracts_vs_exits_by_rank_revised.png`
- `figures/fig_outcome_rates_and_first_contract_share_by_rank_revised.png`
- `docs/figure_captions_revised.txt`

## 6. Revised modelling

The modelling script was updated to use:

- `outcome_group_revised`
- `is_first_contract_true`

The main revised model script is:

- `03_models.py`

The sensitivity model without first-contract status is:

- `14_model_sensitivity_without_first_contract.py`

The model comparison script is:

- `15_model_comparison_summary.py`

The model comparison shows that the models have modest predictive performance overall.

| Model | Feature set | Accuracy | Macro F1 | Weighted F1 |
|---|---|---:|---:|---:|
| Logistic Regression | with first-contract status | 0.299 | 0.193 | 0.323 |
| Random Forest | with first-contract status | 0.328 | 0.250 | 0.368 |
| Logistic Regression | without first-contract status | 0.283 | 0.160 | 0.296 |
| Random Forest | without first-contract status | 0.340 | 0.236 | 0.369 |

The Random Forest model with first-contract status identified the most important features as:

- decade
- first_contract_for_model
- rank_parent_Military
- rank_parent_Sea
- is_high_rank

The sensitivity model without first-contract status still identified:

- decade
- rank_parent_Military
- rank_parent_Sea
- is_high_rank
- is_dutch

This suggests that temporal structure and rank remain relevant, even when first-contract status is excluded.

However, the models do not predict the revised outcome groups strongly enough to become the main article evidence. They should be treated as diagnostic and supplementary.

## 7. Current interpretation

The revised analysis supports a more careful article framing.

The original broad claim that the VOC simply did not recruit enough overall is probably too strong.

The stronger and better-supported claim is:

- VOC workforce outcomes were structured by rank and time.
- Military ranks were especially exposed to mortality.
- Sea ranks had a different exit pattern, especially through repatriation.
- First-contract patterns do not map neatly onto all exit types.
- Mortality and repatriation should be interpreted separately because they reflect different workforce dynamics.

The main article argument should therefore focus on a rank-specific mismatch between new workforce entry and exit patterns, especially the overrepresentation of Military ranks among Death outcomes.

## 8. Current status

The revised cleaning, descriptive, modelling, sensitivity, and comparison scripts now run successfully.

The active scripts no longer use the old "Attrition" category or old "death vs recruitment" wording.

The next step is to decide which revised tables and figures should be included in the article draft, and which should stay as supplementary diagnostics.