# worker/worker.py
from __future__ import annotations

import asyncio
import logging
import signal

from temporalio.client import Client
from temporalio.worker import Worker

from app.settings import settings
from app.workflows import NotifyMemberWorkflow
from app.activities import (
    lookup_member_in_sheet,
    send_email_via_sendgrid,
    log_delivery_event,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [worker] %(message)s",
)



async def main() -> None:

    client = await Client.connect(
        target_host=settings.TEMPORAL_ADDRESS,
        namespace=settings.TEMPORAL_NAMESPACE,
        api_key=settings.TEMPORAL_API_KEY,
        tls=True,  # be explicit
    )
   
    
    logging.info(
        "Connected to Temporal namespace=%s, task_queue=%s",
        settings.TEMPORAL_NAMESPACE,
        settings.TASK_QUEUE,
    )

    # Register workflows and activities
    worker = Worker(
        client=client,
        task_queue=settings.TASK_QUEUE,
        workflows=[NotifyMemberWorkflow],
        activities=[
            lookup_member_in_sheet,
            send_email_via_sendgrid,
            log_delivery_event,
        ],
    )

    # Graceful shutdown on SIGINT/SIGTERM
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_signal(*_):
        logging.info("Shutdown signal received, stopping worker...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            # Windows / limited environments may not support signal handlers
            pass

    # Run worker until a stop signal is received
    async with worker:
        logging.info("Worker started; listening for jobs...")
        await stop_event.wait()
        logging.info("Worker stopping; waiting for in-flight tasks to finish...")


if __name__ == "__main__":
    asyncio.run(main())
