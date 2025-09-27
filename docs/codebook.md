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
- `region_unknown = 1` if region_label == "Unknown", else 0  

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

`is_high_rank = 1` if `rank_level` is 4 or 5, else 0.  

This method ensures a consistent hierarchy even when detailed career ladders are missing.

## Outcome groups
Raw reasons for end of contract are mapped to 5 groups:
- Repatriated → e.g. “repatriated”, “free citizen”  
- Death → includes “deceased”, “shipwrecked”, “executed”, “murdered”  
- Attrition → includes “deserted”, “dismissed”, “penalised”, “removed”  
- Ambiguous → includes “missing”, “last record”, “not recorded”, “age”  
- Unknown → cases that could not be mapped
