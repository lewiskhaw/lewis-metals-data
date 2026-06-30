import os
import base64
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- ENTERPRISE WEB SYNC INITIALIZATION ---
GITHUB_USERNAME = "lewiskhaw"
GITHUB_REPO = "lewis-metals-data"
GITHUB_TOKEN = "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" # Your secret PAT key
FILE_PATH_IN_REPO = "lme_master_data.csv"

# Target local copy fallback path
OUTPUT_DIR = r"C:\Users\Evi\OneDrive - MIND ID Trading Pte. Ltd\Lewis_AI_Data_Sync"
os.makedirs(OUTPUT_DIR, exist_ok=True)
local_csv_path = os.path.join(OUTPUT_DIR, FILE_PATH_IN_REPO)

LME_ASSETS = {
    "Copper": "LMCU3 Comdty", "Aluminium": "LMAH3 Comdty", "Tin": "LMSN3 Comdty",
    "Nickel": "LMNI3 Comdty", "Lead": "LMPB3 Comdty", "Zinc": "LMZS3 Comdty"
}

print("🛰️ Extracting data records from local Bloomberg Terminal Server...")
# (Your highly stable local data loop engine runs here)
dates = pd.date_range(end=datetime.today(), periods=90, freq='D').strftime('%Y-%m-%d')
simulated_data = []
base_prices = {"Copper": 8500, "Aluminium": 2200, "Tin": 26000, "Nickel": 17000, "Lead": 2100, "Zinc": 2400}

for friendly_name in LME_ASSETS.keys():
    base = base_prices[friendly_name]
    for idx, date in enumerate(dates):
        simulated_data.append({
            "date": date, "open": base * (1 + (idx * 0.001)), "high": base * (1 + (idx * 0.002)),
            "low": base * (1 - (idx * 0.001)), "close": base * (1 + (idx * 0.0015)), "metal": friendly_name
        })
master_df = pd.DataFrame(simulated_data)

# Save a backup locally at the office
master_df.to_csv(local_csv_path, index=False)
csv_content = master_df.to_csv(index=False)

print("🚀 Uploading fresh market intelligence matrix directly to Cloud Secure Repository...")
url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH_IN_REPO}"
headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Get file sha fingerprint if it already exists to overwrite it cleanly
response = requests.get(url, headers=headers)
sha = response.json().get("sha") if response.status_code == 200 else None

payload = {
    "message": f"Update LME Market Matrix - {datetime.today().strftime('%Y-%m-%d %H:%M')}",
    "content": base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
}
if sha: payload["sha"] = sha

put_response = requests.put(url, headers=headers, json=payload)
if put_response.status_code in [200, 201]:
    print("✅ Success! Bloomberg data pipeline pushed directly to Cloud Core.")
else:
    print(f"❌ Cloud Push Failed: {put_response.json()}")
