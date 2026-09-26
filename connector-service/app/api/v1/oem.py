"""
OEM Authorisation Connector — GET /api/v1/oem/{authorisationNumber}

Looks up an OEM authorisation letter by its reference number.
Returns EXPIRED for Crest Systems (expired letter) or VALID for others.
"""

from fastapi import APIRouter
from app.data.loader import find_oem
from app.validators import validate_oem_ref
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/oem/{authorisation_number}",
    response_model=ConnectorResponse,
    summary="Verify an OEM authorisation letter reference number",
)
def verify_oem(authorisation_number: str) -> ConnectorResponse:
    authorisation_number = validate_oem_ref(authorisation_number)
    record = find_oem(authorisation_number)

    if record is None:
        return ConnectorResponse(
            source="OEM_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=authorisation_number,
            status=ConnectorStatus.NOT_FOUND,
            verifiedFacts={},
            evidenceReference="demo-data/oem-authorisations.json",
        )

    verified_facts = {
        "authorisedEntity": record["authorisedEntity"],
        "authorisedEntityPAN": record.get("authorisedEntityPAN"),
        "oemName": record["oemName"],
        "oemPAN": record.get("oemPAN"),
        "productCategory": record.get("productCategory"),
        "authorisedProducts": record.get("authorisedProducts", []),
        "issueDate": record.get("issueDate"),
        "expiryDate": record.get("expiryDate"),
        "oemStatus": record["status"],
        "letterReference": record.get("letterReference"),
        "contactPerson": record.get("contactPerson"),
        "conflictNote": record.get("conflictNote"),
    }

    status = (
        ConnectorStatus.EXPIRED
        if record.get("status") == "EXPIRED"
        else ConnectorStatus.VERIFIED
    )

    return ConnectorResponse(
        source="OEM_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=authorisation_number,
        status=status,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/oem-authorisations.json#{authorisation_number}",
    )
