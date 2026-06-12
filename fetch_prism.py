import os
from datetime import datetime, timedelta
from io import StringIO
import pandas as pd
import requests

# 1. PARAMETERS FOR YOUR TARGET SITE
LATITUDE = 35.879129
LONGITUDE = -106.61524
OUTPUT_CSV = "TEST_DATA.csv"

# 2. AUTOMATICALLY COMPUTE YESTERDAY'S CALENDAR STRING (YYYYMMDD)
yesterday = datetime.now() - timedelta(days=1)
date_str = yesterday.strftime("%Y%m%d")

# 3. DIRECT PRISM DATA PORTAL API URL (Using standard HTTP fallback)
base_url = "http://nacse.org"
query_url = f"{base_url}/all/{date_str}?loc={LATITUDE},{LONGITUDE}&format=csv"

print(f"🔄 Requesting unattended data entry for date: {date_str}...")

try:
    response = requests.get(query_url, timeout=30)
    if response.status_code == 200:
        lines = response.text.strip().split("\n")

        # Find where data rows start (skipping metadata text headers)
        header_idx = next(
            i
            for i, line in enumerate(lines)
            if any(x in line for x in ["Date", "Name"])
        )
        clean_csv_text = "\n".join(lines[header_idx:])

        df_new_row = pd.read_csv(StringIO(clean_csv_text))
        df_new_row.columns = df_new_row.columns.str.strip()

        # Format columns to match your precise variable targets
        df_new_row.rename(
            columns={
                "ppt": "ppt (mm)",
                "tmin": "tmin (degrees C)",
                "tmax": "tmax (degrees C)",
                "vpdmin": "vpdmin (hPa)",
                "vpdmax": "vpdmax (hPa)",
            },
            inplace=True,
        )

        df_new_row["Date"] = pd.to_datetime(
            df_new_row["Date"].astype(str), errors="coerce"
        )

        # Merge with master database file if it already exists in the repo
        if os.path.exists(OUTPUT_CSV):
            df_master = pd.read_csv(OUTPUT_CSV)
            df_master["Date"] = pd.to_datetime(
                df_master["Date"], errors="coerce"
            )
            df_combined = pd.concat([df_master, df_new_row], ignore_index=True)
            df_combined.drop_duplicates(subset=["Date"], inplace=True)
        else:
            df_combined = df_new_row

        # Sort chronologically by date and save back
        df_combined.sort_values(by="Date", inplace=True)
        df_combined.to_csv(OUTPUT_CSV, index=False)
        print("✅ Daily weather download appended successfully to master CSV.")
    else:
        print(f"❌ PRISM HTTP Error Connection Code: {response.status_code}")
except Exception as e:
    print(f"❌ Unattended background automation failed: {e}")
