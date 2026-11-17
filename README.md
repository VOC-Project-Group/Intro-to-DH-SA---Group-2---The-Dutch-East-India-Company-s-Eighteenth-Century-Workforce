# VOC Workforce Analysis

This repository documents research on the eighteenth-century workforce of the Dutch East India Company (VOC), developed through a university course project and a subsequent Digital Humanities tutorial/internship at Vrije Universiteit Amsterdam.

The project originated as a group assignment for *Introduction to Digital Humanities & Social Analytics*, completed by Group 2.

The research was subsequently developed further by **Feruza Bakhtiyorova as part of a Digital Humanities tutorial/internship supervised by Dr Lorella Viola** at Vrije Universiteit Amsterdam.

## Internship outputs

The Digital Humanities tutorial/internship resulted in two completed research outputs:

### 1. GitHub research repository

The present repository documents the VOC workforce research, including data preparation, methodology, analytical scripts, results, and research decisions.

### 2. DH Benelux research poster

**Workforce Imbalance and Structural Decline: A Data-Driven Analysis of the Dutch East India Company (1700–1780)**

**Authors:** Feruza Bakhtiyorova and Lorella Viola  
**Institution:** Vrije Universiteit Amsterdam

[View the poster on Zenodo](https://zenodo.org/records/19662396)

The poster presents the findings on occupational composition, recruitment patterns, mortality, and contract outcomes in the eighteenth-century VOC workforce.

The poster and GitHub repository constitute the completed outputs of the Digital Humanities tutorial/internship.

Further development into an academic article may be considered separately.

## Project background

The project examines workforce patterns within the VOC during the eighteenth century, with a focus on relationships between worker origins, rank categories, and contract outcomes.

The analysis uses the enriched VOC dataset:

**Petram et al. (2024), “The Dutch East India Company’s Eighteenth-Century Workforce: an Enriched Data Collection”**, produced by the Huygens Institute and the KNAW Humanities Cluster.

The dataset refines more than 770,000 VOC muster records into approximately 460,000 identified individuals, with standardized information on places of origin, ranks, wages, contracts, and related historical metadata.

## Original course project

The original course version focused on workforce composition, recruitment patterns, rank structure, and contract outcomes in the VOC between the 1700s and 1780s.

The original analysis explored whether internal workforce dynamics could reveal structural weaknesses that contributed to the VOC’s later decline.

Some older files in this repository belong to the original course version of the project. They may use earlier terminology, broader outcome categories, or older figure names.

## Revised analysis developed during the internship


Following the original course project, the analysis was further developed by Feruza Bakhtiyorova as part of a Digital Humanities tutorial/internship supervised by Dr Lorella Viola.

This work involved revising the methodology, refining the outcome categories, improving the interpretation of workforce patterns, and developing additional descriptive and statistical analyses.

The revised approach addresses methodological limitations identified during the research process and provides a more careful interpretation of the VOC workforce data.


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
- Earlier exploratory models are archived. The active question-specific binary logistic model is retained as part of the revised analysis, with its limitations explicitly documented.

## Current revised interpretation


The revised analysis identifies persistent occupational differences in recorded Death and Repatriated contract endings, particularly between Military and Sea ranks.

These differences suggest distinct patterns of occupational risk and workforce return that may have created vulnerabilities within the VOC labor system.

However, first-contract counts cannot be interpreted as direct replacement rates, and repatriation does not necessarily represent a permanent workforce loss. The available data also do not establish whether these workforce patterns contributed directly to the VOC's eventual collapse.

The revised findings therefore provide a basis for understanding occupationally differentiated workforce vulnerabilities rather than demonstrating a causal explanation for institutional decline.


## Repository structure and key files

This repository preserves the original group course project and documents the subsequent Digital Humanities tutorial/internship supervised by Dr Lorella Viola. It includes the revised analytical workflow, research outputs, methodological documentation, and archived exploratory analyses.

### `data_raw/`

Raw VOC data files. These files are not tracked by Git because of file size and data-management reasons.

Expected raw files include:

- `voc_persons_contracts.csv`
- `voc_places.csv`
- `voc_places_standardized.csv`
- `voc_ranks.csv`
- `voc_voyages.csv`
- `voc_sources.csv`
- `voc_names.csv`
- `voc_beneficiaries.csv`

### `data_clean/`

Cleaned and intermediate data files generated by the scripts. These files are not tracked by Git because of file size.

Main generated files include:

- `contracts_filtered.csv`
- `contracts_clean.csv`

### Main scripts

The main revised scripts are stored in the repository root.

#### `01_cleaning.py`

Cleans the raw VOC contracts data, creates revised outcome groups, and creates the corrected first-contract indicator.

Main outputs:

- `data_clean/contracts_filtered.csv`
- `data_clean/contracts_clean.csv`
- `tables/outcome_counts_revised.csv`
- `tables/reason_end_contract_mapping_check_revised.csv`
- `docs/methods_notes.txt`

#### `02_descriptives.py`

Creates revised descriptive tables and figures.

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

#### `03_models.py`

Runs the active question-specific binary logistic model.

The model includes only contracts ending in either Death or Repatriated. Death is coded as 1 and Repatriated is coded as 0. The model estimates whether a clearly recorded Death/Repatriated ending was Death rather than Repatriated.

The model includes rank, decade, rank x decade interaction, region, and high-rank status. It is run both on all records and on identifiable records only.

The identifiable-only model is used as a sensitivity check to test whether the main rank pattern remains similar when records without a valid `person_cluster_id` are excluded.

Main outputs:

- `tables/question_specific_logit_all_records_odds_ratios.csv`
- `tables/question_specific_logit_all_records_fit.csv`
- `tables/question_specific_logit_all_records_predicted_probabilities.csv`
- `tables/question_specific_logit_identifiable_only_odds_ratios.csv`
- `tables/question_specific_logit_identifiable_only_fit.csv`
- `tables/question_specific_logit_identifiable_only_predicted_probabilities.csv`
- `figures/fig_question_specific_rank_death_probabilities.png`
- `docs/question_specific_model_notes.txt`

#### `13_revised_outcome_first_contract_benchmark.py`

Creates benchmark tables comparing first-contract shares with Death, Repatriated, and Death + Repatriated shares by rank.

Main outputs:

- `tables/v3_reason_end_contract_mapping_check_1700_1780.csv`
- `tables/v3_missing_person_cluster_by_disambiguation_1700_1780.csv`
- `tables/v3_missing_person_cluster_by_rank_1700_1780.csv`
- `tables/v3_rank_first_contract_exit_benchmark_all_records_1700_1780.csv`
- `tables/v3_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv`
- `tables/v3_decade_rank_first_contract_exit_benchmark_all_records_1700_1780.csv`
- `tables/v3_decade_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv`

This script was used to refine the interpretation from a broad new-workforce-entry claim to a more specific first-contract versus exit-pattern comparison.


### Archived modelling analyses

Earlier exploratory analyses included six-category Logistic Regression and Random Forest models, as well as sensitivity and model-comparison scripts.

Following methodological revisions and supervisory feedback, these analyses were separated from the active workflow.

The archived scripts are:

- `archive/previous_models/scripts/14_model_sensitivity_without_first_contract.py`
- `archive/previous_models/scripts/15_model_comparison_summary.py`

The corresponding documentation, figures, and tables are organized under:

- `archive/previous_models/docs/`
- `archive/previous_models/figures/`
- `archive/previous_models/tables/`

These files are retained for transparency and documentation of the research process. They are not part of the current analysis workflow.

The original course-project files remain separately identifiable.


### `docs/`

Documentation and summary files.

Most useful revised files:

- `docs/results_summary_revised.md`
- `docs/article_method_decision_log.md`
- `docs/figure_captions_revised.txt`
- `docs/question_specific_model_notes.txt`

Original course documentation may also be present, including:

- `docs/workflow_documentation.pdf`
- `docs/codebook.md`
- `docs/methods_notes.txt`
- `docs/model_notes.txt`
- `docs/figure_captions.txt`
- `docs/VOC_Methodology_Summary.pdf`

### `tables/`

Generated CSV tables from the original and revised analyses.

Key revised tables include:

- `outcome_counts_revised.csv`
- `reason_end_contract_mapping_check_revised.csv`
- `trend_by_decade_revised.csv`
- `first_contracts_vs_exits_by_rank_revised.csv`
- `outcome_rates_and_first_contract_share_by_decade_rank_revised.csv`
- `question_specific_logit_all_records_odds_ratios.csv`
- `question_specific_logit_identifiable_only_odds_ratios.csv`
- `question_specific_logit_all_records_predicted_probabilities.csv`
- `question_specific_logit_identifiable_only_predicted_probabilities.csv`

### `figures/`

Generated figures from the original and revised analyses.

Key revised figures include:

- `fig_region_by_rank_parent.png`
- `fig_rank_parent_by_outcome_revised.png`
- `fig_trend_over_time_revised.png`
- `fig_death_rate_and_first_contract_rate_by_decade.png`
- `fig_first_contracts_vs_exits_by_rank_revised.png`
- `fig_outcome_rates_and_first_contract_share_by_rank_revised.png`
- `fig_question_specific_rank_death_probabilities.png`

## Most useful research documentation

For an overview of the completed internship research and subsequent methodological revisions, start with:

- `docs/results_summary_revised.md`
- `docs/article_method_decision_log.md`
- `docs/question_specific_model_notes.txt`
- `docs/figure_captions_revised.txt``

## Data sources

The raw CSV files are not included in this repository.

To rerun the full analysis, place the VOC data files locally in `data_raw/`.

Expected raw files include:

- `voc_persons_contracts.csv`
- `voc_places.csv`
- `voc_places_standardized.csv`
- `voc_ranks.csv`
- `voc_voyages.csv`
- `voc_sources.csv`
- `voc_names.csv`
- `voc_beneficiaries.csv`


## How to run the revised analysis

The current analytical workflow consists of data cleaning, descriptive analysis, question-specific modelling, and first-contract benchmark comparisons.

From the repository root, run:

```bash
python 01_cleaning.py
python 02_descriptives.py
python 03_models.py
```

For the additional first-contract and exit-pattern benchmark:

```bash
python 13_revised_outcome_first_contract_benchmark.py
```

The scripts use locally available data and write results to the relevant output directories:

- `data_clean/`
- `tables/`
- `figures/`
- `docs/`

Raw VOC data must be provided locally because they are not included in the GitHub repository.

The earlier six-category and sensitivity models are preserved in the archive and are not part of the active workflow.


## Dependencies

See `requirements.txt` for package dependencies.

Main libraries used in the current analytical workflow include:

- pandas
- numpy
- matplotlib
- statsmodels

Earlier exploratory analyses also used scikit-learn. Some original project files may require additional dependencies.


## Current status

The Digital Humanities tutorial/internship has been completed.

Its two research outputs are the present GitHub repository and the DH Benelux poster presentation.

The repository documents the research workflow, analytical results, methodological revisions, and decisions developed during the project.

Earlier exploratory models are preserved separately in the archive for transparency.

Potential future work includes additional historical interpretation, literature review development, and preparation of an academic article. This work is separate from the completed internship.


## Authors - original course project, Group 2

1. Feruza Bakhtiyorova, Artificial Intelligence  
   Data preparation, analysis, modelling, and methodology writing.

2. Dunya Boon, Communication  
   Literature research, historical context, editing, and citations.

3. Emily Li, History and Sociology  
   Literature research, sustainability focus, and report structure.


## Digital Humanities tutorial/internship

Following the original group course project, Feruza Bakhtiyorova continued developing the VOC workforce research as part of a **Digital Humanities tutorial/internship supervised by Dr Lorella Viola** at Vrije Universiteit Amsterdam.

The internship involved refining the analytical workflow, revising the methodology, examining occupational mortality and repatriation patterns, and documenting the research process.

The completed internship outputs are:

- The GitHub repository containing the analytical workflow, results, and methodological documentation.
- The DH Benelux research poster, *Workforce Imbalance and Structural Decline: A Data-Driven Analysis of the Dutch East India Company (1700–1780)*, available on [Zenodo](https://zenodo.org/records/19662396).

The repository preserves the contributions of the original Group 2 course project while distinguishing them from the subsequent work carried out during the tutorial/internship.

Future academic publication may build on this research, but it is separate from the completed internship.

