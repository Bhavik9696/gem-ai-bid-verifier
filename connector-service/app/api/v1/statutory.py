"""
Statutory Connector — GET /api/v1/statutory/{source}/{identifier}

Generic connector for EPFO, ESIC, NSIC, Startup India, BIS, DPIIT, etc.
Looks up by source name and identifier (PAN or registration number).
Returns all matching records for that source+identifier combination.

Example paths:
  /api/v1/statutory/EPFO/AABCA1234F
  /api/v1/statutory/NSIC/AADCB5432G
  /api/v1/statutory/STARTUP_INDIA/AABCA1234F
"""

from fastapi import APIRouter
from app.data.loader import find_statutory
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/statutory/{source}/{identifier}",
    response_model=ConnectorResponse,
    summary="Check statutory compliance (EPFO/ESIC/NSIC/Startup India/etc.)",
)
def check_statutory(source: str, identifier: str) -> ConnectorResponse:
    records = find_statutory(source, identifier)

    source_upper = source.upper()
    id_upper = identifier.upper()

    if not records:
        return ConnectorResponse(
            source=f"{source_upper}_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=id_upper,
            status=ConnectorStatus.NOT_FOUND,
            verifiedFacts={
                "source": source_upper,
                "message": f"No {source_upper} record found for identifier {id_upper}.",
            },
            evidenceReference="demo-data/statutory-records.json",
        )

    # Return the first matching record as the primary result
    record = records[0]

    scenario = record.get("scenario", "VERIFIED")
    status: ConnectorStatus
    if scenario == "NOT_APPLICABLE":
        status = ConnectorStatus.NOT_APPLICABLE
    elif record.get("status") in ("COMPLIANT", "REGISTERED", "VERIFIED"):
        status = ConnectorStatus.VERIFIED
    else:
        status = ConnectorStatus.NOT_FOUND

    # Build facts dict from all record fields except internal keys
    _exclude = {"source", "identifierType", "scenario"}
    verified_facts = {k: v for k, v in record.items() if k not in _exclude}

    return ConnectorResponse(
        source=f"{source_upper}_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=id_upper,
        status=status,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/statutory-records.json#{source_upper}/{id_upper}",
    )
