"""
MCA/CIN Connector — GET /api/v1/mca/{cin}

Looks up a Company Identification Number in the demo MCA21 source records.
"""

from fastapi import APIRouter
from app.data.loader import find_mca
from app.validators import validate_cin
from app.schemas.connector import ConnectorResponse, ConnectorMode, ConnectorStatus

router = APIRouter()


@router.get(
    "/mca/{cin}",
    response_model=ConnectorResponse,
    summary="Verify a CIN/LLPIN against demo MCA21 source data",
)
def verify_mca(cin: str) -> ConnectorResponse:
    cin = validate_cin(cin)
    record = find_mca(cin)

    if record is None:
        return ConnectorResponse(
            source="MCA_DEMO",
            mode=ConnectorMode.DEMO,
            identifier=cin.upper(),
            status=ConnectorStatus.NOT_FOUND,
            verifiedFacts={},
            evidenceReference="demo-data/mca-records.json",
        )

    verified_facts = {
        "companyName": record["companyName"],
        "pan": record["pan"],
        "companyStatus": record["companyStatus"],
        "dateOfIncorporation": record.get("dateOfIncorporation"),
        "registeredAddress": record.get("registeredAddress"),
        "companyCategory": record.get("companyCategory"),
        "companySubCategory": record.get("companySubCategory"),
        "classOfCompany": record.get("classOfCompany"),
        "authorisedCapital": record.get("authorisedCapital"),
        "paidUpCapital": record.get("paidUpCapital"),
        "lastAGMDate": record.get("lastAGMDate"),
        "lastFilingDate": record.get("lastFilingDate"),
        "directors": record.get("directors", []),
    }

    return ConnectorResponse(
        source="MCA_DEMO",
        mode=ConnectorMode.DEMO,
        identifier=cin.upper(),
        status=ConnectorStatus.VERIFIED,
        verifiedFacts=verified_facts,
        evidenceReference=f"demo-data/mca-records.json#{cin.upper()}",
    )
