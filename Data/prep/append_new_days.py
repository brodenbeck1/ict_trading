
# filepath: /Users/blakerodenbeck/Projects/Data/prep/append_new_days.py
import pandas as pd
from pathlib import Path

def append_new_days(existing_csv: str, new_csv: str, output_csv: str = None) -> str:
    """
    Append only new timestamps from new_csv onto existing_csv.
    Writes result to output_csv (or overwrites existing_csv if output_csv is None).
    Returns path to written file.
    """
    existing_path = Path(existing_csv)
    new_path = Path(new_csv)
    if not new_path.is_file():
        raise FileNotFoundError(f"New data file not found: {new_csv}")
    if not existing_path.is_file():
        # If base file doesn't exist, just copy new file
        df_new = pd.read_csv(new_path, parse_dates=['timestamp'])
        out = output_csv or existing_csv
        df_new.sort_values('timestamp').to_csv(out, index=False)
        print(f"Base file missing. Created {out} with new data only. Rows={len(df_new)}")
        return out

    df_old = pd.read_csv(existing_path, parse_dates=['timestamp'])
    df_new = pd.read_csv(new_path, parse_dates=['timestamp'])

    # Ensure same columns
    missing_cols = set(df_old.columns) - set(df_new.columns)
    if missing_cols:
        raise ValueError(f"New file missing columns: {missing_cols}")

    # Identify truly new rows (timestamps not already present)
    old_ts = set(df_old['timestamp'])
    mask_new = ~df_new['timestamp'].isin(old_ts)
    df_add = df_new.loc[mask_new]

    if df_add.empty:
        print("No new timestamps to append.")
        return existing_csv

    # Concatenate and de-duplicate (defensive)
    df_out = (
        pd.concat([df_old, df_add], ignore_index=True)
          .drop_duplicates(subset=['timestamp'])
          .sort_values('timestamp')
    )

    out = output_csv or existing_csv
    df_out.to_csv(out, index=False)

    print(f"Appended {len(df_add)} new rows. Total rows now {len(df_out)}. Written to {out}")
    return out


if __name__ == "__main__":
    existing_file = "/Users/blakerodenbeck/Projects/Data/nq_futures_1m_cleaned.csv"
    new_file = "/Users/blakerodenbeck/Projects/Data/NQ_futures_1m_cleaned_new.csv"
    # Set output_csv to a different path to keep original intact, or leave None to overwrite.
    append_new_days(existing_file, new_file, output_csv=None)