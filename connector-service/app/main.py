"""
App factory for the Connector Service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import gst, pan, udyam, mca, oem, digilocker, blacklist, statutory, health


def create_app() -> FastAPI:
    app = FastAPI(
        title="ComplianceOS — Demo Connector Service",
        description=(
            "Dynamic demo source connectors for the ComplianceOS prototype. "
            "All responses carry mode=DEMO and must never be presented as live "
            "government portal data."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(gst.router, prefix="/api/v1", tags=["GST"])
    app.include_router(pan.router, prefix="/api/v1", tags=["PAN"])
    app.include_router(udyam.router, prefix="/api/v1", tags=["Udyam"])
    app.include_router(mca.router, prefix="/api/v1", tags=["MCA"])
    app.include_router(oem.router, prefix="/api/v1", tags=["OEM"])
    app.include_router(digilocker.router, prefix="/api/v1", tags=["DigiLocker"])
    app.include_router(blacklist.router, prefix="/api/v1", tags=["Blacklist"])
    app.include_router(statutory.router, prefix="/api/v1", tags=["Statutory"])

    return app
