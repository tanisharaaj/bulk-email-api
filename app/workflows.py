from __future__ import annotations

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities in a workflow-safe way
with workflow.unsafe.imports_passed_through():
    from .activities import (
        lookup_member_in_sheet,
        send_email_via_sendgrid,
        log_delivery_event,
    )


@workflow.defn
class NotifyMemberWorkflow:
    @workflow.run
    async def run(
        self,
        member_id: str,
        email: str,
        template_payload: dict | None = None,
    ) -> str:
        retry = RetryPolicy(maximum_attempts=3)
        info = workflow.info()  # includes workflow_id and run_id

        # 1) Validate presence in sheet
        lookup = await workflow.execute_activity(
            lookup_member_in_sheet,
            args=[member_id, email],
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=retry,
        )

        if not lookup.get("found"):
            await workflow.execute_activity(
                log_delivery_event,
                args=[
                    info.workflow_id,
                    info.run_id,
                    member_id,
                    email,
                    "not_found",
                    "Member/email not present in sheet",
                    ""
                ],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry,
            )
            return "NOT_FOUND"

        # 2) Send email (with guard to log failures)
        dynamic_data = {"member_id": member_id}
        if template_payload:
            dynamic_data.update(template_payload)

        try:
            sg_status = await workflow.execute_activity(
                send_email_via_sendgrid,
                args=[email, dynamic_data],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry,
            )

            await workflow.execute_activity(
                log_delivery_event,
                args=[
                    info.workflow_id,
                    info.run_id,
                    member_id,
                    email,
                    "sent",
                    f"SendGrid status {sg_status}",
                    str(sg_status)
                ],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry,
            )
            return "SENT"

        except Exception as e:
            await workflow.execute_activity(
                log_delivery_event,
                args=[
                    info.workflow_id,
                    info.run_id,
                    member_id,
                    email,
                    "failed",
                    str(e),
                    ""
                ],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry,
            )
            raise
