# Codebook

This codebook records the exact mappings used in cleaning and analysis, so results are reproducible.

## Regions (from voc_places_standardized.csv)

Code → Label  
- A → Dutch Republic  
- B → Low German  
- C → German interior  
- D → British Isles  
- E → France  
- F → Iberia  
- G → Italy/Corsica  
- H → Scandinavia  
- I → Eastern/Southeastern Europe  

Derived flags  
- `is_dutch = 1` if region_label == "Dutch Republic", else 0  
- `region_label = "Unknown"` if no standardized region could be matched (ambiguous or missing bridge)

## Rank parent categories
Detailed rank titles are mapped to the following six parent groups:
- Sea  
- Ship  
- Trade  
- Medical  
- Military  
- Other  
- Unknown (fallback for unmapped titles)

## Ordered rank ladder
`rank_level` is derived from median_wage quintiles in `voc_ranks.csv`:
- 1 = lowest quintile  
- 2 = second quintile  
- 3 = middle quintile  
- 4 = fourth quintile  
- 5 = highest quintile  

Additional flag:  
- `is_high_rank = 1` if `rank_level >= 4` (top two quintiles), else 0

This method ensures a consistent hierarchy even when detailed career ladders are missing.

## Outcome groups
Raw `reason_end_contract` values are grouped into four analytical categories:  

- **Death** → includes deceased, shipwrecked, executed, murdered  
- **Repatriated** → includes repatriated, returned home, free citizen  
- **Attrition** → includes deserted, dismissed, penalised, removed  
- **Unknown (Ambiguous)** → includes missing, last record, unknown, not recorded, chamber labels, age


## Notes
- “Unknown” does not necessarily mean missing information. For origins, it means the origin could not be linked via the standardized bridge.  
- For ranks, “Unknown” applies to rare or ambiguous titles not mapped to the six parent categories.  
- For outcomes, “Unknown” groups all ambiguous, administrative, or unrecorded cases.
