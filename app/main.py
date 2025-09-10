from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from temporalio.client import Client

from app.settings import settings
from app.models import NotifyRequest, NotifyResponse, MemberRequest
from app.workflows import NotifyMemberWorkflow
from app.auth import require_auth

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
        tls=True,
    )


@app.post("/notify", response_model=list[NotifyResponse])
async def notify(
    req: NotifyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    await require_auth(authorization=f"Bearer {credentials.credentials}")
    client: Client = app.state.temporal

    responses: list[NotifyResponse] = []

    for member in req.members:
        print("Starting workflow with:")
        print("  member_id:", member.member_id)
        print("  email:", member.email)
        print("  brand_name:", member.brand_name)
        print("  app_name:", member.app_name)
        print("  appstore_link:", member.appstore_link)
        print("  playstore_link:", member.playstore_link)
        print("  website_portal:", member.website_portal)
        print("  cta_url:", member.cta_url)

        template_data = {
            "brand_name": member.brand_name,
            "app_name": member.app_name,
            "appstore_link": member.appstore_link,
            "playstore_link": member.playstore_link,
            "website_portal": member.website_portal,
        }
        if member.cta_url:
            template_data["cta_url"] = member.cta_url

        try:
            handle = await client.start_workflow(
                NotifyMemberWorkflow.run,
                id=f"notify-{member.member_id}-{member.email}",
                task_queue=settings.TASK_QUEUE,
                args=[member.member_id, member.email, template_data],
            )
            responses.append(
                NotifyResponse(status="QUEUED", run_id=handle.first_execution_run_id)
            )
        except Exception as e:
            print("Workflow start failed for", member.email, ":", e)
            responses.append(NotifyResponse(status="FAILED", run_id=None, message=str(e)))

    return JSONResponse([resp.dict() for resp in responses])


@app.get("/health")
async def health():
    return {"status": "ok"}
