from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.routers import auth, calendar, milestones, qualifications, study_logs


def create_app() -> FastAPI:
    app = FastAPI(title="learnlog api", version="0.1.0")

    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = FastAPI()
    api.include_router(auth.router)
    api.include_router(qualifications.router)
    api.include_router(study_logs.router)
    api.include_router(milestones.router)
    api.include_router(calendar.router)

    app.mount("/api/v1", api)
    return app


app = create_app()
handler = Mangum(app)
