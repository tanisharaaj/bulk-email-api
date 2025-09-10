import gspread
import os
from dotenv import load_dotenv

load_dotenv()

sa_json_path = os.getenv("GOOGLE_SA_JSON_PATH")
sheet_id = os.getenv("GOOGLE_SHEET_ID")

print("🔎 Using ID:", sheet_id)

gc = gspread.service_account(filename=sa_json_path)
sh = gc.open_by_key(sheet_id)  # <-- this should NOT raise 404
print("✅ Sheet title:", sh.title)
