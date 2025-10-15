# **Codebook - The Dutch East India Company’s Eighteenth-Century Workforce**

This document describes the variables used in our analysis of the Dutch East India Company (VOC) workforce between 1700 and 1780.  
It is intended to make the data cleaning and transformation process transparent and to support reproducibility.

## **1. Data Source**

All variables originate from the enriched VOC dataset compiled by **Petram et al. (2024)** and made available by the **International Institute of Social History (IISH)**.  
The dataset integrates several tables:

| File | Content |
|------|----------|
| `voc_persons_contracts.csv` | Core contract records for VOC employees |
| `voc_places.csv` | Original place names of origin |
| `voc_places_standardized.csv` | Standardized places with region codes (A–I) |
| `voc_ranks.csv` | Detailed occupational titles and wages |
| `voc_voyages.csv` | Voyage and fleet metadata (not analyzed here) |

The project focuses on contracts **starting between 1700 and 1780**, totaling **676 934** records after filtering.

## **2. Derived and Processed Variables**

| Variable name | Type | Description / Definition | Source / Derivation |
|----------------|-------|--------------------------|----------------------|
| `person_cluster_id` | Integer | Unique identifier for an individual (after disambiguation). | From `voc_persons_contracts.csv`. |
| `contract_id` | Integer | Unique contract identifier. | From `voc_persons_contracts.csv`. |
| `year_start` | Integer | Year when the contract began. | Parsed from contract date. |
| `decade` | Integer | Decade of contract start (e.g., 1700, 1710, …). Used for temporal trends. | Derived from `year_start`. |
| `place_of_origin` | Text | Raw place of origin as recorded in the VOC archives. | From raw data. |
| `place_standardized_id` | Integer | ID linking to standardized toponyms. | From `voc_places_standardized.csv`. |
| `region_code` | Text (A–I) | Region category (A = Dutch Republic, B = Low German, etc.). | From standardized mapping. |
| `region_label` | Text | Human-readable region name. | From standardized mapping; supplemented with fallbacks for Dutch toponyms. |
| `rank_raw` | Text | Detailed historical rank title (e.g., “matroos,” “opperkoopman”). | From `voc_ranks.csv`. |
| `rank_parent` | Categorical | Simplified parent rank group: **Sea**, **Ship**, **Trade**, **Medical**, **Military**, **Other**. | Mapped from `rank_raw`. |
| `wage_monthly` | Numeric | Monthly wage in guilders. | From `voc_ranks.csv`. |
| `wage_quintile` | Integer (1–5) | Relative wage quintile within all records. | Computed from `wage_monthly`. |
| `rank_level` | Integer | Seniority indicator (1 = lowest → 5 = highest). | Same as `wage_quintile`. |
| `is_high_rank` | Boolean | 1 if `rank_level` ≥ 4 (high wage / senior rank). | Derived. |
| `nationality_dutch` | Boolean | 1 if origin region = Dutch Republic, 0 otherwise. | Derived from `region_label`. |
| `reason_end_contract_raw` | Text | Unprocessed archival entry for contract termination. | From `voc_persons_contracts.csv`. |
| `outcome_group` | Categorical | Simplified outcome: **Death**, **Repatriated**, **Attrition**, **Unknown**. | Recoded from raw reason field. |
| `is_first_contract` | Boolean | 1 if this contract is the first recorded for that individual (recruitment). | Derived by comparing contract years per person. |
| `source_reference` | Text | Archival or database reference. | From `voc_sources.csv`. |

## **3. Summary Tables Generated**

| File | Purpose | Key columns |
|------|----------|-------------|
| `rank_counts.csv` | Counts of contracts per parent rank. | `rank_parent`, `count` |
| `region_counts.csv` | Counts of contracts per region. | `region_label`, `count` |
| `outcome_counts.csv` | Total counts by outcome category. | `outcome_group`, `count` |
| `rank_parent_by_outcome_count.csv` | Cross-tab of ranks by outcomes (counts). | `rank_parent`, `Death`, `Repatriated`, `Attrition`, `Unknown` |
| `rank_parent_by_outcome_pct.csv` | Same as above in percentages. | same columns as above |
| `region_by_outcome_group_count.csv` | Region × outcome table (counts). | `region_label`, `Death`, `Repatriated`, `Attrition`, `Unknown` |
| `region_by_outcome_group_pct.csv` | Region × outcome table (percentages). | same columns as above |
| `region_by_rank_parent_count.csv` | Region × rank table (counts). | `region_label`, `rank_parent` |
| `region_by_rank_parent_pct.csv` | Region × rank table (percentages). | `region_label`, `rank_parent` |
| `trend_by_decade.csv` | Decade-level summary of outcome and recruitment rates. | `decade`, `death_rate`, `recruitment_share`, etc. |
| `death_recruitment_by_rank_*.csv` | Decade-specific comparison of death and recruitment by rank (1700s–1780s). | `rank_parent`, `death_rate`, `recruitment_share` |
| `outcome_rates_by_decade_rank.csv` | Outcome rates for each rank per decade. | `decade`, `rank_parent`, `death`, `repatriated`, `attrition` |
| `outcome_rates_and_recruitment_by_decade_rank.csv` | Combined outcomes + recruitment share. | `decade`, `rank_parent`, `recruitment_share` |

## **4. Modeling Variables**

The predictive models used the following independent and dependent variables.

| Role | Variable | Description |
|------|-----------|-------------|
| **Target (y)** | `outcome_group` | Four-class categorical variable: Death / Repatriated / Attrition / Unknown. |
| **Features (X)** | `rank_parent` | Occupational category (Sea, Ship, Trade, Medical, Military, Other). |
| | `region_label` | Region of origin. |
| | `decade` | Start decade of contract. |
| | `is_high_rank` | Binary indicator for senior position. |
| | `is_first_contract` | Recruitment indicator. |
| | `nationality_dutch` | Binary Dutch / non-Dutch. |

Data split: **train = 507 700**, **test = 169 234**.
Both models used `class_weight="balanced"` to account for class imbalance.

## **5. Output Figures**

| Figure file | Description |
|--------------|-------------|
| `fig_region_by_rank_parent.png` | Distribution of worker origins across rank categories. |
| `fig_death_vs_recruitment_by_decade.png` | Death and recruitment rates per decade (1700–1780). |
| `fig_death_vs_recruitment_by_rank.png` | Comparison of death and recruitment shares across rank types. |
| `fig_outcome_trends_plus_recruitment_by_rank.png` | Small-multiples panel showing outcome and recruitment shares per rank over time. |
| `fig_logit_confusion_matrix.png` | Confusion matrix for Logistic Regression model on test data. |
| `fig_rf_feature_importance.png` | Ranked list of variable importance for Random Forest model. |
| `fig_rf_confusion_matrix.png` | Confusion matrix for Random Forest predictions vs. true outcomes. |

## **6. Notes on Data Quality**

- Geographic coverage after fallbacks: **≈ 81.6 %**.
- Origin coverage (raw text field): **≈ 99.5 %**.
- Military rank category contains relatively fewer Dutch entries, likely due to data standardization artifacts.
- Asian or locally hired personnel are under-represented in this dataset; results apply primarily to the European workforce.

## **7. References**

- Petram, L., et al. (2024). *The Dutch East India Company’s Eighteenth-Century Workforce: An Enriched Data Collection.* Journal of Open Humanities Data.  
- Gaastra, F. S. (2007). *The Organization of the VOC.*
- Lucassen, J. (2004). *A Multinational and Its Labor Force: The Dutch East India Company, 1595–1795.*
- Rei, C. (2012). *Careers and Wages in the Dutch East India Company.* Vanderbilt University Department of Economics Working Paper 12-00007.

## **Credits**

- **Feruza Bakhtiyorova** (Artificial Intelligence) - Data preparation, processing, analysis, visualization, and modeling
- **Dunya Boon** (Communication) - Historical context, literature research, editing, and citations
- **Emily Li** (History and Sociology) - Literature integration, sustainability perspective, and report structuring

**Maintainer (technical contact):** Feruza Bakhtiyorova  
**Course:** Introduction to Digital Humanities & Social Analytics - Lorella Viola, Vrije Universiteit Amsterdam (2025)
