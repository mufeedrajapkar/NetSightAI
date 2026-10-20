"""
build_dataset.py
----------------
CN_AI Project — Dataset Aggregation & Validation Pipeline
Merges per-PC CSV captures from an input folder into a validated, unified training CSV.

Features:
  - Validates column names against ai/CONTRACT.md
  - Detects and drops malformed rows (missing values, unparseable floats, invalid labels)
  - Reports dropped row counts per file and total
  - Displays class counts and bot tier distributions
  - Warns loudly if any target class has fewer than 50 samples
"""

import os
import sys
import argparse
from typing import List, Tuple, Dict, Any
import pandas as pd
import numpy as np

# Canonical features specified by ai/CONTRACT.md
CONTRACT_NUMERICAL_FEATURES = [
    "requests_per_sec",
    "session_duration",
    "packet_size_mean",
    "packet_size_var",
    "request_interval_mean",
    "request_interval_var",
    "bytes_transferred",
    "num_connections",
]
CONTRACT_CATEGORICAL_FEATURES = ["protocol"]
CONTRACT_REQUIRED_FEATURES = CONTRACT_NUMERICAL_FEATURES + CONTRACT_CATEGORICAL_FEATURES
VALID_LABELS = {"human": "Human", "bot": "Bot", "suspicious": "Suspicious"}
VALID_PROTOCOLS = {"tcp": "TCP", "udp": "UDP"}
MIN_CLASS_THRESHOLD = 50


def validate_and_clean_dataframe(
    df: pd.DataFrame, source_name: str
) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Validate an individual DataFrame against the AI contract.
    Returns: (cleaned_df, dropped_count, drop_reasons)
    """
    initial_rows = len(df)
    drop_reasons: List[str] = []

    # 1. Check required columns exist
    missing_cols = [c for c in CONTRACT_REQUIRED_FEATURES + ["label"] if c not in df.columns]
    if missing_cols:
        drop_reasons.append(f"Missing required contract columns: {missing_cols}")
        return pd.DataFrame(), initial_rows, drop_reasons

    valid_mask = pd.Series(True, index=df.index)

    # 2. Check for null / NaN in required features or label
    null_mask = df[CONTRACT_REQUIRED_FEATURES + ["label"]].isna().any(axis=1)
    if null_mask.any():
        drop_reasons.append(f"{null_mask.sum()} rows with NaN / missing values")
        valid_mask &= ~null_mask

    # 3. Validate numerical feature parseability & types
    for col in CONTRACT_NUMERICAL_FEATURES:
        num_converted = pd.to_numeric(df[col], errors="coerce")
        nan_in_num = num_converted.isna() & valid_mask
        if nan_in_num.any():
            drop_reasons.append(f"{nan_in_num.sum()} rows with invalid numeric value in '{col}'")
            valid_mask &= ~nan_in_num

    # 4. Validate protocol
    valid_proto_mask = df["protocol"].astype(str).str.lower().isin(VALID_PROTOCOLS) & valid_mask
    invalid_proto_count = (valid_mask & ~valid_proto_mask).sum()
    if invalid_proto_count > 0:
        drop_reasons.append(f"{invalid_proto_count} rows with unrecognized protocol")
        valid_mask &= valid_proto_mask

    # 5. Validate label
    valid_label_mask = df["label"].astype(str).str.lower().isin(VALID_LABELS) & valid_mask
    invalid_label_count = (valid_mask & ~valid_label_mask).sum()
    if invalid_label_count > 0:
        drop_reasons.append(f"{invalid_label_count} rows with invalid label (allowed: Human, Bot, Suspicious)")
        valid_mask &= valid_label_mask

    cleaned_df = df[valid_mask].copy()

    # Normalize values
    for col in CONTRACT_NUMERICAL_FEATURES:
        cleaned_df[col] = pd.to_numeric(cleaned_df[col])
    cleaned_df["protocol"] = cleaned_df["protocol"].astype(str).str.lower().map(VALID_PROTOCOLS)
    cleaned_df["label"] = cleaned_df["label"].astype(str).str.lower().map(VALID_LABELS)

    dropped_count = initial_rows - len(cleaned_df)
    return cleaned_df, dropped_count, drop_reasons


def merge_dataset_directory(input_dir: str, output_path: str) -> pd.DataFrame:
    """
    Search input_dir for all CSV files, validate and clean each,
    and output unified dataset.
    """
    print(f"\n{'='*65}")
    print("SENTINELNET DATASET BUILDER & VALIDATOR")
    print(f"{'='*65}")
    print(f"  Input directory : {input_dir}")
    print(f"  Output CSV path : {output_path}")

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    csv_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith(".csv")
    ]

    if not csv_files:
        raise ValueError(f"No CSV capture files found in directory: {input_dir}")

    print(f"  Found {len(csv_files)} capture file(s):")
    for f in csv_files:
        print(f"    - {os.path.basename(f)}")

    cleaned_dfs = []
    total_raw_rows = 0
    total_dropped_rows = 0

    print(f"\n{'-'*65}")
    print("FILE VALIDATION SUMMARY:")
    print(f"{'-'*65}")

    for file_path in csv_files:
        filename = os.path.basename(file_path)
        try:
            df = pd.read_csv(file_path)
        except Exception as exc:
            print(f"  [!] Failed to read {filename}: {exc}")
            continue

        raw_count = len(df)
        total_raw_rows += raw_count
        cleaned, dropped, reasons = validate_and_clean_dataframe(df, filename)
        total_dropped_rows += dropped

        status_str = f"PASSED ({len(cleaned)} rows)" if dropped == 0 else f"PARTIAL ({len(cleaned)} valid, {dropped} dropped)"
        print(f"  [{status_str}] {filename}")
        for r in reasons:
            print(f"      -> {r}")

        if not cleaned.empty:
            cleaned_dfs.append(cleaned)

    if not cleaned_dfs:
        raise ValueError("No valid rows remained across all CSV files! Check format against ai/CONTRACT.md.")

    combined_df = pd.concat(cleaned_dfs, ignore_index=True)
    print(f"\n{'-'*65}")
    print("DATASET AGGREGATION RESULTS:")
    print(f"{'-'*65}")
    print(f"  Total raw rows read    : {total_raw_rows}")
    print(f"  Total dropped rows     : {total_dropped_rows}")
    print(f"  Valid unified rows     : {len(combined_df)}")

    # Class distribution
    print(f"\n  Class Counts:")
    counts = combined_df["label"].value_counts()
    for cls, count in counts.items():
        print(f"    - {cls:12s}: {count:5d} sessions ({count / len(combined_df) * 100:.1f}%)")

    # Bot tier breakdown if present
    if "bot_tier" in combined_df.columns:
        print(f"\n  Bot Tier Breakdown:")
        tier_counts = combined_df["bot_tier"].fillna("None/Human").value_counts()
        for tier, count in tier_counts.items():
            print(f"    - {str(tier):12s}: {count:5d} sessions")

    # Minimum row checks
    under_threshold = [cls for cls, count in counts.items() if count < MIN_CLASS_THRESHOLD]
    if under_threshold:
        print(f"\n{'!'*65}")
        for cls in under_threshold:
            print(f"  [!] WARNING: Class '{cls}' has only {counts[cls]} rows (< {MIN_CLASS_THRESHOLD} minimum target)!")
        print("  Models trained with < 50 samples per class may overfit or fail stratified folds.")
        print(f"{'!'*65}\n")
    else:
        print(f"\n  [+] All classes satisfy minimum threshold of {MIN_CLASS_THRESHOLD} sessions.")

    # Save output
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    combined_df.to_csv(output_path, index=False)
    print(f"\n  [✓] Unified dataset saved to: {output_path}\n")

    return combined_df


def main():
    parser = argparse.ArgumentParser(description="SentinelNet Dataset Merging and Validation CLI")
    parser.add_argument(
        "--input-dir",
        default="data/real",
        help="Directory containing per-PC raw capture CSV files (default: data/real)",
    )
    parser.add_argument(
        "--output",
        default="data/processed/sentinelnet_real_dataset.csv",
        help="Output CSV path for the merged and validated dataset",
    )
    args = parser.parse_args()

    try:
        merge_dataset_directory(args.input_dir, args.output)
    except Exception as exc:
        print(f"\n[ERROR] Failed to build dataset: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
