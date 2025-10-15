# **Notebooks Documentation**

This folder contains the main Python scripts used for the analysis of the **Dutch East India Company (VOC) workforce (1700–1780)**.  
Each script can be run independently, but they are designed to be executed in sequence to reproduce the full workflow.

## **1. 01_cleaning.py**
**Purpose:**  
Prepares the data for analysis by filtering, standardizing, and creating derived variables.

**Main tasks:**  
- Filters contracts between 1700 and 1780.
- Merges place data with standardized regions (A–I).
- Groups ranks into six parent categories: *Sea, Ship, Trade, Medical, Military, Other*.
- Derives seniority from wage quintiles.
- Simplifies outcomes to four groups: *Death, Repatriated, Attrition, Unknown*.
- Marks first-time contracts for recruitment analysis.

**Output:**  
- `data_clean/contracts_clean.csv`
- Summary tables (`rank_counts.csv`, `region_counts.csv`, `outcome_counts.csv`)


## **2. 02_descriptives.py**
**Purpose:**  
Performs descriptive analysis and creates visualizations for workforce patterns.

**Main tasks:**  
- Produces tables showing relationships between region, rank, and outcome.
- Calculates decade-level trends in mortality, attrition, and recruitment.
- Exports summary CSV files and figures for presentation.

**Key outputs:**  
- `/tables/`
  - `trend_by_decade.csv` 
  - `rank_parent_by_outcome_pct.csv`, etc.
- `/figures/`
  - `fig_region_by_rank_parent.png`
  - `fig_death_vs_recruitment_by_decade.png`
  - `fig_death_vs_recruitment_by_rank.png`
  - `fig_outcome_trends_plus_recruitment_by_rank.png`


## **3. 03_models.py**
**Purpose:**
Builds and evaluates machine learning models to predict contract outcomes.

**Main tasks:**
- Encodes categorical variables (region, rank, decade, etc.).
- Splits the dataset into training (507,700) and testing (169,234) subsets.
- Trains **Logistic Regression** and **Random Forest** models.
- Evaluates accuracy, recall, and precision using confusion matrices.
- Extracts feature importance to identify key predictors of contract outcomes.

**Key outputs:**  
- `/figures/`
  - `fig_logit_confusion_matrix.png`
  - `fig_rf_feature_importance.png`
  - `fig_rf_confusion_matrix.png`
- `/docs/`
  - `model_notes.txt` (includes metrics and classification reports)

## **Execution order**
1. Run `01_cleaning.py`
2. Run `02_descriptives.py`
3. Run `03_models.py`

All outputs are automatically saved in `/data_clean/`, `/tables/`, `/figures/`, and `/docs/`.
Make sure the raw CSVs are placed in `data_raw/` before starting.

## **Authors - Group 2**
- **Feruza Bakhtiyorova** (Artificial Intelligence) - Data preparation, cleaning, analysis, visualization, and modeling  
- **Dunya Boon** (Communication) - Historical context, literature research, editing, and citations  
- **Emily Li** (History and Sociology) - Literature integration, sustainability perspective, and report structuring  

**Course:** Introduction to Digital Humanities & Social Analytics - Lorella Viola, Vrije Universiteit Amsterdam (2025)
