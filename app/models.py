from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()


class NotifyRequest(BaseModel):
    member_id: str
    email: EmailStr
    brand_name: str
    app_name: str
    appstore_link: str
    playstore_link: str
    website_portal: str
    # Optional: call-to-action URL (you can still use it if needed)
    cta_url: str | None = None


class NotifyResponse(BaseModel):
    status: str
    run_id: str | None = None
    message: str | None = None
