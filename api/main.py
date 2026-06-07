from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from onboarding.database import init_db
from onboarding.seed import seed_database
from onboarding.service import process_hire

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_database()


@app.post("/webhooks/hris")
def hris_webhook(payload: dict[str, Any]) -> JSONResponse:
    try:
        result = process_hire(payload)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "event_id": payload.get("event_id"),
                "status": "failed",
                "error": str(exc),
            },
        )

    return JSONResponse(status_code=202, content=result)


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
