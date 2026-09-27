"""
Shared Pydantic schemas for all connector responses.

The standard response envelope is:
{
  "source":            str   — connector identifier (e.g. GST_DEMO)
  "mode":              "DEMO"
  "identifier":        str   — the identifier that was looked up
  "status":            str   — VERIFIED | NOT_FOUND | MISMATCH | EXPIRED |
                               BLACKLISTED | SOURCE_UNAVAILABLE
  "verifiedFacts":     dict  — connector-specific payload
  "checkedAt":         str   — ISO 8601 UTC timestamp
  "evidenceReference": str   — reference to the source record
}

Every connector MUST use mode="DEMO".  Never return mode="LIVE".
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConnectorMode(str, Enum):
    DEMO = "DEMO"
    LIVE = "LIVE"
    SANDBOX = "SANDBOX"
    MANUAL = "MANUAL"


class ConnectorStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NOT_FOUND = "NOT_FOUND"
    MISMATCH = "MISMATCH"
    EXPIRED = "EXPIRED"
    BLACKLISTED = "BLACKLISTED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ConnectorResponse(BaseModel):
    source: str = Field(..., description="Connector source identifier, e.g. GST_DEMO")
    mode: ConnectorMode = Field(ConnectorMode.DEMO, description="Always DEMO in prototype")
    identifier: str = Field(..., description="The identifier that was queried")
    status: ConnectorStatus = Field(..., description="Lookup result status")
    verifiedFacts: dict[str, Any] = Field(
        default_factory=dict, description="Connector-specific payload"
    )
    checkedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )
    evidenceReference: str = Field(
        default="demo-data", description="Reference to the backing source record"
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "connector-service"
    port: int = 8001
    mode: ConnectorMode = ConnectorMode.DEMO
    checkedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
