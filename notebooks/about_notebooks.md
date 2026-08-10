# Scripts Documentation

This file documents the main Python scripts used for the VOC workforce analysis.

The repository contains two related workflows:

1. The original course project for *Introduction to Digital Humanities & Social Analytics*.
2. The revised article-extension analysis continued after the DHBenelux poster presentation.

The original course project was completed by Group 2. The revised article-extension analysis was continued by Feruza Bakhtiyorova, with feedback from Lorella Viola.

## 1. Original course workflow

The original course workflow focused on the VOC workforce between the 1700s and 1780s, especially relationships between worker origins, ranks, and contract outcomes.

The original workflow used three main scripts:

1. `01_cleaning.py`
2. `02_descriptives.py`
3. `03_models.py`

Some older documentation and figures may refer to broader outcome categories and earlier “death vs recruitment” wording. These belong to the original course version and have since been revised for the article-extension analysis.

## 2. Revised article-extension workflow

The revised analysis updates the methodology, interpretation, descriptive analysis, and modelling diagnostics.

The main methodological updates are:

- First contracts are calculated on the full dataset before filtering to the 1700s-1780s.
- First contracts are treated as a proxy for new workforce entry, not as a direct hiring rate.
- The earlier broad outcome grouping has been replaced with revised outcome groups:
  - Death
  - Repatriated
  - Chamber
  - Unknown / unclear
  - Other
  - Irregular exit
- Death and Repatriated are analyzed both separately and together.
- Missing `person_cluster_id` values are treated as a methodological limitation.
- Modelling results are treated as diagnostic and supplementary, not as central evidence.

## 3. Revised scripts

### `01_cleaning.py`

Prepares the cleaned dataset for the revised analysis.

Main tasks:

- Loads the raw VOC contracts dataset.
- Creates first-contract indicators on the full dataset before filtering.
- Filters the main analysis period to the 1700s-1780s.
- Merges place and rank information.
- Creates rank, region, decade, and other analysis variables.
- Creates the revised outcome grouping.

Main outputs:

- `data_clean/contracts_filtered.csv`
- `data_clean/contracts_clean.csv`
- `tables/outcome_counts_revised.csv`
- `tables/reason_end_contract_mapping_check_revised.csv`
- `docs/methods_notes.txt`

### `02_descriptives.py`

Creates revised descriptive tables and figures.

Main tasks:

- Builds revised crosstabs for region, rank, and outcome groups.
- Creates decade-level trend tables.
- Compares first-contract shares with Death, Repatriated, and Death + Repatriated shares by rank.
- Creates revised figures using first-contract terminology.

Main outputs:

- `tables/region_by_rank_parent_count.csv`
- `tables/region_by_rank_parent_pct.csv`
- `tables/rank_parent_by_outcome_revised_count.csv`
- `tables/rank_parent_by_outcome_revised_pct.csv`
- `tables/region_by_outcome_group_revised_count.csv`
- `tables/region_by_outcome_group_revised_pct.csv`
- `tables/trend_by_decade_revised.csv`
- `tables/first_contracts_vs_exits_by_rank_revised.csv`
- `tables/outcome_rates_and_first_contract_share_by_decade_rank_revised.csv`
- `figures/fig_region_by_rank_parent.png`
- `figures/fig_rank_parent_by_outcome_revised.png`
- `figures/fig_trend_over_time_revised.png`
- `figures/fig_death_rate_and_first_contract_rate_by_decade.png`
- `figures/fig_first_contracts_vs_exits_by_rank_revised.png`
- `figures/fig_outcome_rates_and_first_contract_share_by_rank_revised.png`
- `docs/figure_captions_revised.txt`

The script also generates decade-specific first-contract versus exit figures and tables for the 1700s through 1780s.

### `03_models.py`

Runs revised diagnostic models using the revised outcome grouping.

Main tasks:

- Uses `outcome_group_revised` as the target.
- Uses `is_first_contract_true` as the corrected first-contract feature.
- Creates `decade` from `contract_start_year` if needed.
- Trains Logistic Regression and Random Forest models.
- Saves classification reports, confusion matrices, feature importances, and notes.

Main outputs:

- `tables/model_class_distribution_revised.csv`
- `tables/model_logit_classification_report_revised.csv`
- `tables/model_logit_confusion_matrix_revised.csv`
- `tables/model_rf_classification_report_revised.csv`
- `tables/model_rf_confusion_matrix_revised.csv`
- `tables/model_rf_feature_importances_revised.csv`
- `figures/fig_logit_confusion_matrix_revised.png`
- `figures/fig_rf_confusion_matrix_revised.png`
- `figures/fig_rf_feature_importance_revised.png`
- `docs/model_notes_revised.txt`

### `13_revised_outcome_first_contract_benchmark.py`

Creates benchmark tables comparing first-contract shares with major exit shares by rank.

Main comparisons:

- First-contract share vs Death share
- First-contract share vs Repatriated share
- First-contract share vs Death + Repatriated share

Main outputs:

- `tables/v3_reason_end_contract_mapping_check_1700_1780.csv`
- `tables/v3_missing_person_cluster_by_disambiguation_1700_1780.csv`
- `tables/v3_missing_person_cluster_by_rank_1700_1780.csv`
- `tables/v3_rank_first_contract_exit_benchmark_all_records_1700_1780.csv`
- `tables/v3_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv`
- `tables/v3_decade_rank_first_contract_exit_benchmark_all_records_1700_1780.csv`
- `tables/v3_decade_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv`

This script helped refine the interpretation from a broad new-workforce-entry claim to a more specific first-contract versus exit-pattern comparison.

### `14_model_sensitivity_without_first_contract.py`

Runs a sensitivity model without first-contract status.

Purpose:

- Checks whether rank, region, decade, Dutch/non-Dutch status, and high-rank status still help separate revised outcome groups when the derived first-contract variable is removed.

Main outputs:

- `tables/model_sensitivity_no_first_contract_class_distribution.csv`
- `tables/model_sensitivity_no_first_contract_logit_report.csv`
- `tables/model_sensitivity_no_first_contract_logit_confusion_matrix.csv`
- `tables/model_sensitivity_no_first_contract_rf_report.csv`
- `tables/model_sensitivity_no_first_contract_rf_confusion_matrix.csv`
- `tables/model_sensitivity_no_first_contract_rf_feature_importances.csv`
- `figures/fig_logit_confusion_matrix_sensitivity_no_first_contract.png`
- `figures/fig_rf_confusion_matrix_sensitivity_no_first_contract.png`
- `figures/fig_rf_feature_importance_sensitivity_no_first_contract.png`
- `docs/model_sensitivity_no_first_contract_notes.txt`

### `15_model_comparison_summary.py`

Creates a compact comparison of the main revised models and sensitivity models.

Main outputs:

- `tables/model_comparison_summary_revised.csv`
- `docs/model_comparison_summary_revised.txt`

## 4. Revised execution order

To rerun the revised analysis from the repository root:

1. `python 01_cleaning.py`
2. `python 02_descriptives.py`
3. `python 03_models.py`
4. `python 14_model_sensitivity_without_first_contract.py`
5. `python 15_model_comparison_summary.py`

## 5. Most useful revised summary files

For a quick overview, start with:

- `docs/results_summary_revised.md`
- `docs/article_method_decision_log.md`
- `docs/model_comparison_summary_revised.txt`
- `docs/figure_captions_revised.txt`

## 6. Authors

### Original course project, Group 2

- Feruza Bakhtiyorova, Artificial Intelligence  
  Data preparation, cleaning, analysis, visualization, and modelling.

- Dunya Boon, Communication  
  Historical context, literature research, editing, and citations.

- Emily Li, History and Sociology  
  Literature integration, sustainability perspective, and report structuring.

### Revised article-extension analysis

The revised article-extension analysis was continued by Feruza Bakhtiyorova after the original course project and DHBenelux poster presentation, with feedback from Lorella Viola.

Course: Introduction to Digital Humanities & Social Analytics, Lorella Viola, Vrije Universiteit Amsterdam.
