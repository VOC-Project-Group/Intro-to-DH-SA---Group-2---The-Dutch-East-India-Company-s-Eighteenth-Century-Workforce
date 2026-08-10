import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE, "data_raw")
TABLES = os.path.join(BASE, "tables")

os.makedirs(TABLES, exist_ok=True)

contracts_path = os.path.join(DATA_RAW, "voc_persons_contracts.csv")
contracts = pd.read_csv(contracts_path, low_memory=False)

# Check needed columns
needed_cols = ["reason_end_contract", "could_muster_again"]
missing_cols = [col for col in needed_cols if col not in contracts.columns]

if missing_cols:
    print("Missing columns:", missing_cols)
    print("Available columns containing 'muster' or 'reason':")
    print([col for col in contracts.columns if "muster" in col.lower() or "reason" in col.lower()])
    raise SystemExit

total_records = len(contracts)

summary = (
    contracts
    .assign(reason_end_contract=contracts["reason_end_contract"].fillna("MISSING"))
    .groupby("reason_end_contract", dropna=False)
    .agg(
        count=("reason_end_contract", "size"),
        could_muster_again_1=("could_muster_again", lambda s: (s == 1).sum()),
        could_muster_again_0=("could_muster_again", lambda s: (s == 0).sum()),
        could_muster_again_missing=("could_muster_again", lambda s: s.isna().sum()),
    )
    .reset_index()
)

summary["percentage_of_dataset"] = (summary["count"] / total_records * 100).round(2)
summary["could_muster_again_1_pct_within_reason"] = (
    summary["could_muster_again_1"] / summary["count"] * 100
).round(2)

summary = summary.sort_values("count", ascending=False)

output_path = os.path.join(TABLES, "reason_end_contract_with_muster_again.csv")
summary.to_csv(output_path, index=False)

print(summary)
print(f"\nSaved to: {output_path}")