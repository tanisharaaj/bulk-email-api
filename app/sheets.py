from __future__ import annotations

import os
import time
import pandas as pd
from .settings import settings


from dotenv import load_dotenv
load_dotenv()


# Optional Google Sheets libs (only if you configure Google service account)
try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:  # keep optional
    gspread = None
    Credentials = None

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetClient:
    def __init__(self):
        self._client = None
        if (
            settings.GOOGLE_SA_JSON_PATH
            and os.path.exists(settings.GOOGLE_SA_JSON_PATH)
            and gspread
            and Credentials
        ):
            creds = Credentials.from_service_account_file(
                settings.GOOGLE_SA_JSON_PATH, scopes=SCOPES
            )
            self._client = gspread.authorize(creds)

    def members_df(self) -> pd.DataFrame:
        """
        Return the Members roster as a DataFrame with columns at least:
        ['member_id', 'email'].

        Prefers Google Sheets; falls back to CSV if not available.
        """
        if self._client and settings.GOOGLE_SHEET_ID:
            sh = self._client.open_by_key(settings.GOOGLE_SHEET_ID)
            ws = sh.worksheet(settings.GOOGLE_SHEET_TAB)
            data = ws.get_all_records()
            return pd.DataFrame(data)

        # Fallback: CSV
        if os.path.exists(settings.CSV_PATH):
            return pd.read_csv(settings.CSV_PATH)

        # Empty default
        return pd.DataFrame(columns=["member_id", "email"])

    def append_log(self, row: dict) -> None:
        """
        Append a single delivery log row to the 'Log' tab (or CSV fallback).
        Ensures consistent columns and includes both epoch and ISO timestamps.
        """
        cols = [
            "ts_epoch",
            "ts_iso",
            "workflow_id",
            "run_id",
            "member_id",
            "email",
            "status",
            "message",
            "sendgrid_status",
        ]
        now = int(time.time())
        iso = pd.Timestamp.utcnow().isoformat()

        base = {
            "ts_epoch": now,
            "ts_iso": iso,
            "workflow_id": row.get("workflow_id", ""),
            "run_id": row.get("run_id", ""),
            "member_id": row.get("member_id", ""),
            "email": row.get("email", ""),
            "status": row.get("status", ""),
            "message": row.get("message", ""),
            "sendgrid_status": row.get("sendgrid_status", ""),
        }

        if self._client and settings.GOOGLE_SHEET_ID:
            sh = self._client.open_by_key(settings.GOOGLE_SHEET_ID)
            try:
                ws = sh.worksheet(settings.GOOGLE_LOG_SHEET_TAB)
            except Exception:
                # Create tab and write header row once
                ws = sh.add_worksheet(
                    title=settings.GOOGLE_LOG_SHEET_TAB,
                    rows=1000,
                    cols=len(cols),
                )
                ws.append_row(cols)
            ws.append_row([base[c] for c in cols])
            return

        # CSV fallback with headers
        header = not os.path.exists(settings.LOG_CSV_PATH)
        pd.DataFrame([[base[c] for c in cols]], columns=cols).to_csv(
            settings.LOG_CSV_PATH, mode="a", header=header, index=False
        )


sheet_client = SheetClient()
