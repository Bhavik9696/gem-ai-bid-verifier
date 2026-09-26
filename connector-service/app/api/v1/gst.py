"""
GST Connector — GET /api/v1/gst/{gstin}

Looks up a GSTIN in the demo GST source records.
Returns VERIFIED (with verifiedFacts) or NOT_FOUND.
When the record's legalName differs from any related bid entity name,
the MISMATCH scenario is surfaced via the verifiedFacts payload so
Member 5 (compliance engine) can raise the conflict finding.
"""

from fastapi import APIRouter
from app.data.loader import find_gst
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/gst/{gstin}",
    response_model=ConnectorResponse,
    summary="Verify a GSTIN against demo GST source data",
)
def verify_gst(gstin: str) -> ConnectorResponse:
    record = find_gst(gstin)

    if record is None:
        return ConnectorResponse(
            source="GST_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=gstin.upper(),
            status=ConnectorStatus.NOT_FOUND,
            verifiedFacts={},
            evidenceReference="demo-data/gst-records.json",
        )

    verified_facts = {
        "legalName": record["legalName"],
        "tradeName": record.get("tradeName"),
        "pan": record["pan"],
        "gstStatus": record["status"],
        "registrationDate": record["registrationDate"],
        "cancellationDate": record.get("cancellationDate"),
        "registeredAddress": record.get("registeredAddress"),
        "stateCode": record.get("stateCode"),
        "returnFilingStatus": record.get("returnFilingStatus"),
        "lastReturnPeriod": record.get("lastReturnPeriod"),
        "taxPayerType": record.get("taxPayerType"),
        "businessActivity": record.get("businessActivity"),
        "conflictNote": record.get("conflictNote"),
    }

    # Surface scenario as a top-level hint for the compliance engine
    status = ConnectorStatus.VERIFIED
    if record.get("scenario") == "NAME_MISMATCH":
        status = ConnectorStatus.MISMATCH

    return ConnectorResponse(
        source="GST_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=gstin.upper(),
        status=status,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/gst-records.json#{gstin.upper()}",
    )
