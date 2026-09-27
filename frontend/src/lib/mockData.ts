// ─── Mock data for ComplianceOS prototype ───────────────────────────

export const DEMO_TENDERS = [
  {
    id: "GEM/2025/B/47821",
    title: "Supply of IT Equipment",
    department: "Ministry of Electronics & IT",
    closingDate: "2026-09-30",
    bidderCount: 3,
    status: "Under Evaluation",
    complianceProgress: 78,
    riskSummary: "1 Critical, 1 High, 1 Ready",
  },
  {
    id: "GEM/2025/B/46210",
    title: "Construction of Office Building",
    department: "CPWD",
    closingDate: "2026-10-15",
    bidderCount: 5,
    status: "Published",
    complianceProgress: 0,
    riskSummary: "Evaluation pending",
  },
  {
    id: "GEM/2025/B/44122",
    title: "Medical Equipment Supply",
    department: "Ministry of Health",
    closingDate: "2026-08-20",
    bidderCount: 4,
    status: "Awarded",
    complianceProgress: 100,
    riskSummary: "All compliant",
  },
  {
    id: "GEM/2025/B/43876",
    title: "Vehicle Procurement",
    department: "Ministry of Defence",
    closingDate: "2026-10-05",
    bidderCount: 2,
    status: "Published",
    complianceProgress: 0,
    riskSummary: "Evaluation pending",
  },
  {
    id: "GEM/2025/B/43109",
    title: "Furniture & Fixtures",
    department: "Ministry of Finance",
    closingDate: "2026-09-25",
    bidderCount: 4,
    status: "Under Evaluation",
    complianceProgress: 60,
    riskSummary: "2 Under Review",
  },
];

export const DEMO_TENDER = {
  id: "GEM/2025/B/47821",
  title: "Supply of IT Equipment",
  department: "Ministry of Electronics & IT",
  closingDate: "2026-09-30",
  publishedDate: "2026-08-01",
  estimatedValue: "₹45,00,000",
  category: "Electronics",
  description: "Procurement of laptops, desktops, printers and networking equipment for central government offices.",
  eligibility: [
    "Must be registered on GeM portal",
    "MSME or Udyam registration mandatory",
    "Active GST registration",
    "Make in India – 50% local content mandatory",
    "OEM authorisation letter required",
    "No blacklisting or debarment",
  ],
  clauses: [
    { id: "CLAUSE_4_2", ref: "Clause 4.2, Page 7", text: "GST registration must be active on bid closing date." },
    { id: "CLAUSE_5_1", ref: "Clause 5.1, Page 9", text: "Udyam/MSME registration must be valid." },
    { id: "CLAUSE_6_3", ref: "Clause 6.3, Page 11", text: "OEM authorisation letter must be valid and not expired." },
    { id: "CLAUSE_7_1", ref: "Clause 7.1, Page 12", text: "Make in India local content ≥ 50%." },
    { id: "CLAUSE_8_2", ref: "Clause 8.2, Page 14", text: "No debarment or blacklisting by any government authority." },
  ],
  rulebook: "RULEBOOK-GEM-47821-v1.0",
  bidderCount: 3,
  status: "Under Evaluation",
};

export const DEMO_BIDDERS = [
  {
    id: "BID-001",
    tenderId: "GEM/2025/B/47821",
    legalName: "Aster Tech Private Limited",
    pan: "ABCDE1234F",
    gstin: "33ABCDE1234F1Z5",
    udyamNumber: "UDYAM-TN-01-0001234",
    cin: "U12345TN2022PTC000001",
    address: "Plot 42, SIDCO Industrial Estate, Chennai, TN 600098",
    authorisedSignatory: "Arun Kumar",
    oemRelationship: "Authorised Reseller – Dell Technologies India",
    complianceScore: 100,
    verificationScore: 96,
    riskScore: 8,
    riskLevel: "Low",
    status: "Compliant",
    statusLabel: "Ready for Confirmation",
    conflicts: 0,
    missingDocs: 0,
    flags: [],
  },
  {
    id: "BID-002",
    tenderId: "GEM/2025/B/47821",
    legalName: "Bharat Supplies Private Limited",
    pan: "FGHIJ5678K",
    gstin: "07FGHIJ5678K1Z3",
    udyamNumber: "UDYAM-DL-02-0005678",
    cin: "U67890DL2019PTC000002",
    address: "A-14, Lawrence Road Industrial Area, Delhi, DL 110035",
    authorisedSignatory: "Sunita Mehta",
    oemRelationship: "Authorised Reseller – HP India",
    complianceScore: 82,
    verificationScore: 86,
    riskScore: 61,
    riskLevel: "High",
    status: "High-Risk",
    statusLabel: "Identity Conflict",
    conflicts: 2,
    missingDocs: 0,
    flags: ["GST name mismatch", "PAN entity mismatch"],
  },
  {
    id: "BID-003",
    tenderId: "GEM/2025/B/47821",
    legalName: "Crest Systems Private Limited",
    pan: "KLMNO9012P",
    gstin: "29KLMNO9012P1Z1",
    udyamNumber: null,
    cin: "U22222KA2020PTC000003",
    address: "78, Industrial Layout, Peenya, Bengaluru, KA 560058",
    authorisedSignatory: "Rajesh Nair",
    oemRelationship: "Authorised Reseller – Lenovo India",
    complianceScore: 74,
    verificationScore: 72,
    riskScore: 79,
    riskLevel: "Critical",
    status: "Needs-Clarification",
    statusLabel: "OEM/Udyam Issue",
    conflicts: 1,
    missingDocs: 1,
    flags: ["Udyam certificate missing", "OEM authorisation expired"],
  },
];

export const DEMO_DOCUMENTS = {
  "BID-001": [
    { id: "DOC-001-1", name: "GST Certificate", type: "GST_CERTIFICATE", status: "Extracted", confidence: 98, page: 1, hash: "sha256:a1b2c3d4..." },
    { id: "DOC-001-2", name: "PAN Certificate", type: "PAN_CERTIFICATE", status: "Extracted", confidence: 99, page: 1, hash: "sha256:e5f6g7h8..." },
    { id: "DOC-001-3", name: "Udyam Certificate", type: "UDYAM_CERTIFICATE", status: "Extracted", confidence: 97, page: 1, hash: "sha256:i9j0k1l2..." },
    { id: "DOC-001-4", name: "CIN Document", type: "CIN_DOCUMENT", status: "Extracted", confidence: 95, page: 2, hash: "sha256:m3n4o5p6..." },
    { id: "DOC-001-5", name: "OEM Authorisation Letter", type: "OEM_LETTER", status: "Extracted", confidence: 94, page: 1, hash: "sha256:q7r8s9t0..." },
    { id: "DOC-001-6", name: "Make in India Declaration", type: "MII_DECLARATION", status: "Extracted", confidence: 96, page: 1, hash: "sha256:u1v2w3x4..." },
  ],
  "BID-002": [
    { id: "DOC-002-1", name: "GST Certificate", type: "GST_CERTIFICATE", status: "Conflict Detected", confidence: 97, page: 1, hash: "sha256:y5z6a7b8..." },
    { id: "DOC-002-2", name: "PAN Certificate", type: "PAN_CERTIFICATE", status: "Extracted", confidence: 98, page: 1, hash: "sha256:c9d0e1f2..." },
    { id: "DOC-002-3", name: "Udyam Certificate", type: "UDYAM_CERTIFICATE", status: "Extracted", confidence: 93, page: 1, hash: "sha256:g3h4i5j6..." },
    { id: "DOC-002-4", name: "OEM Authorisation Letter", type: "OEM_LETTER", status: "Extracted", confidence: 91, page: 1, hash: "sha256:k7l8m9n0..." },
  ],
  "BID-003": [
    { id: "DOC-003-1", name: "GST Certificate", type: "GST_CERTIFICATE", status: "Extracted", confidence: 96, page: 1, hash: "sha256:o1p2q3r4..." },
    { id: "DOC-003-2", name: "PAN Certificate", type: "PAN_CERTIFICATE", status: "Extracted", confidence: 98, page: 1, hash: "sha256:s5t6u7v8..." },
    { id: "DOC-003-3", name: "OEM Authorisation Letter", type: "OEM_LETTER", status: "Expired", confidence: 89, page: 1, hash: "sha256:w9x0y1z2..." },
  ],
};

export const DEMO_EXTRACTED_FIELDS = {
  "DOC-001-1": [
    { field: "GSTIN", value: "33ABCDE1234F1Z5", confidence: 98, page: 1 },
    { field: "Legal Name", value: "Aster Tech Private Limited", confidence: 97, page: 1 },
    { field: "Registration Date", value: "2022-04-10", confidence: 95, page: 1 },
    { field: "Status", value: "ACTIVE", confidence: 99, page: 1 },
  ],
  "DOC-001-2": [
    { field: "PAN", value: "ABCDE1234F", confidence: 99, page: 1 },
    { field: "Legal Name", value: "Aster Tech Private Limited", confidence: 98, page: 1 },
    { field: "Date of Issue", value: "2020-06-15", confidence: 94, page: 1 },
  ],
  "DOC-002-1": [
    { field: "GSTIN", value: "07FGHIJ5678K1Z3", confidence: 97, page: 1 },
    { field: "Legal Name", value: "Bharat Trading Corporation Pvt Ltd", confidence: 96, page: 1 },
    { field: "Registration Date", value: "2019-09-01", confidence: 95, page: 1 },
    { field: "Status", value: "ACTIVE", confidence: 99, page: 1 },
  ],
};

export const DEMO_GST_VERIFICATION = {
  "BID-001": { source: "GST_DEMO", mode: "DEMO", gstin: "33ABCDE1234F1Z5", legalName: "Aster Tech Private Limited", status: "ACTIVE", registrationDate: "2022-04-10", returnFilingStatus: "CURRENT", lastReturnPeriod: "2026-08", verificationStatus: "VERIFIED", match: true },
  "BID-002": { source: "GST_DEMO", mode: "DEMO", gstin: "07FGHIJ5678K1Z3", legalName: "Bharat Trading Corporation Pvt Ltd", status: "ACTIVE", registrationDate: "2019-09-01", returnFilingStatus: "CURRENT", lastReturnPeriod: "2026-08", verificationStatus: "VERIFIED", match: false, conflict: "Legal name mismatch: submitted 'Bharat Supplies Private Limited', GST records show 'Bharat Trading Corporation Pvt Ltd'" },
  "BID-003": { source: "GST_DEMO", mode: "DEMO", gstin: "29KLMNO9012P1Z1", legalName: "Crest Systems Private Limited", status: "ACTIVE", registrationDate: "2020-03-15", returnFilingStatus: "CURRENT", lastReturnPeriod: "2026-08", verificationStatus: "VERIFIED", match: true },
};

export const DEMO_PAN_VERIFICATION = {
  "BID-001": { source: "PAN_DEMO", mode: "DEMO", pan: "ABCDE1234F", name: "Aster Tech Private Limited", status: "ACTIVE", verificationStatus: "VERIFIED", match: true },
  "BID-002": { source: "PAN_DEMO", mode: "DEMO", pan: "FGHIJ5678K", name: "Bharat Supplies Private Limited", status: "ACTIVE", verificationStatus: "VERIFIED", match: false, conflict: "GST legal name does not match PAN name" },
  "BID-003": { source: "PAN_DEMO", mode: "DEMO", pan: "KLMNO9012P", name: "Crest Systems Private Limited", status: "ACTIVE", verificationStatus: "VERIFIED", match: true },
};

export const DEMO_UDYAM_VERIFICATION = {
  "BID-001": { source: "UDYAM_DEMO", mode: "DEMO", udyamNumber: "UDYAM-TN-01-0001234", legalName: "Aster Tech Private Limited", pan: "ABCDE1234F", status: "ACTIVE", verificationStatus: "VERIFIED", match: true },
  "BID-002": { source: "UDYAM_DEMO", mode: "DEMO", udyamNumber: "UDYAM-DL-02-0005678", legalName: "Bharat Supplies Private Limited", pan: "FGHIJ5678K", status: "ACTIVE", verificationStatus: "VERIFIED", match: true },
  "BID-003": { source: "UDYAM_DEMO", mode: "DEMO", udyamNumber: null, legalName: null, status: "NOT_FOUND", verificationStatus: "UNAVAILABLE", match: false, conflict: "Udyam registration not found or not submitted" },
};

export const DEMO_OEM_VERIFICATION = {
  "BID-001": { source: "OEM_DEMO", mode: "DEMO", authNumber: "DELL-AUTH-2025-1234", manufacturer: "Dell Technologies India", product: "Laptops & Desktops", validFrom: "2025-01-01", validTo: "2026-12-31", status: "VALID", verificationStatus: "VERIFIED", match: true },
  "BID-002": { source: "OEM_DEMO", mode: "DEMO", authNumber: "HP-AUTH-2024-5678", manufacturer: "HP India", product: "Printers & Laptops", validFrom: "2024-01-01", validTo: "2026-10-31", status: "VALID", verificationStatus: "VERIFIED", match: true },
  "BID-003": { source: "OEM_DEMO", mode: "DEMO", authNumber: "LEN-AUTH-2024-9012", manufacturer: "Lenovo India", product: "Laptops & Tablets", validFrom: "2024-01-01", validTo: "2026-06-30", status: "EXPIRED", verificationStatus: "VERIFIED", match: false, conflict: "OEM authorisation expired on 2026-06-30. Bid closing date: 2026-09-30." },
};

export const DEMO_BLACKLIST_VERIFICATION = {
  "BID-001": { source: "BLACKLIST_DEMO", mode: "DEMO", status: "CLEAR", verificationStatus: "VERIFIED" },
  "BID-002": { source: "BLACKLIST_DEMO", mode: "DEMO", status: "CLEAR", verificationStatus: "VERIFIED" },
  "BID-003": { source: "BLACKLIST_DEMO", mode: "DEMO", status: "CLEAR", verificationStatus: "VERIFIED" },
};

export const DEMO_CONFLICTS = {
  "BID-002": [
    {
      id: "CONF-002-1",
      type: "PAN_GST_MISMATCH",
      severity: "high",
      title: "GST Legal Name ≠ Bid / PAN Entity Name",
      description: "The company name in the GST registration record differs materially from the bidder's submitted legal name and PAN records.",
      bidSubmission: "Bharat Supplies Private Limited",
      sourceRecord: "Bharat Trading Corporation Pvt Ltd",
      source: "GST_DEMO",
      mode: "DEMO",
      evidence: "GST Certificate - Page 1 | GST Source Record",
      relatedRule: "GST_NAME_MATCH",
      recommendation: "Seek clarification on entity identity. Request CIN and fresh GST certificate.",
    },
    {
      id: "CONF-002-2",
      type: "ENTITY_MISMATCH",
      severity: "medium",
      title: "PAN ↔ GSTIN Entity Mismatch",
      description: "GST verified name does not match PAN name, indicating possible registration under a different entity.",
      bidSubmission: "Bharat Supplies Private Limited",
      sourceRecord: "Bharat Trading Corporation Pvt Ltd",
      source: "PAN_DEMO",
      mode: "DEMO",
      evidence: "PAN Certificate - Page 1 | GST_DEMO Record",
      relatedRule: "ENTITY_IDENTITY_MATCH",
      recommendation: "High-risk — officer review required.",
    },
  ],
  "BID-003": [
    {
      id: "CONF-003-1",
      type: "OEM_EXPIRED",
      severity: "high",
      title: "OEM Authorisation Expired Before Bid Closing Date",
      description: "Lenovo OEM authorisation expired on 2026-06-30. Tender closing date is 2026-09-30.",
      bidSubmission: "Valid to: 2026-12-31 (claimed)",
      sourceRecord: "Valid to: 2026-06-30 (OEM registry)",
      source: "OEM_DEMO",
      mode: "DEMO",
      evidence: "OEM Authorisation Letter - Page 1 | OEM Registry",
      relatedRule: "OEM_VALID_ON_CLOSING_DATE",
      recommendation: "OEM authorisation expired. Bidder must submit fresh letter.",
    },
  ],
};

export const DEMO_COMPLIANCE_RULES = {
  "BID-001": [
    { id: "GST_ACTIVE", name: "Active GST Registration", result: "PASS", severity: "mandatory", clause: "Clause 4.2, Page 7", evidence: "GST Certificate, Page 1 + GST_DEMO" },
    { id: "PAN_VALID", name: "Valid PAN", result: "PASS", severity: "mandatory", clause: "Clause 4.4, Page 8", evidence: "PAN Certificate, Page 1 + PAN_DEMO" },
    { id: "UDYAM_VALID", name: "Udyam/MSME Registration", result: "PASS", severity: "mandatory", clause: "Clause 5.1, Page 9", evidence: "Udyam Certificate + UDYAM_DEMO" },
    { id: "OEM_VALID", name: "OEM Authorisation Valid", result: "PASS", severity: "mandatory", clause: "Clause 6.3, Page 11", evidence: "OEM Letter, Page 1 + OEM_DEMO" },
    { id: "MII_COMPLIANCE", name: "Make in India ≥ 50%", result: "PASS", severity: "mandatory", clause: "Clause 7.1, Page 12", evidence: "MII Declaration, Page 1" },
    { id: "BLACKLIST_CLEAR", name: "No Blacklisting/Debarment", result: "PASS", severity: "mandatory", clause: "Clause 8.2, Page 14", evidence: "Blacklist DEMO" },
    { id: "GST_RETURNS_CURRENT", name: "GST Returns Current", result: "PASS", severity: "standard", clause: "Clause 4.3, Page 7", evidence: "GST_DEMO return status" },
    { id: "ENTITY_MATCH", name: "Entity Identity Match", result: "PASS", severity: "standard", clause: "Clause 3.1, Page 5", evidence: "PAN + GST + Udyam cross-check" },
  ],
  "BID-002": [
    { id: "GST_ACTIVE", name: "Active GST Registration", result: "PASS", severity: "mandatory", clause: "Clause 4.2, Page 7", evidence: "GST_DEMO" },
    { id: "PAN_VALID", name: "Valid PAN", result: "PASS", severity: "mandatory", clause: "Clause 4.4, Page 8", evidence: "PAN Certificate, Page 1" },
    { id: "UDYAM_VALID", name: "Udyam/MSME Registration", result: "PASS", severity: "mandatory", clause: "Clause 5.1, Page 9", evidence: "Udyam Certificate + UDYAM_DEMO" },
    { id: "OEM_VALID", name: "OEM Authorisation Valid", result: "PASS", severity: "mandatory", clause: "Clause 6.3, Page 11", evidence: "OEM Letter, Page 1" },
    { id: "MII_COMPLIANCE", name: "Make in India ≥ 50%", result: "PASS", severity: "mandatory", clause: "Clause 7.1, Page 12", evidence: "MII Declaration" },
    { id: "BLACKLIST_CLEAR", name: "No Blacklisting/Debarment", result: "PASS", severity: "mandatory", clause: "Clause 8.2, Page 14", evidence: "Blacklist DEMO" },
    { id: "GST_RETURNS_CURRENT", name: "GST Returns Current", result: "PASS", severity: "standard", clause: "Clause 4.3, Page 7", evidence: "GST_DEMO" },
    { id: "ENTITY_MATCH", name: "Entity Identity Match", result: "FAIL", severity: "mandatory", clause: "Clause 3.1, Page 5", evidence: "PAN + GST cross-check: name mismatch" },
  ],
  "BID-003": [
    { id: "GST_ACTIVE", name: "Active GST Registration", result: "PASS", severity: "mandatory", clause: "Clause 4.2, Page 7", evidence: "GST_DEMO" },
    { id: "PAN_VALID", name: "Valid PAN", result: "PASS", severity: "mandatory", clause: "Clause 4.4, Page 8", evidence: "PAN Certificate, Page 1" },
    { id: "UDYAM_VALID", name: "Udyam/MSME Registration", result: "FAIL", severity: "mandatory", clause: "Clause 5.1, Page 9", evidence: "Udyam not submitted or not found" },
    { id: "OEM_VALID", name: "OEM Authorisation Valid", result: "FAIL", severity: "mandatory", clause: "Clause 6.3, Page 11", evidence: "OEM expired 2026-06-30. Bid close: 2026-09-30." },
    { id: "MII_COMPLIANCE", name: "Make in India ≥ 50%", result: "NEEDS_CLARIFICATION", severity: "mandatory", clause: "Clause 7.1, Page 12", evidence: "Declaration submitted; local content % unverified" },
    { id: "BLACKLIST_CLEAR", name: "No Blacklisting/Debarment", result: "PASS", severity: "mandatory", clause: "Clause 8.2, Page 14", evidence: "Blacklist DEMO" },
    { id: "GST_RETURNS_CURRENT", name: "GST Returns Current", result: "PASS", severity: "standard", clause: "Clause 4.3, Page 7", evidence: "GST_DEMO" },
    { id: "ENTITY_MATCH", name: "Entity Identity Match", result: "PASS", severity: "standard", clause: "Clause 3.1, Page 5", evidence: "PAN + GST match" },
  ],
};

export const DEMO_RECOMMENDATIONS = {
  "BID-001": {
    status: "Compliant",
    label: "Ready for Officer Confirmation",
    color: "green",
    summary: "All mandatory eligibility conditions are met. GST, PAN, Udyam, OEM, and blacklist checks passed. Entity identity verified across all sources. Documents are complete and extraction confidence is high.",
    reasons: [
      "GST registration active on bid closing date.",
      "PAN and entity identity verified.",
      "Udyam/MSME registration confirmed.",
      "OEM authorisation valid through 2026-12-31.",
      "No blacklisting or debarment found.",
      "Make In India compliance declared and consistent.",
    ],
    aiNote: "No anomalies detected. All evidence is consistent and source-verified. Ready for officer confirmation.",
  },
  "BID-002": {
    status: "High-Risk",
    label: "Officer Review Required",
    color: "red",
    summary: "A material identity conflict has been detected. The GST registered legal name differs significantly from the bidder's submitted name and PAN registration. This is a mandatory eligibility gate failure.",
    reasons: [
      "GST legal name 'Bharat Trading Corporation Pvt Ltd' differs from submitted name 'Bharat Supplies Private Limited'.",
      "Entity identity cross-check failed (PAN ↔ GSTIN mismatch).",
      "Possible multiple-entity registration or incorrect GSTIN submitted.",
    ],
    aiNote: "High identity conflict risk. Officer should seek written clarification from the bidder and request fresh GST certificate showing correct registered name.",
  },
  "BID-003": {
    status: "Needs-Clarification",
    label: "Missing / Expired Evidence",
    color: "yellow",
    summary: "Udyam registration is missing and OEM authorisation has expired before the bid closing date. These are mandatory eligibility conditions under the tender rules.",
    reasons: [
      "Udyam certificate not submitted; not found in UDYAM_DEMO registry.",
      "OEM authorisation (Lenovo) expired on 2026-06-30; bid closing date is 2026-09-30.",
      "Make In India local content percentage is declared but unverified.",
    ],
    aiNote: "Bidder must submit valid Udyam certificate and a fresh OEM authorisation letter to proceed. Officer may issue clarification notice.",
  },
};

export const DEMO_AUDIT_EVENTS = [
  { time: "10:02", event: "Bid imported", desc: "BID-001 (Aster Tech) imported from GeM tender GEM/2025/B/47821", actor: "System", type: "import" },
  { time: "10:03", event: "Document hash created", desc: "SHA-256 hash generated for 6 uploaded documents", actor: "System", type: "security" },
  { time: "10:04", event: "OCR completed", desc: "PaddleOCR processed all 6 documents successfully", actor: "AI Engine", type: "ocr" },
  { time: "10:05", event: "GSTIN extracted", desc: "GSTIN 33ABCDE1234F1Z5 extracted with 98% confidence from GST Certificate, Page 1", actor: "AI Engine", type: "extraction" },
  { time: "10:06", event: "GST connector executed", desc: "GST_DEMO connector verified GSTIN. Status: ACTIVE. Mode: DEMO", actor: "Verification Engine", type: "verification" },
  { time: "10:07", event: "All connectors completed", desc: "PAN, Udyam, MCA, OEM, Blacklist connectors executed. No conflicts.", actor: "Verification Engine", type: "verification" },
  { time: "10:08", event: "Rules engine evaluated", desc: "8 rules evaluated. All 8 PASS. Compliance Score: 100%", actor: "Rules Engine", type: "rules" },
  { time: "10:09", event: "Recommendation generated", desc: "AI Recommendation: Compliant — Ready for Officer Confirmation", actor: "AI Engine", type: "recommendation" },
  { time: "10:10", event: "BID-002 (Bharat Supplies) imported", desc: "Documents processed. GST name mismatch detected.", actor: "System", type: "import" },
  { time: "10:11", event: "Identity conflict flagged", desc: "GST legal name 'Bharat Trading Corporation' ≠ submitted name 'Bharat Supplies'. HIGH severity.", actor: "Conflict Engine", type: "conflict" },
  { time: "10:12", event: "Rules evaluated — FAIL", desc: "Rule ENTITY_MATCH failed. Recommendation: High-Risk — Officer Review Required.", actor: "Rules Engine", type: "rules" },
  { time: "10:15", event: "Officer requested clarification", desc: "Procurement Officer initiated clarification notice for BID-002.", actor: "Officer Sharma", type: "officer" },
  { time: "10:20", event: "BID-003 (Crest Systems) imported", desc: "Documents processed. Missing Udyam. OEM expired.", actor: "System", type: "import" },
  { time: "10:21", event: "Missing document detected", desc: "Udyam certificate not submitted. UDYAM_DEMO: NOT_FOUND.", actor: "Verification Engine", type: "conflict" },
  { time: "10:22", event: "OEM expiry conflict", desc: "OEM authorisation expired 2026-06-30. Bid closing: 2026-09-30.", actor: "Conflict Engine", type: "conflict" },
  { time: "10:23", event: "Recommendation generated", desc: "Needs Clarification — Missing / Expired Evidence.", actor: "AI Engine", type: "recommendation" },
];

export const CONNECTORS = [
  { id: "gst", name: "GST / GSTIN", icon: "🧾", mode: "DEMO", status: "OPERATIONAL", desc: "GST registration & return filing status" },
  { id: "pan", name: "PAN / Income Tax", icon: "🆔", mode: "DEMO", status: "OPERATIONAL", desc: "PAN validity and entity name" },
  { id: "udyam", name: "Udyam / MSME", icon: "🏭", mode: "DEMO", status: "OPERATIONAL", desc: "MSME registration and category" },
  { id: "mca", name: "MCA21 / CIN", icon: "🏢", mode: "DEMO", status: "OPERATIONAL", desc: "Company incorporation details" },
  { id: "oem", name: "OEM Authorisation", icon: "✅", mode: "DEMO", status: "OPERATIONAL", desc: "OEM/manufacturer letter validity" },
  { id: "digilocker", name: "DigiLocker", icon: "🔒", mode: "DEMO", status: "OPERATIONAL", desc: "Government-issued document verification" },
  { id: "startup", name: "Startup India / NSIC", icon: "🚀", mode: "DEMO", status: "OPERATIONAL", desc: "Startup India and NSIC registration" },
  { id: "epfo", name: "EPFO / ESIC", icon: "👷", mode: "DEMO", status: "OPERATIONAL", desc: "Labour compliance" },
  { id: "blacklist", name: "Blacklist / Debarment", icon: "🚫", mode: "DEMO", status: "OPERATIONAL", desc: "Government debarment registries" },
];
