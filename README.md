# Intro-to-DH-SA---Group-2---The-Dutch-East-India-Company-s-Eighteenth-Century-Workforce

This repository contains our project files for the course Introduction to Digital Humanities & Social Analytics.
Our project investigates workforce patterns in the VOC (Dutch East India Company) during the eighteenth century, focusing on origins, ranks, and outcomes of contracts, and how these patterns may relate to the company’s decline.

## Folder structure
- data_raw: original CSVs provided by the instructor. Not tracked by Git.
- data_clean: smaller cleaned CSVs that we generate. Safe to commit.
- notebooks: Python scripts for cleaning, descriptives, and modeling.
- figures: exported charts used in the report.
- tables: exported tables used in the report.
- docs: documentation files (codebook.md, methods_notes.txt, figure_captions.txt, etc.).

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

## How to run
1. Create a virtual environment.
   - python -m venv .venv
   - source .venv/bin/activate  (Windows: .venv\Scripts\activate)
   - pip install -r requirements.txt
3. Put the raw CSV files into data_raw.
4. Run: python notebooks/01_cleaning.py
5. Outputs appear in data_clean, tables, and figures.
