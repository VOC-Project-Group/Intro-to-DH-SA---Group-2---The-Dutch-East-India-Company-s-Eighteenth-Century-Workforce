# Codebook

This codebook records the exact mappings used in cleaning and analysis so results are reproducible.

## Regions (from voc_places_standardized.csv)
Code → Label
- A → Dutch Republic
- B → Low German
- C → Scandinavia
- D → German interior
- E → British Isles
- F → France
- G → Iberia
- H → Italy or Corsica
- I → Eastern or Southeastern Europe
- 0 → Unknown or unassigned

Derived flags
- is_dutch = 1 if region == "A", else 0
- region_unknown = 1 if region == "0", else 0

## Rank parent categories
Detailed rank titles are mapped to the following six parents:
- Sea
- Ship
- Trade
- Medical
- Military
- Other

To be added: The final mapping.

## Ordered rank ladder
An integer rank_level is created to reflect seniority. Suggested ladder:
- 1 entry or apprentice
- 2 ordinary crew or soldier
- 3 petty officer or corporal
- 4 officer or mate or assistant
- 5 senior officer or first mate or merchant
- 6 command or senior merchant

To be added: The final ladder mapping and a few examples will be included here once validated.

## Outcome groups
Raw reasons for end of contract are mapped to four groups:
- Repatriated
- Death  includes deceased, shipwrecked, executed, murdered
- Attrition  includes deserted, dismissed, penalised
- Ambiguous  includes missing, last record, unknown

To be added: The final OUTCOME_MAP from 01_cleaning.py will be included here when finalized.

