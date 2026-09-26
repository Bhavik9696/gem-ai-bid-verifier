"""
Blacklist / Debarment Connector — GET /api/v1/blacklist?pan={pan}

Checks whether a PAN appears on the debarment/blacklist registry.
None of the three demo bidders are blacklisted; the list contains
fictional PANs that can be used to test the BLACKLISTED flow.
"""

from fastapi import APIRouter, Query
from app.data.loader import find_blacklist_by_pan
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/blacklist",
    response_model=ConnectorResponse,
    summary="Check blacklist/debarment registry by PAN",
)
def check_blacklist(
    pan: str = Query(..., description="PAN to check against debarment registry"),
) -> ConnectorResponse:
    record = find_blacklist_by_pan(pan)

    if record is None:
        return ConnectorResponse(
            source="BLACKLIST_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=pan.upper(),
            status=ConnectorStatus.VERIFIED,   # Not found = clean / not blacklisted
            verifiedFacts={
                "blacklisted": False,
                "message": "No debarment or blacklist entry found for this PAN.",
            },
            evidenceReference="demo-data/blacklist-records.json",
        )

    verified_facts = {
        "blacklisted": True,
        "entityName": record.get("entityName"),
        "listType": record.get("listType"),
        "listedBy": record.get("listedBy"),
        "listedDate": record.get("listedDate"),
        "reason": record.get("reason"),
        "orderReference": record.get("orderReference"),
        "validUpto": record.get("validUpto"),
    }

    return ConnectorResponse(
        source="BLACKLIST_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=pan.upper(),
        status=ConnectorStatus.BLACKLISTED,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/blacklist-records.json#{pan.upper()}",
    )
