from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.services.orchestration.seed import seed_demo_data
from app.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("complianceos.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and seed demo data
    logger.info("Initializing database...")
    init_db()
    with SessionLocal() as db:
        logger.info("Seeding demo data from %s...", settings.DEMO_DATA_DIR)
        seed_demo_data(db)
    logger.info("ComplianceOS Core API startup complete.")
    yield
    logger.info("Shutting down ComplianceOS Core API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="ComplianceOS Core API — Orchestration, Data Models, and Verification Backbone for GeM Procurement.",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)

    return app


app = create_app()
