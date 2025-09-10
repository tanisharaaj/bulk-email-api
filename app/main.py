from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from temporalio.client import Client

from app.settings import settings
from app.models import NotifyRequest, NotifyResponse
from app.workflows import NotifyMemberWorkflow
from app.auth import require_auth
from app.utils import get_members_from_sheet  # we'll add this helper

app = FastAPI(
    title="Member Email API",
    swagger_ui_parameters={"persistAuthorization": True},
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
        tls=True,
    )


@app.post("/notify", response_model=list[NotifyResponse])
async def notify(
    req: NotifyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    await require_auth(authorization=f"Bearer {credentials.credentials}")
    client: Client = app.state.temporal

    # 1. fetch members from the given tab
    members = get_members_from_sheet(
        sheet_id=settings.GOOGLE_SHEET_ID,
        sheet_tab=req.sheet_tab,
        service_account_path=settings.GOOGLE_SA_JSON_PATH,
    )

    responses: list[NotifyResponse] = []

    # 2. shared template data
    template_data = {
        "brand_name": req.brand_name,
        "app_name": req.app_name,
        "appstore_link": str(req.appstore_link),
        "playstore_link": str(req.playstore_link),
        "website_portal": str(req.website_portal),
    }
    if req.cta_url:
        template_data["cta_url"] = str(req.cta_url)

    # 3. start workflows for each member
    for member in members:
        member_id = member.get("member_id")
        email = member.get("email")

        if not member_id or not email:
            continue  # skip incomplete rows

        print(f"Starting workflow for {member_id} - {email}")

        try:
            handle = await client.start_workflow(
                NotifyMemberWorkflow.run,
                id=f"notify-{member_id}-{email}",
                task_queue=settings.TASK_QUEUE,
                args=[member_id, email, template_data],
            )
            responses.append(
                NotifyResponse(status="QUEUED", run_id=handle.first_execution_run_id)
            )
        except Exception as e:
            print("Workflow start failed for", email, ":", e)
            responses.append(NotifyResponse(status="FAILED", run_id=None, message=str(e)))

    return JSONResponse([resp.dict() for resp in responses])


@app.get("/health")
async def health():
    return {"status": "ok"}
