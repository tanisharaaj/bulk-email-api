from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()




class Settings(BaseSettings):
    # Temporal
    TEMPORAL_NAMESPACE: str
    TEMPORAL_API_KEY: str
    TEMPORAL_ADDRESS: str
    TASK_QUEUE: str = "member-email-task-queue"

    # Google Sheets (primary)
    GOOGLE_SA_JSON_PATH: str | None = None
    GOOGLE_SHEET_ID: str | None = None
    GOOGLE_SHEET_TAB: str = "Members"
    GOOGLE_LOG_SHEET_TAB: str = "Log"

    # CSV fallback
    CSV_PATH: str = "./members.csv"
    LOG_CSV_PATH: str = "./delivery_log.csv"

    # SendGrid
    SENDGRID_API_KEY: str | None = None
    SENDGRID_TEMPLATE_ID: str | None = None
    SENDGRID_FROM_EMAIL: str | None = None
    SENDGRID_FROM_NAME: str = "Notifications"

    # Auth
    AUTH_STATIC_BEARER_TOKEN: str | None = None
    AUTH_JWT_SECRET: str | None = None
    AUTH_JWT_ISSUER: str | None = None
    AUTH_JWT_AUDIENCE: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
