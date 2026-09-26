import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.entities import Tender, Bidder, Bid, Document, AuditEvent

logger = logging.getLogger("complianceos.seed")

DEFAULT_TENDER = {
    "tenderId": "TENDER-GEM-2026-001",
    "title": "Supply of IT Equipment and Accessories",
    "referenceNumber": "GeM-2026-IT-001",
    "category": "IT Equipment",
    "buyerOrganisation": "Ministry of Electronics and IT",
    "publishedDate": "2026-08-01",
    "bidClosingDate": "2026-09-30",
    "estimatedValue": 5000000.0,
    "currency": "INR",
    "eligibilityConditions": {
        "msmeRequired": True,
        "makeInIndiaRequired": True,
        "localContentThreshold": 50,
        "oemRequired": True,
        "minimumTurnover": 2000000,
    },
    "mandatoryDocuments": [
        "GST Registration Certificate",
        "PAN Card",
        "Udyam/MSME Certificate",
        "OEM Authorisation Letter",
        "Make in India Declaration",
    ],
    "rulebookVersion": "v1.0",
    "status": "ACTIVE",
}

DEFAULT_BIDDERS = [
    {
        "bidderId": "BID-001",
        "legalName": "Aster Tech Private Limited",
        "tradeName": "Aster Tech",
        "pan": "AABCA1234F",
        "gstin": "33AABCA1234F1Z5",
        "udyamNumber": "UDYAM-TN-01-0001234",
        "cin": "U72900TN2018PTC122345",
        "authorisedSignatory": "Arun Kumar",
        "registeredAddress": "12, Anna Salai, Chennai, Tamil Nadu 600002",
        "category": "MSME",
        "scenario": "COMPLIANT",
    },
    {
        "bidderId": "BID-002",
        "legalName": "Bharat Supplies Private Limited",
        "tradeName": "Bharat Supplies",
        "pan": "AADCB5432G",
        "gstin": "07AADCB5432G1ZK",
        "udyamNumber": "UDYAM-DL-02-0005678",
        "cin": "U51909DL2015PTC281234",
        "authorisedSignatory": "Suresh Mehta",
        "registeredAddress": "45, Connaught Place, New Delhi 110001",
        "category": "MSME",
        "scenario": "NAME_CONFLICT",
    },
    {
        "bidderId": "BID-003",
        "legalName": "Crest Systems Private Limited",
        "tradeName": "Crest Systems",
        "pan": "AAHCC7891H",
        "gstin": "29AAHCC7891H1ZT",
        "udyamNumber": None,
        "cin": "U72200KA2020PTC135678",
        "authorisedSignatory": "Priya Sharma",
        "registeredAddress": "78, MG Road, Bengaluru, Karnataka 560001",
        "category": "NON-MSME",
        "scenario": "MISSING_EXPIRED",
    },
]

DEFAULT_BIDS = [
    {
        "bidId": "GEM-BID-2026-001",
        "tenderId": "TENDER-GEM-2026-001",
        "bidderId": "BID-001",
        "submittedAt": "2026-09-10T14:30:00Z",
        "bidAmount": 4750000.0,
        "currency": "INR",
        "status": "SUBMITTED",
        "documents": [
            {"docId": "DOC-001-01", "type": "GST_CERTIFICATE", "filename": "aster_gst_cert.pdf"},
            {"docId": "DOC-001-02", "type": "PAN_CARD", "filename": "aster_pan.pdf"},
            {"docId": "DOC-001-03", "type": "UDYAM_CERTIFICATE", "filename": "aster_udyam.pdf"},
            {"docId": "DOC-001-04", "type": "OEM_AUTHORISATION", "filename": "aster_oem_letter.pdf"},
            {"docId": "DOC-001-05", "type": "MAKE_IN_INDIA_DECLARATION", "filename": "aster_mii_declaration.pdf"},
        ],
    },
    {
        "bidId": "GEM-BID-2026-002",
        "tenderId": "TENDER-GEM-2026-001",
        "bidderId": "BID-002",
        "submittedAt": "2026-09-12T10:15:00Z",
        "bidAmount": 4900000.0,
        "currency": "INR",
        "status": "SUBMITTED",
        "documents": [
            {"docId": "DOC-002-01", "type": "GST_CERTIFICATE", "filename": "bharat_gst_cert.pdf"},
            {"docId": "DOC-002-02", "type": "PAN_CARD", "filename": "bharat_pan.pdf"},
            {"docId": "DOC-002-03", "type": "UDYAM_CERTIFICATE", "filename": "bharat_udyam.pdf"},
            {"docId": "DOC-002-04", "type": "OEM_AUTHORISATION", "filename": "bharat_oem_letter.pdf"},
            {"docId": "DOC-002-05", "type": "MAKE_IN_INDIA_DECLARATION", "filename": "bharat_mii_declaration.pdf"},
        ],
    },
    {
        "bidId": "GEM-BID-2026-003",
        "tenderId": "TENDER-GEM-2026-001",
        "bidderId": "BID-003",
        "submittedAt": "2026-09-15T09:00:00Z",
        "bidAmount": 4600000.0,
        "currency": "INR",
        "status": "SUBMITTED",
        "documents": [
            {"docId": "DOC-003-01", "type": "GST_CERTIFICATE", "filename": "crest_gst_cert.pdf"},
            {"docId": "DOC-003-02", "type": "PAN_CARD", "filename": "crest_pan.pdf"},
            {"docId": "DOC-003-03", "type": "OEM_AUTHORISATION", "filename": "crest_oem_letter_expired.pdf"},
            {"docId": "DOC-003-04", "type": "MAKE_IN_INDIA_DECLARATION", "filename": "crest_mii_declaration.pdf"},
        ],
        "notes": "Udyam certificate NOT submitted. OEM authorisation letter may be expired.",
    },
]


def seed_demo_data(db: Session, force: bool = False) -> None:
    """
    Seeds demo tender, bidders, bids, and documents from backend/demo-data/
    (or fallback records) into the database if they do not already exist.
    """
    demo_dir = settings.DEMO_DATA_DIR
    if not demo_dir.exists():
        alt_dir = Path("backend/demo-data")
        if alt_dir.exists():
            demo_dir = alt_dir

    existing_tenders = db.query(Tender).count()
    if existing_tenders > 0 and not force:
        logger.info("Database already contains %d tenders. Skipping seed.", existing_tenders)
        return

    # 1. Seed Tender
    t_data = DEFAULT_TENDER
    tender_file = demo_dir / "tender.json" if demo_dir.exists() else None
    if tender_file and tender_file.exists():
        try:
            with open(tender_file, "r", encoding="utf-8") as f:
                t_data = json.load(f)
        except Exception:
            pass

    tender = db.query(Tender).filter(Tender.tender_id == t_data["tenderId"]).first()
    if not tender:
        tender = Tender(
            tender_id=t_data["tenderId"],
            title=t_data["title"],
            reference_number=t_data["referenceNumber"],
            category=t_data["category"],
            buyer_organisation=t_data["buyerOrganisation"],
            published_date=t_data.get("publishedDate"),
            bid_closing_date=t_data.get("bidClosingDate"),
            estimated_value=t_data.get("estimatedValue"),
            currency=t_data.get("currency", "INR"),
            eligibility_conditions=t_data.get("eligibilityConditions", {}),
            mandatory_documents=t_data.get("mandatoryDocuments", []),
            rulebook_version=t_data.get("rulebookVersion", "v1.0"),
            status=t_data.get("status", "ACTIVE"),
        )
        db.add(tender)
        db.flush()
        logger.info("Seeded Tender: %s", tender.tender_id)

    # 2. Seed Bidders
    b_list = DEFAULT_BIDDERS
    bidders_file = demo_dir / "bidders.json" if demo_dir.exists() else None
    if bidders_file and bidders_file.exists():
        try:
            with open(bidders_file, "r", encoding="utf-8") as f:
                b_list = json.load(f)
        except Exception:
            pass

    for b_data in b_list:
        bidder = db.query(Bidder).filter(Bidder.bidder_id == b_data["bidderId"]).first()
        if not bidder:
            bidder = Bidder(
                bidder_id=b_data["bidderId"],
                legal_name=b_data["legalName"],
                trade_name=b_data.get("tradeName"),
                pan=b_data["pan"],
                gstin=b_data.get("gstin"),
                udyam_number=b_data.get("udyamNumber"),
                cin=b_data.get("cin"),
                authorised_signatory=b_data.get("authorisedSignatory"),
                registered_address=b_data.get("registeredAddress"),
                category=b_data.get("category", "MSME"),
                scenario=b_data.get("scenario"),
            )
            db.add(bidder)
    db.flush()
    logger.info("Seeded %d Bidders", len(b_list))

    # 3. Seed Bids and Documents
    bids_list = DEFAULT_BIDS
    bids_file = demo_dir / "gem-bids.json" if demo_dir.exists() else None
    if bids_file and bids_file.exists():
        try:
            with open(bids_file, "r", encoding="utf-8") as f:
                bids_list = json.load(f)
        except Exception:
            pass

    for bid_data in bids_list:
        bid = db.query(Bid).filter(Bid.bid_id == bid_data["bidId"]).first()
        if not bid:
            bid = Bid(
                bid_id=bid_data["bidId"],
                tender_id=bid_data["tenderId"],
                bidder_id=bid_data["bidderId"],
                submitted_at=bid_data.get("submittedAt"),
                bid_amount=bid_data.get("bidAmount", 0.0),
                currency=bid_data.get("currency", "INR"),
                status=bid_data.get("status", "SUBMITTED"),
                notes=bid_data.get("notes"),
            )
            db.add(bid)
            db.flush()

            for doc_data in bid_data.get("documents", []):
                doc = Document(
                    doc_id=doc_data["docId"],
                    bid_id=bid.bid_id,
                    doc_type=doc_data["type"],
                    filename=doc_data["filename"],
                    file_hash=f"sha256-demo-{doc_data['docId'].lower()}",
                    status="UPLOADED",
                )
                db.add(doc)

            audit = AuditEvent(
                bid_id=bid.bid_id,
                event_type="BID_INGESTED",
                actor="SYSTEM",
                details={
                    "message": f"Bid {bid.bid_id} imported from GeM data source.",
                    "documentsCount": len(bid_data.get("documents", [])),
                },
            )
            db.add(audit)

    db.commit()
    logger.info("Seeded %d Bids and associated documents.", len(bids_list))
