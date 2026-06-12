import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO

# CONFIGURATION
LATITUDE = 35.882555
LONGITUDE = -106.123456 # Replace with your target longitude
OUTPUT_CSV = "TEST_DATA.csv" # Saved directly inside your repository folder

# Calculate yesterday's date
yesterday = datetime.now() - timedelta(days=1)
date_str = yesterday.strftime("%Y%m%d")

base_url = "https://nacse.org"
query_url = f"{base_url}/all/{date_str}?loc={LATITUDE},{LONGITUDE}&format=csv"

print(f"Requesting PRISM data for {yesterday.strftime('%Y-%m-%d')}...")

try:
    response = requests.get(query_url, timeout=20)
    if response.status_code == 200:
        lines = response.text.strip().split("\n")
        
        # Find where data rows start
        header_idx = next(i for i, line in enumerate(lines) if any(x in line for x in ["Date", "Name"]))
        clean_csv_text = "\n".join(lines[header_idx:])
        
        df_new_row = pd.read_csv(StringIO(clean_csv_text))
        df_new_row.columns = df_new_row.columns.str.strip()
        
        # Clean up column names to match your precise script layout
        df_new_row.rename(columns={
            "ppt": "ppt (mm)", "tmin": "tmin (degrees C)", "tmax": "tmax (degrees C)",
            "vpdmin": "vpdmin (hPa)", "vpdmax": "vpdmax (hPa)"
        }, inplace=True)
        
        # Format the date properly for consistency
        df_new_row['Date'] = pd.to_datetime(df_new_row['Date'].astype(str), errors='coerce')
        
        # Load existing database file if it exists, otherwise create a new one
        if os.path.exists(OUTPUT_CSV):
            df_master = pd.read_csv(OUTPUT_CSV)
            df_master['Date'] = pd.to_datetime(df_master['Date'], errors='coerce')
            df_combined = pd.concat([df_master, df_new_row], ignore_index=True)
            df_combined.drop_duplicates(subset=["Date"], inplace=True)
        else:
            df_combined = df_new_row
            
        # Ensure rows remain sorted cleanly by chronological calendar date
        df_combined.sort_values(by="Date", inplace=True)
        df_combined.to_csv(OUTPUT_CSV, index=False)
        print("Success! Data appended and saved to repository.")
    else:
        print(f"API Error Code: {response.status_code}")
except Exception as e:
    print(f"Automation Error: {e}")
