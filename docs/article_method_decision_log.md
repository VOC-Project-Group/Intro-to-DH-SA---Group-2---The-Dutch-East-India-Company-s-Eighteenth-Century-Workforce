# Article method notes

This file is for myself while extending the VOC workforce project from the DHBenelux poster and abstract into a possible journal article.

I want to keep track of the methodological choices I make, because the analysis has already changed several times after checking the data more carefully and discussing the interpretation with Lorella. These notes are not meant to be the final methods section yet. They are mainly here so I can later see why I changed something, which scripts were involved, and what still needs to be checked.

I number the steps so I can keep track of the work more easily. The numbers are not formal decision IDs. They are just a practical way to follow the development of the analysis.

---

## Step 1: I kept the period 1700-1780

For now I am keeping the analytical period from 1700 to 1780, because this was also the period used in the original course project and in the DHBenelux version.

I checked whether the period could be justified by missingness in `reason_end_contract`, but that does not seem to be the case. The variable itself does not have a clear missing-value gap by decade. So I should not write that the 1700-1780 filter is chosen because `reason_end_contract` is only reliable in that period.

The better explanation is that this period keeps the article aligned with the original project scope and with the broader historical and source-completeness framing of the dataset. If I later write this in the paper, I need to be careful and not overclaim.

Files connected to this:

* `01_cleaning.py`
* `02_descriptives.py`
* `03_models.py`
* `12_revised_outcome_first_contract_comparison_v2.py`
* `13_revised_outcome_first_contract_benchmark.py`

---

## Step 2: I used the full dataset for checks, but not for the main analysis

I used the full dataset to inspect all possible values of `reason_end_contract`. This was useful because I needed to see which raw categories exist before grouping them.

The actual analysis still uses the 1700-1780 subset. The full dataset is mainly used as a diagnostic step, for example to check raw outcome categories or to calculate true first contracts before filtering.

Important reminder for myself: when reporting percentages, I should make clear whether they come from the full dataset or from the 1700-1780 analysis subset. Most article results should use the 1700-1780 subset unless I explicitly say otherwise.

Files connected to this:

* `04_reason_end_contract_counts_full.py`
* `05_reason_end_contract_coverage_by_decade.py`
* `12_revised_outcome_first_contract_comparison_v2.py`

---

## Step 3: I revised the outcome grouping

The old grouping of `reason_end_contract` was too broad. In particular, “Attrition” was not precise enough, because it grouped together different types of contract endings such as desertion, dismissal, penalisation, and removal. “Unknown” was also too broad, because some categories were known administrative outcomes rather than truly unknown.

After checking the source-paper explanations and discussing this with Lorella, I revised the grouping into clearer categories:

* Death
* Repatriated
* Irregular exit
* Chamber
* Unknown / unclear
* Other

The current mapping is:

**Death:** Deceased, Shipwrecked, Murdered, Death penalty

**Repatriated:** Repatriated

**Irregular exit:** Deserted, Dismissal, Penalised or punished, Removed, Woman

**Chamber:** Amsterdam chamber, Delft chamber, Rotterdam chamber, Zeeland chamber, Hoorn chamber, Enkhuizen chamber

**Unknown / unclear:** Missing, Unknown, Not recorded, Last record

**Other:** Absent upon departure, Age, Free citizen, Transferred, To a man of war, To a private ship, To regiment, Remains at the Cape, Unfit to work, Resignation, Otherwise, In lening gaan

This grouping is more transparent than the previous one, and it should be documented clearly in the article methods section.

Files connected to this:

* `09_outcome_grouping_v2.py`
* `10_cleaning_outcome_group_v3_test.py`
* `11_revised_outcome_hiring_comparison.py`
* `12_revised_outcome_first_contract_comparison_v2.py`
* later also `01_cleaning.py`, `02_descriptives.py`, and `03_models.py`

---

## Step 4: I separated Chamber into its own category

Lorella suggested separating all chamber-related outcomes into one group instead of putting them under “Other”. This makes sense because these categories are internally consistent and administrative in nature.

The Chamber group includes:

* Amsterdam chamber
* Delft chamber
* Rotterdam chamber
* Zeeland chamber
* Hoorn chamber
* Enkhuizen chamber

This change makes the grouping cleaner and avoids mixing these administrative endings with a very broad “Other” category.

Files connected to this:

* `12_revised_outcome_first_contract_comparison_v2.py`
* later also `01_cleaning.py`, `02_descriptives.py`, and `03_models.py`

---

## Step 5: I changed from keyword matching to dictionary-based mapping

Earlier exploratory scripts used keyword matching to test outcome groupings quickly. That was useful in the beginning, but it is not transparent enough for the final article version.

I changed the revised grouping to dictionary-based mapping. This means that each observed raw value of `reason_end_contract` is mapped directly to one revised group.

I also normalize the raw values before mapping by trimming spaces and converting everything to lowercase. This avoids small issues like `To regiment` and `to regiment` being treated differently.

Important reminder for myself: every script that uses the revised outcome grouping should print a warning or check table if any non-null category is left unmapped.

Files connected to this:

* `12_revised_outcome_first_contract_comparison_v2.py`
* later `01_cleaning.py`

---

## Step 6: I calculated first contracts before filtering

I calculate the first-contract indicator on the full dataset before filtering to 1700-1780.

This is important because if I calculate first contracts only after filtering, someone whose actual first contract was before 1700 could incorrectly appear as a first contract inside the analysis period.

So the current logic is:

1. Load the full contracts dataset.
2. Convert `date_begin_contract` to dates.
3. For each `person_cluster_id`, find the earliest contract date.
4. Mark a contract as a true first contract if its start date matches that person’s earliest contract date.
5. Only after that, filter to 1700-1780 for the actual analysis.

I need to keep calling this “first contracts” or “first contracts as a proxy for recruitment”. I should avoid calling it a direct hiring rate, because the dataset does not directly record hiring in a modern institutional sense.

Files connected to this:

* `12_revised_outcome_first_contract_comparison_v2.py`
* later `01_cleaning.py` and `02_descriptives.py`

---

## Step 7: I avoided “hiring rate” language

I changed the wording from “hiring” or “hiring rate” to “first contracts” where possible.

This is more careful because the dataset gives contract records, not a direct modern hiring variable. First contracts are useful as a proxy for recruitment, but they should not be treated as a perfect measure of institutional hiring.

Better terms:

* `first_contracts_n`
* `first_contract_share_within_rank`
* `first_contract_share_of_all_first_contracts`
* `first_contract_minus_death_share`

Terms to avoid:

* `hires_n`
* `hiring_rate`
* `hiring_share_of_all_hires`

This also matters for the article wording. I can say “first contracts as a proxy for recruitment”, but I should not simply say “hiring rate” without explaining it.

---

## Step 8: I compared first contracts with deaths by rank

The first revised comparison looked at whether first contracts match deaths by rank.

The main result was that first contracts broadly follow the overall distribution of contract endings, but they do not match the distribution of deaths. Military ranks are the clearest case: they account for a larger share of deaths than first contracts. Sea ranks show the opposite pattern.

Current local result:

* Sea ranks: 53.27% of all contract endings, 53.42% of first contracts, but 44.86% of deaths.
* Military ranks: 34.62% of all contract endings, 34.56% of first contracts, but 43.24% of deaths.

This means I should not frame the result as a general mismatch between first contracts and all contract endings. The more accurate interpretation is a mismatch between first contracts and mortality by rank.

This was also confirmed by Lorella, who wrote that it makes sense to frame the result as a mismatch between first contracts and mortality by rank.

Files connected to this:

* `summary_rank_first_contracts_vs_deaths.csv`
* `v2_death_vs_first_contract_share_by_decade_rank_1700_1780.csv`

---

## Step 9: I added repatriation as the next comparison to check

Lorella pointed out that I should not only compare first contracts with deaths. Repatriation is also a substantial reason for contracts ending, so it should be included in the analysis as well.

The next benchmark script should compare first contracts with:

* Death
* Repatriated
* Death + Repatriated

This should be done by rank and also by decade/rank.

The point is to check whether the mismatch only appears for deaths or whether it also appears when repatriations are included.

File to work on:

* `13_revised_outcome_first_contract_benchmark.py`

---

## Step 10: I planned to combine Death and Repatriated as major exits

Lorella also suggested grouping Death and Repatriated together against first contracts to make the argument stronger.

I need to be careful here. Death and repatriation are historically different outcomes and should not be described as the same thing. But analytically, both are major contract exits, so it can make sense to compare them together against first contracts.

Possible wording for later:

“Death and repatriation are combined here as major contract exits, not because they are historically equivalent, but because both represent substantial outflow from the active contract population.”

This combined measure should help test whether first contracts were enough to compensate for the most important forms of workforce exit.

File to work on:

* `13_revised_outcome_first_contract_benchmark.py`

---

## Step 11: I added a benchmark against all records / overall workforce structure

Lorella also raised an important criticism: a lower first-contract share in a certain rank does not automatically mean under-recruitment. The VOC might already have had enough workers in that category.

So I need a benchmark. The next analysis should compare first contracts and exits against the overall distribution of records by rank.

For each rank, I should compare:

* share of all records
* share of first contracts
* share of deaths
* share of repatriations
* share of death + repatriation

This should help answer whether first contracts were low only because the rank was already smaller or whether the mismatch remains visible even against the overall record distribution.

I may also compare first contracts with non-first contracts, but I need to be careful. Non-first contracts are not exactly a stable workforce measure. They are better described as already-recorded or returning workforce presence.

File to work on:

* `13_revised_outcome_first_contract_benchmark.py`

---

## Step 12: I decided not to update the main pipeline too early

I should not immediately change `01_cleaning.py`, `02_descriptives.py`, and `03_models.py`.

First, I need to finish the benchmark script and check whether the new results actually support the interpretation. Only after that should I update the main filtering, descriptive, and modelling scripts.

Current order:

1. Finish and run `13_revised_outcome_first_contract_benchmark.py`.
2. Check the benchmark results.
3. Decide how the interpretation should be phrased.
4. Update `01_cleaning.py`.
5. Update `02_descriptives.py`.
6. Rerun figures.
7. Update and rerun `03_models.py`.
8. Only then update the README, documentation, and article text.

This avoids changing the whole pipeline before I know what the benchmark shows.

---

## Step 13: I made a backup before editing the main scripts

Before continuing with the next scripts, I made a local backup folder:

`backup_20260713_1407`

I copied the main scripts into it:

* `01_cleaning.py`
* `02_descriptives.py`
* `03_models.py`
* `12_revised_outcome_first_contract_comparison_v2.py`
* `13_revised_outcome_first_contract_benchmark.py`

This was necessary because the local working folder is not currently a Git repository. Since I am working locally only, these manual backups are important before editing the main scripts.

---

## Step 14: I checked the current local folder and raw data files

The active working folder is:

`D:\Study\VU Amsterdam\Intro to Digital Humanities and Social Analytics\VOC_Dataset`

This folder contains the analysis scripts and the raw data. It is not currently a Git repository, so Git commands such as `git status` do not work here.

The raw data files are present in `data_raw`, including:

* `voc_persons_contracts.csv`
* `voc_places.csv`
* `voc_places_standardized.csv`
* `voc_ranks.csv`
* `voc_sources.csv`
* `voc_voyages.csv`
* `voc_names.csv`
* `voc_beneficiaries.csv`

This means I can continue working locally, but I should be careful with backups until I decide whether to connect this folder to Git or copy the final cleaned scripts into the actual GitHub repository.

---

## Step 15: I checked the needed columns before writing the benchmark script

Before writing the benchmark script, I checked the needed columns in the raw files.

In `voc_persons_contracts.csv`, the relevant columns are:

* `vocop_id`
* `person_cluster_id`
* `rank_id`
* `date_begin_contract`
* `reason_end_contract`
* `could_muster_again`

In `voc_ranks.csv`, the relevant columns are:

* `rank_id`
* `rank`
* `parent_rank`
* `category`
* `subcategory`
* `median_wage`

For rank grouping, I can use the `category` column from `voc_ranks.csv`. The categories are:

* MEDICAL
* MILITARY
* OTHER
* SEA
* SHIP
* TRADE

This is useful because I do not need to manually recreate rank groups for the benchmark script.

---

## Step 16: I found the missing `person_cluster_id` issue

Before writing the benchmark script, I checked missing values for `person_cluster_id`.

In the full dataset:

* total rows: 774,200
* missing `person_cluster_id`: 226,873
* missing `date_begin_contract`: 257

In the 1700-1780 analysis subset:

* filtered rows: 676,934
* missing `person_cluster_id`: 179,991
* missing percentage: 26.59%

This is important because first-contract status depends on `person_cluster_id`. If a row has no `person_cluster_id`, I cannot confidently know whether it is that person’s first contract.

The current script marks first contracts only for rows where a person cluster can be used. Rows without `person_cluster_id` effectively cannot be identified as true first contracts.

This does not mean the analysis is unusable, but it needs to be documented. Before interpreting first-contract shares too strongly, I should check whether missing `person_cluster_id` is evenly distributed across rank categories or concentrated in certain groups.

Next checks to run:

* missing `person_cluster_id` by `disambiguated_person`
* missing `person_cluster_id` by rank category
* number of identifiable records and first contracts among identifiable records

Depending on those results, I may need to add a limitation or sensitivity note to the article.

---

## Step 17: I checked missing `person_cluster_id` before writing the benchmark script

Before writing `13_revised_outcome_first_contract_benchmark.py`, I checked whether missing `person_cluster_id` could affect the first-contract analysis.

This matters because first-contract status depends on `person_cluster_id`. If a row has no `person_cluster_id`, I cannot confidently know whether it is that person’s first contract.

In the 1700-1780 analysis subset, there are 676,934 records. Of these, 179,991 records have no `person_cluster_id`, which is 26.59% of the subset.

I checked this against `disambiguated_person`. Almost all records without `person_cluster_id` are records where the person was not disambiguated:

* `disambiguated_person = 0`: 179,991 missing `person_cluster_id`
* `disambiguated_person = 1`: 0 missing `person_cluster_id`

I also checked missing `person_cluster_id` by rank category. The missingness is not evenly distributed:

* Sea: 22.70% missing
* Military: 34.09% missing
* Ship: 20.73% missing
* Other: 27.05% missing
* Medical: 17.69% missing
* Trade: 11.30% missing
* Unknown: 46.90% missing

This is important because Military has a higher missing percentage than Sea. Since Military is central to the argument, I need to be careful when interpreting first-contract comparisons by rank.

The current first-contract logic identifies 415,727 first contracts in the 1700-1780 subset. Among records with a non-missing `person_cluster_id`, this is 83.66%.

For the next benchmark script, I should therefore include not only the main benchmark using all records, but also a sensitivity check using only records with identifiable `person_cluster_id`. This will help check whether the interpretation changes when records without person disambiguation are excluded.

The limitation to remember for the article is that first-contract status is only directly identifiable for records with `person_cluster_id`. Records without `person_cluster_id` cannot be confidently classified as first contracts.

---

## Step 18: I wrote and ran the benchmark script

I wrote and ran `13_revised_outcome_first_contract_benchmark.py`.

The script worked and produced the planned benchmark tables in the `tables` folder. It created:

* `v3_reason_end_contract_mapping_check_1700_1780.csv`
* `v3_missing_person_cluster_by_disambiguation_1700_1780.csv`
* `v3_missing_person_cluster_by_rank_1700_1780.csv`
* `v3_rank_first_contract_exit_benchmark_all_records_1700_1780.csv`
* `v3_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv`
* `v3_decade_rank_first_contract_exit_benchmark_all_records_1700_1780.csv`
* `v3_decade_rank_first_contract_exit_benchmark_identifiable_only_1700_1780.csv`

The script confirmed that all non-null `reason_end_contract` categories were mapped successfully.

The rank-level benchmark using all records shows that the Military mismatch is clear for Death only:

* Military first contracts: 34.56%
* Military deaths: 43.24%
* Difference: -8.68 percentage points

This supports the interpretation that Military ranks carried a disproportionate mortality burden relative to first contracts.

However, when Death and Repatriated are combined, the mismatch becomes much weaker:

* Military first contracts: 34.56%
* Military Death + Repatriated: 33.40%
* Difference: +1.16 percentage points

For Sea ranks, the all-records Death + Repatriated comparison is also very close:

* Sea first contracts: 53.42%
* Sea Death + Repatriated: 53.75%
* Difference: -0.33 percentage points

This means I should be careful with the stronger argument that the VOC did not recruit enough overall when death and repatriation are combined. The current rank-level benchmark suggests a more precise interpretation: the imbalance is strongest for mortality specifically. When repatriation is included, the broader major-exit pattern is more balanced, partly because Sea ranks account for a very large share of repatriations.

Next I need to inspect the decade-rank benchmark to see whether this pattern is stable over time or whether some decades still show stronger mismatches.

## Step 19: I inspected the decade-rank benchmark

After running `13_revised_outcome_first_contract_benchmark.py`, I inspected the decade-rank benchmark for Sea and Military ranks.

The decade-level results confirm that the Military mismatch is stable for Death only. In the all-records benchmark, Military first-contract share is lower than Military death share in every decade:

* 1700s: -6.77
* 1710s: -7.89
* 1720s: -9.96
* 1730s: -9.14
* 1740s: -8.81
* 1750s: -10.58
* 1760s: -9.17
* 1770s: -8.48
* 1780s: -6.76

This supports the interpretation that Military ranks carried a consistent mortality burden relative to first contracts.

However, when Death and Repatriated are combined, the mismatch becomes much weaker. In the all-records benchmark, Military first-contract share is close to, or slightly above, the combined Death + Repatriated share in most decades:

* 1700s: +0.83
* 1710s: +3.82
* 1720s: +2.72
* 1730s: +1.35
* 1740s: +2.32
* 1750s: +0.68
* 1760s: +0.21
* 1770s: +0.13
* 1780s: -1.22

This means I should be careful with the stronger claim that the VOC did not recruit enough overall when death and repatriation are combined. The more accurate interpretation is that the clearest imbalance is mortality-specific.

The Sea pattern helps explain why the combined Death + Repatriated comparison becomes more balanced. Sea ranks have a much higher share of repatriations than deaths, so adding repatriation changes the overall exit distribution.

Current interpretation:
First contracts did not match mortality by rank, especially in Military ranks. But first contracts were much closer to the combined Death + Repatriated distribution. This suggests that the article should frame the strongest finding as a persistent mortality imbalance rather than a general recruitment deficit across all major exits.

## Step 20: I summarized the decade patterns across all ranks

I summarized the decade-rank benchmark across all ranks for three comparisons:

* first contracts minus deaths
* first contracts minus repatriations
* first contracts minus death + repatriation

This helped check whether the Military and Sea patterns are unique or part of a broader rank pattern.

The all-records benchmark shows that Military has a consistently negative difference for Death only. Across decades, the Military first-contract minus death share ranges from -10.58 to -6.76, with a mean of -8.62. This confirms that Military ranks were consistently overrepresented among deaths relative to first contracts.

The identifiable-only benchmark shows the same direction, but the gap is smaller. For Military, the first-contract minus death share ranges from -7.20 to -0.71, with a mean of -4.87. This means the mortality-specific mismatch remains visible even when the analysis is restricted to records with `person_cluster_id`, although missing person IDs do affect the size of the gap.

However, when Death and Repatriated are combined, the Military mismatch does not become stronger. In the all-records benchmark, Military has a mean difference of +1.20 for first contracts minus Death + Repatriated. In the identifiable-only benchmark, the mean difference is +4.28. This means Military is not underrepresented when death and repatriation are combined.

Sea ranks show the opposite pattern. Sea has a positive difference for Death only, but a large negative difference for Repatriated. This suggests that Sea ranks account for a much larger share of repatriations than deaths. Because of this, adding Repatriated changes the overall exit distribution and makes the combined Death + Repatriated comparison much more balanced.

Current interpretation:
The strongest result is a mortality-specific imbalance. Military ranks were consistently overrepresented among deaths relative to first contracts. However, the broader Death + Repatriated comparison does not support a simple claim that Military was under-recruited overall. Repatriation needs to be discussed separately because it shows a different rank pattern, especially for Sea ranks.

## Step 21: I updated the first-contract logic in `01_cleaning.py`

I updated `01_cleaning.py` so that first contracts are now calculated on the full dataset before filtering to 1700-1780.

This is important because first contracts should reflect a person’s true earliest contract in the full dataset, not only the first contract visible inside the filtered period. If first contracts were calculated only after filtering, a person with an earlier contract before 1700 could be incorrectly marked as a first contract in the analysis subset.

The updated cleaning script now does this:

1. Loads the full contracts dataset.
2. Converts `date_begin_contract` to a date.
3. Creates `contract_start_year`.
4. Marks whether a record has `person_cluster_id`.
5. Calculates each person’s earliest contract date on the full dataset.
6. Creates `is_first_contract_true`.
7. Keeps `is_first_contract` as an alias so older scripts do not break.
8. Filters to the 1700-1780 analysis period only after this.

The script ran successfully and printed:

`[info] Created first-contract indicator on the full dataset before filtering.`

The filtered dataset still contains 676,934 records, which matches the earlier analysis subset.

This change makes the first-contract variable methodologically cleaner, but the limitation remains that first-contract status can only be identified for records with `person_cluster_id`.

---

## Step 22: I updated the outcome grouping in `01_cleaning.py`

I updated the outcome section in `01_cleaning.py` to use the revised dictionary-based grouping instead of the old broad grouping.

The old grouping used categories such as Death, Repatriated, Attrition, and Unknown. This was too broad, especially because “Attrition” grouped different kinds of contract endings together and “Unknown” included some categories that were actually known administrative outcomes.

The revised grouping now creates:

* Death
* Repatriated
* Irregular exit
* Chamber
* Unknown / unclear
* Other

The revised grouping uses normalized `reason_end_contract` values and a dictionary-based mapping. This is more transparent because each raw category is mapped directly to one revised group.

The cleaning script now saves:

* `tables/outcome_counts_revised.csv`
* `tables/reason_end_contract_mapping_check_revised.csv`
* updated `data_clean/contracts_clean.csv`

The script ran successfully and confirmed that all non-null `reason_end_contract` categories were mapped.

The revised outcome counts in `contracts_clean.csv` are:

* Death: 351,404
* Repatriated: 203,890
* Chamber: 43,231
* Unknown / unclear: 41,686
* Other: 19,327
* Irregular exit: 17,396

I also checked that the first-contract columns still match after the cleaning update:

* `is_first_contract_true`: 415,727
* `is_first_contract`: 415,727
* records with `person_cluster_id`: 496,943

This means the alias column `is_first_contract` is still consistent with the corrected `is_first_contract_true` column.

I also removed the old duplicate first-contract block from `01_cleaning.py`, because first contracts are now calculated earlier in the script before filtering.

Current status:
`01_cleaning.py` has now been updated with the revised outcome grouping and corrected first-contract logic. The next step is to update `02_descriptives.py` so the descriptive tables and figures use the revised outcomes and the new benchmark interpretation.

## Step 23: I started updating `02_descriptives.py`

I started updating `02_descriptives.py` so that the descriptive tables and figures use the revised outcome grouping and corrected first-contract logic from `01_cleaning.py`.

First, I added explicit aliases near the data-loading section:

* `OUTCOME_COL`
* `FIRST_CONTRACT_COL`
* `outcome_group_for_descriptives`
* `first_contract_for_descriptives`

The script now uses `outcome_group_revised` as the outcome column and `is_first_contract_true` as the first-contract column.

The script ran successfully and printed:

`[info] Using outcome column: outcome_group_revised`

`[info] Using first-contract column: is_first_contract_true`

I then updated the revised outcome crosstab tables and the rank-by-outcome figure. The script now saves:

* `rank_parent_by_outcome_revised_count.csv`
* `rank_parent_by_outcome_revised_pct.csv`
* `region_by_outcome_group_revised_count.csv`
* `region_by_outcome_group_revised_pct.csv`
* `fig_rank_parent_by_outcome_revised.png`

This means the first descriptive outputs now explicitly use the revised outcome grouping.

However, some older terminology and filenames still remain in the script, especially “recruitment” and files such as `fig_death_vs_recruitment...`. The next step is to update those sections so they use first-contract terminology and reflect the revised interpretation more carefully.

## Step 24: I updated the decade trend section in `02_descriptives.py`

I updated the decade trend section in `02_descriptives.py` so it no longer uses the old “Attrition” category.

The revised trend table now uses the revised outcome groups and saves:

* `trend_by_decade_revised.csv`

The revised trend figure now includes:

* foreign share
* death rate
* repatriated rate
* irregular exit rate
* high-rank share

It saves:

* `fig_trend_over_time_revised.png`

I also replaced the old “Death rate vs recruitment by decade” figure with a more careful version that compares:

* death rate
* first-contract rate

It saves:

* `fig_death_rate_and_first_contract_rate_by_decade.png`

This is more accurate because first contracts are only a proxy for recruitment, not a direct hiring rate.

The script still contains older per-rank sections with “death vs recruitment” wording. The next step is to update those sections so they use first-contract terminology and match the revised interpretation.

## Step 25: I updated the per-rank first-contract and exit comparison in `02_descriptives.py`

I replaced the old “death vs recruitment by rank” section in `02_descriptives.py`.

The old section used “recruitment” wording and created files such as:

* `death_recruitment_by_rank.csv`
* `fig_death_vs_recruitment_by_rank.png`

This wording was too broad because first contracts are only a proxy for recruitment, not a direct hiring rate.

The updated section now compares:

* first-contract share
* death share
* repatriated share
* death + repatriated share

The script now saves the revised overall table and figure:

* `first_contracts_vs_exits_by_rank_revised.csv`
* `fig_first_contracts_vs_exits_by_rank_revised.png`

It also saves revised decade-specific tables and figures for each decade from the 1700s to the 1780s.

This update makes the descriptive script match the revised interpretation more closely. The focus is now on how first contracts compare with major exits by rank, rather than saying “recruitment” too directly.

## Step 26: I updated the final small-multiples section in `02_descriptives.py`

I replaced the final old “outcome rates + recruitment” section in `02_descriptives.py`.

The old section still used the old outcome categories:

- Attrition
- Death
- Repatriated
- Unknown

It also used “recruitment share” wording, which was not precise enough for the revised analysis.

The updated section now uses the revised outcome grouping and compares:

- death rate within rank and decade
- repatriated rate within rank and decade
- death + repatriated rate within rank and decade
- first-contract share across ranks within each decade

The script now saves:

- `outcome_rates_and_first_contract_share_by_decade_rank_revised.csv`
- `fig_outcome_rates_and_first_contract_share_by_rank_revised.png`
- `figure_captions_revised.txt`

This means the final descriptive figure now matches the revised method and terminology. The script avoids saying “recruitment” directly and instead uses “first-contract share”, which is more accurate.

## Step 27: I reran the cleaned pipeline after updating `01_cleaning.py` and `02_descriptives.py`

After updating the cleaning and descriptive scripts, I reran both scripts.

`01_cleaning.py` ran successfully and recreated:

- `data_clean/contracts_filtered.csv`
- `data_clean/contracts_clean.csv`
- `tables/outcome_counts_revised.csv`
- `tables/reason_end_contract_mapping_check_revised.csv`
- `docs/methods_notes.txt`

The console confirmed that first contracts were created on the full dataset before filtering:

`[info] Created first-contract indicator on the full dataset before filtering.`

It also confirmed that the analysis filter kept 676,934 records for 1700-1780s.

Then I reran `02_descriptives.py`. It used:

- `outcome_group_revised`
- `is_first_contract_true`

The script successfully saved the revised descriptive tables, revised figures, and revised figure captions.

This means the cleaning and descriptive pipeline is now aligned with the revised outcome grouping and first-contract interpretation.

## Step 28: I updated and reran `03_models.py`

I updated `03_models.py` so that the modelling script now uses the revised outcome grouping and corrected first-contract logic.

The model target is now `outcome_group_revised`, with the following classes:

- Death
- Repatriated
- Chamber
- Unknown / unclear
- Other
- Irregular exit

The first-contract feature now uses `is_first_contract_true`.

The script ran successfully and saved revised model outputs, including:

- `model_class_distribution_revised.csv`
- `model_logit_classification_report_revised.csv`
- `model_logit_confusion_matrix_revised.csv`
- `fig_logit_confusion_matrix_revised.png`
- `model_rf_classification_report_revised.csv`
- `model_rf_confusion_matrix_revised.csv`
- `model_rf_feature_importances_revised.csv`
- `fig_rf_feature_importance_revised.png`
- `fig_rf_confusion_matrix_revised.png`
- `model_notes_revised.txt`

The models are diagnostic and descriptive, not causal. They help check whether broad structural variables such as rank, region, decade, Dutch/non-Dutch status, high-rank status, and first-contract status can separate the revised outcome groups.

## Step 29: I inspected the revised model outputs

I inspected the outputs from the revised `03_models.py`.

The model target was `outcome_group_revised`, with six classes:

- Death
- Repatriated
- Chamber
- Unknown / unclear
- Other
- Irregular exit

The class distribution is highly imbalanced. Death represents 51.91% of records and Repatriated represents 30.12%.

The Logistic Regression model reached an accuracy of 0.314, with macro F1 of 0.205.

The Random Forest model reached an accuracy of 0.337, with macro F1 of 0.229.

These scores suggest that the broad structural variables used in the model do not cleanly separate all revised outcome groups. Therefore, the models should be treated as diagnostic and descriptive, not as main evidence for the article.

The Random Forest feature importances show that `first_contract_for_model` is the strongest feature, followed by rank-related variables such as `rank_parent_Military`, `is_high_rank`, and `rank_parent_Sea`.

This is useful, but it needs to be interpreted carefully because first-contract status is a derived workforce-entry variable. A later sensitivity model without first-contract status would be useful to check whether rank and region still matter when this variable is removed.

I also noticed that `decade` did not appear in the model notes as a feature, so the modelling script should be checked and updated to create or include decade consistently.

I then noticed that `decade` was not included in the first model run because it was not present in the cleaned file. I updated `03_models.py` to create `decade` from `contract_start_year` when needed.

After rerunning the script, the model notes confirmed that `decade` is now included as a feature.

This makes the modelling script more consistent with the rest of the analysis, but the model performance remains modest. This supports the decision to treat the models as a supplementary diagnostic check rather than as a main article result.

After adding `decade`, I reran `03_models.py`.

The revised model now includes:

- region_label
- rank_parent
- decade
- is_high_rank
- is_dutch
- first_contract_for_model

The Logistic Regression accuracy was 0.299, with macro F1 of 0.193.

The Random Forest accuracy was 0.328, with macro F1 of 0.250.

The Random Forest feature importances changed after adding `decade`. The most important features were:

- decade
- first_contract_for_model
- rank_parent_Military
- rank_parent_Sea
- is_high_rank

This suggests that temporal structure and first-contract status are important for separating outcome groups. Rank still appears in the feature importances, especially Military and Sea, but the model performance remains modest.

Because the model does not predict the revised outcome groups very strongly, I should treat it as a supplementary diagnostic check rather than as a main article result.

## Step 30: I created a sensitivity model without first-contract status

I created a separate sensitivity script called `14_model_sensitivity_without_first_contract.py`.

The purpose of this script is to repeat the revised outcome prediction task, but without using first-contract status as a feature.

This is important because `first_contract_for_model` was one of the strongest features in the main Random Forest model. Since first-contract status is a derived workforce-entry variable, I wanted to check whether rank, region, decade, Dutch/non-Dutch status, and high-rank status still help separate revised outcome groups when this variable is removed.

The sensitivity model uses:

- region_label
- rank_parent
- decade
- is_high_rank
- is_dutch

It excludes:

- first-contract status

The script ran successfully and saved model reports, confusion matrices, feature importances, figures, and notes. This gives a cleaner diagnostic comparison with the main revised model.

## Step 31: I interpreted the sensitivity model without first-contract status

I inspected the sensitivity model outputs from `14_model_sensitivity_without_first_contract.py`.

This model excludes first-contract status and uses only:

- region_label
- rank_parent
- decade
- is_high_rank
- is_dutch

The Random Forest sensitivity model reached an accuracy of 0.340, with macro F1 of 0.236 and weighted F1 of 0.369.

This is similar to the main revised Random Forest model, which had accuracy 0.328, macro F1 0.250, and weighted F1 0.368.

This means that removing first-contract status does not collapse the model. However, the overall model performance remains modest, so the modelling should still be treated as a supplementary diagnostic rather than as main evidence.

In the sensitivity model, the strongest Random Forest feature was `decade`, followed by `rank_parent_Military`, `rank_parent_Sea`, `is_high_rank`, and `is_dutch`.

This suggests that temporal structure is very important for separating revised outcome groups. Rank also remains relevant, especially Military and Sea, even without first-contract status.

The sensitivity result supports a careful interpretation: the models show that outcome patterns are structured by time and rank, but they do not predict revised outcome groups strongly enough to become the central article argument.

## Step 32: I created and cleaned the revised model comparison summary

I created a separate script called `15_model_comparison_summary.py`.

This script compares:

- the main revised Logistic Regression model with first-contract status
- the main revised Random Forest model with first-contract status
- the sensitivity Logistic Regression model without first-contract status
- the sensitivity Random Forest model without first-contract status

The script saves:

- `tables/model_comparison_summary_revised.csv`
- `docs/model_comparison_summary_revised.txt`

I first created a longer comparison table, but then cleaned it so that the final version has one row per model and feature set. The final comparison includes:

- accuracy
- macro precision
- macro recall
- macro F1
- weighted precision
- weighted recall
- weighted F1

The purpose of this comparison is to make the modelling results easier to interpret and to keep them clearly framed as diagnostic rather than central evidence.

The main comparison is that the Random Forest model with first-contract status had accuracy 0.328 and macro F1 0.250, while the Random Forest model without first-contract status had accuracy 0.340 and macro F1 0.236.

This means the sensitivity model performs similarly to the main model. The results are therefore not only driven by the first-contract variable. However, because performance remains modest, the modelling results should be treated as diagnostic and supplementary rather than central evidence.

## Step 33: I created a revised results summary

I created `docs/results_summary_revised.md`.

This file summarizes the revised analysis in one readable document. It includes:

- the revised outcome grouping
- the corrected first-contract logic
- the filtered dataset size
- revised outcome counts
- missing `person_cluster_id` issue
- first-contract versus exit patterns by rank
- revised descriptive outputs
- revised modelling outputs
- sensitivity model results
- current interpretation

The purpose is to make it easier for Lorella to review the current state of the analysis without needing to inspect every CSV and figure separately.

I also cleaned the file encoding so that quotation marks and apostrophes display correctly.