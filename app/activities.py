from __future__ import annotations

import pandas as pd
from temporalio import activity

from .sheets import sheet_client
from .emailer import emailer

from dotenv import load_dotenv
load_dotenv()


@activity.defn(name="lookup_member_in_sheet")
async def lookup_member_in_sheet(member_id: str, email: str) -> dict:
    """
    Validate (member_id, email) exists in the Members roster.
    Returns {"found": bool, "row": {...}} if found.
    """
    df: pd.DataFrame = sheet_client.members_df()

    if df.empty:
        return {"found": False}

    # Normalize
    df["member_id"] = df["member_id"].astype(str).str.strip()
    df["email"] = df["email"].astype(str).str.strip().str.lower()

    member_id_norm = str(member_id).strip()
    email_norm = email.strip().lower()

    match = df[(df["member_id"] == member_id_norm) & (df["email"] == email_norm)]
    if match.empty:
        return {"found": False}

    row = match.iloc[0].to_dict()
    return {"found": True, "row": row}


@activity.defn(name="send_email_via_sendgrid")
async def send_email_via_sendgrid(email: str, template_data: dict) -> str:
    """
    Send the templated email via SendGrid and return a status string.
    """
    return emailer.send(email, template_data)


@activity.defn(name="log_delivery_event")
async def log_delivery_event(
    workflow_id: str,
    run_id: str,
    member_id: str,
    email: str,
    status: str,
    message: str = "",
    sendgrid_status: str = "",
) -> None:
    """
    Append a delivery log row to the Log sheet/CSV.
    """
    sheet_client.append_log(
        {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "member_id": member_id,
            "email": email,
            "status": status,
            "message": message,
            "sendgrid_status": sendgrid_status,
        }
    )
