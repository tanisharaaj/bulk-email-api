from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from temporalio.client import Client

from app.settings import settings
from app.models import NotifyRequest, NotifyResponse
from app.workflows import NotifyMemberWorkflow
from app.auth import require_auth


from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings

app = FastAPI(
    title="Member Email API",
    swagger_ui_parameters={"persistAuthorization": True},  # lock icon works
)

# parse comma-separated origins from env
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

# enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


@app.on_event("startup")
async def startup_event():
    print("Connecting to Temporal...")
    app.state.temporal = await Client.connect(
        "us-east-2.aws.api.temporal.io:7233",
        namespace=settings.TEMPORAL_NAMESPACE,
        api_key=settings.TEMPORAL_API_KEY,
        tls=True
    )


@app.post("/notify", response_model=NotifyResponse)
async def notify(
    req: NotifyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    await require_auth(authorization=f"Bearer {credentials.credentials}")

    client: Client = app.state.temporal

    print("Starting workflow with:")
    print("  member_id:", req.member_id)
    print("  email:", req.email)
    print("  brand_name:", req.brand_name)
    print("  app_name:", req.app_name)
    print("  appstore_link:", req.appstore_link)
    print("  playstore_link:", req.playstore_link)
    print("  website_portal:", req.website_portal)
    print("  cta_url:", req.cta_url)

    # Bundle all fields into dynamic template data
    template_data = {
        "brand_name": req.brand_name,
        "app_name": req.app_name,
        "appstore_link": req.appstore_link,
        "playstore_link": req.playstore_link,
        "website_portal": req.website_portal,
    }

    # Include optional field if present
    if req.cta_url:
        template_data["cta_url"] = req.cta_url

    try:
        handle = await client.start_workflow(
            NotifyMemberWorkflow.run,
            id=f"notify-{req.member_id}-{req.email}",
            task_queue=settings.TASK_QUEUE,
            args=[
                req.member_id,
                req.email,
                template_data,
            ],
        )
        return JSONResponse(
            NotifyResponse(status="QUEUED", run_id=handle.first_execution_run_id).dict()
        )
    except Exception as e:
        print("Workflow start failed:", e)
        raise e


@app.get("/health")
async def health():
    return {"status": "ok"}
