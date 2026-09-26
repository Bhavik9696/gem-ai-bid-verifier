"""
Udyam/MSME Connector — GET /api/v1/udyam/{udyamNumber}

Looks up a Udyam registration number in the demo MSME source records.
NOT_FOUND is the expected response for Crest Systems (they didn't register Udyam),
which signals a mandatory-gate failure to the compliance engine.
"""

from fastapi import APIRouter
from app.data.loader import find_udyam
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/udyam/{udyam_number}",
    response_model=ConnectorResponse,
    summary="Verify a Udyam/MSME registration number",
)
def verify_udyam(udyam_number: str) -> ConnectorResponse:
    record = find_udyam(udyam_number)

    if record is None:
        return ConnectorResponse(
            source="UDYAM_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=udyam_number.upper(),
            status=ConnectorStatus.NOT_FOUND,
            verifiedFacts={},
            evidenceReference="demo-data/udyam-records.json",
        )

    verified_facts = {
        "entityName": record["entityName"],
        "pan": record["pan"],
        "gstin": record.get("gstin"),
        "category": record.get("category"),
        "enterpriseType": record.get("enterpriseType"),
        "registrationDate": record.get("registrationDate"),
        "validUpto": record.get("validUpto"),
        "udyamStatus": record["status"],
        "nic2008ActivityCode": record.get("nic2008ActivityCode"),
        "majorActivityDescription": record.get("majorActivityDescription"),
        "districtIndustriesCentre": record.get("districtIndustriesCentre"),
        "state": record.get("state"),
    }

    return ConnectorResponse(
        source="UDYAM_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=udyam_number.upper(),
        status=ConnectorStatus.VERIFIED,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/udyam-records.json#{udyam_number.upper()}",
    )
