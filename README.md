# Intro-to-DH-SA---Group-2---The-Dutch-East-India-Company-s-Eighteenth-Century-Workforce

This repository contains our project files for the course Introduction to Digital Humanities & Social Analytics (taught by Lorella Viola at VU Amsterdam).
Our project examines workforce patterns within the VOC (Dutch East India Company) during the eighteenth century (1700-1780), with a focus on the relationships between origins, ranks, and contract outcomes. The analysis explores whether internal workforce dynamics reveal early structural weaknesses that may have contributed to the company’s eventual decline.

## Project overview

We analyzed a subset of the dataset “The Dutch East India Company’s Eighteenth-Century Workforce: an Enriched Data Collection” (Petram et al., 2024), produced by the Huygens Institute and the KNAW Humanities Cluster.
This dataset refines more than 770,000 muster records of VOC employees (1633–1794) into approximately 460,000 identified individuals, standardizing places of origin, ranks, and wages.
Focusing on the eighteenth century (1700–1780), our analysis explored patterns in workforce composition by region of origin, rank structure, and contract outcomes such as Death, Repatriated, Attrition, and Unknown.
Using descriptive statistics and predictive models (Logistic Regression and Random Forest), we tested whether recruitment and attrition patterns reveal internal workforce imbalances that led to the VOC’s decline.

## Main findings

- Death and attrition rates remained persistently high across the eighteenth century.
- Recruitment did not match the ranks with the highest losses.
- Rank and region were the strongest predictors of contract outcomes.
- The VOC’s workforce system appears structurally imbalanced, reflecting internal fragility during its decline.

## Repository structure

- data_raw: original CSVs provided by the instructor. Not tracked by Git due to size.
- data_clean: smaller processed(cleaned) CSVs that we generate. Not tracked by Git due to size.
- notebooks: Python scripts for processing(cleaning), descriptives, and modeling.
- figures: exported charts used in the report.
- tables: exported tables used in the report.
- docs: documentation files (workflow_documentation.pdf, codebook.md, methods_notes.txt, etc.).

## Data sources (place files in data_raw)

These CSV files were provided as part of the enriched VOC dataset package (Petram et al., 2024). 
We do not commit them to Git because of size.

- voc_persons_contracts.csv  → core contract records
- voc_places.csv             → original places
- voc_places_standardized.csv → standardized places with region codes (A-I)
- voc_ranks.csv              → detailed rank information
- voc_voyages.csv            → voyage information
- voc_sources.csv            → source references
- voc_names.csv              → name clusters and disambiguation
- voc_beneficiaries.csv      → beneficiaries listed in contracts

## Scripts and Reproducibility
The entire analysis is reproducible through three sequential Python scripts:
1. 01_cleaning.py - filters data (1700–1780), maps regions and ranks, creates derived variables
2. 02_descriptives.py - produces descriptive statistics and figures
3. 03_models.py - runs Logistic Regression and Random Forest models, generates feature importance and confusion matrices

## How to run
1. Create a virtual environment.
   - python -m venv .venv
   - source .venv/bin/activate  (Windows: .venv\Scripts\activate)
   - pip install -r requirements.txt
2. Put the raw CSV files into data_raw.
3. Run: python notebooks/01_cleaning.py
4. Outputs appear in data_clean, tables, and figures.

## Dependencies
See requirements.txt for exact versions.
Main libraries: pandas, numpy, matplotlib, scikit-learn, statsmodels, lifelines.

## **Documentation**
- `docs/workflow_documentation.pdf` - full workflow documentation
- `docs/codebook.md` - variable definitions and coding details
- `docs/methods_notes.txt` - detailed notes on preprocessing and modeling decisions
- `docs/model_notes.txt` - model results, evaluation metrics, and confusion matrices
- `docs/figure_captions.txt` - figure summaries and interpretations
- `docs/VOC_Methodology_Summary.pdf` - methodology and figures overview

## About the Figures

The figures summarize the main findings of the analysis:
- fig_region_by_rank_parent.png - distribution of worker origins across rank categories
- fig_death_vs_recruitment_by_decade.png - comparison of death and recruitment rates per decade
- fig_death_vs_recruitment_by_rank.png - death and recruitment patterns across rank types
- fig_outcome_trends_plus_recruitment_by_rank.png - decade-by-decade panel view showing outcomes and recruitment share for each rank
- fig_logit_confusion_matrix.png - model evaluation for Logistic Regression
- fig_rf_feature_importance.png - key variables influencing outcomes in the Random Forest model
- fig_rf_confusion_matrix.png - performance of the Random Forest model compared with actual outcomes

Each figure is listed in docs/figure_captions.txt in addition to the other figures we created throughout the project.

## Authors - Group 2
1. Feruza Bakhtiyorova (Artificial Intelligence) - Data preparation, analysis, modeling, and methodology writing
2. Dunya Boon (Communication) - Literature research, historical context, editing, and citations
3. Emily Li (History and Sociology) - Literature research, sustainability focus, and report structure
