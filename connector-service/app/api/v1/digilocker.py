"""
DigiLocker Document Origin Connector — GET /api/v1/digilocker/{documentId}

Simulates issuer-verified document origin lookup (DigiLocker-ready boundary).
All results carry mode=DEMO and evidenceReference so the dashboard can display
document lineage without claiming live DigiLocker API access.
"""

from fastapi import APIRouter
from app.data.loader import find_digilocker
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/digilocker/{document_id}",
    response_model=ConnectorResponse,
    summary="Verify document origin via DigiLocker-ready issuer simulation",
)
def verify_digilocker(document_id: str) -> ConnectorResponse:
    record = find_digilocker(document_id)

    if record is None:
        return ConnectorResponse(
            source="DIGILOCKER_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=document_id,
            status=ConnectorStatus.NOT_FOUND,
            verifiedFacts={},
            evidenceReference="demo-data/digilocker-records.json",
        )

    verified_facts = {
        "issuerId": record.get("issuerId"),
        "issuerName": record.get("issuerName"),
        "documentType": record.get("documentType"),
        "linkedIdentifier": record.get("linkedIdentifier"),
        "holderName": record.get("holderName"),
        "issueDate": record.get("issueDate"),
        "expiryDate": record.get("expiryDate"),
        "verificationStatus": record.get("verificationStatus"),
        "documentHash": record.get("documentHash"),
        "digilockerReady": record.get("digilockerReady", False),
        "conflictNote": record.get("conflictNote"),
    }

    # Surface name mismatch scenario from record
    status = ConnectorStatus.VERIFIED
    if record.get("scenario") == "NAME_MISMATCH":
        status = ConnectorStatus.MISMATCH

    return ConnectorResponse(
        source="DIGILOCKER_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=document_id,
        status=status,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/digilocker-records.json#{document_id}",
    )
