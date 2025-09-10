from pydantic import BaseModel, HttpUrl
from typing import Optional


class NotifyRequest(BaseModel):
    # which Google Sheet tab to read from
    sheet_tab: str

    # shared parameters for all members in that tab
    brand_name: str
    app_name: str
    appstore_link: HttpUrl
    playstore_link: HttpUrl
    website_portal: HttpUrl
    cta_url: Optional[HttpUrl] = None


class NotifyResponse(BaseModel):
    status: str
    run_id: str | None = None
    message: str | None = None
