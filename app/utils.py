import gspread
from typing import List, Dict


def get_members_from_sheet(sheet_id: str, sheet_tab: str, service_account_path: str) -> List[Dict[str, str]]:
    gc = gspread.service_account(filename=service_account_path)
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.worksheet(sheet_tab)

    records = worksheet.get_all_records()  # returns list of dicts
    # each dict will have keys like {"member_id": "...", "email": "...", ...}
    return records
