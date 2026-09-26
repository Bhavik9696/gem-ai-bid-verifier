"""
PAN Connector — GET /api/v1/pan/{pan}

Looks up a PAN in the demo Income Tax / PAN source records.
"""

from fastapi import APIRouter
from app.data.loader import find_pan
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/pan/{pan}",
    response_model=ConnectorResponse,
    summary="Verify a PAN against demo Income Tax source data",
)
def verify_pan(pan: str) -> ConnectorResponse:
    record = find_pan(pan)

    if record is None:
        return ConnectorResponse(
            source="PAN_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=pan.upper(),
            status=ConnectorStatus.NOT_FOUND,
            verifiedFacts={},
            evidenceReference="demo-data/pan-records.json",
        )

    verified_facts = {
        "entityName": record["entityName"],
        "entityType": record.get("entityType"),
        "panStatus": record["status"],
        "dateOfIncorporation": record.get("dateOfIncorporation"),
        "assessmentYear": record.get("assessmentYear"),
        "itFilingStatus": record.get("itFilingStatus"),
        "lastFiledAY": record.get("lastFiledAY"),
        "linkedGSTIN": record.get("linkedGSTIN"),
        "conflictNote": record.get("conflictNote"),
    }

    status = ConnectorStatus.VERIFIED
    if record.get("scenario") == "PAN_NAME_DIFFERS_FROM_GST":
        # Both GST and PAN records are individually valid,
        # but entity names differ — the compliance engine raises the conflict.
        status = ConnectorStatus.MISMATCH

    return ConnectorResponse(
        source="PAN_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=pan.upper(),
        status=status,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/pan-records.json#{pan.upper()}",
    )
