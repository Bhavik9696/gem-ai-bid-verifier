# ComplianceOS API Contract

## Core API — Port 8000

- GET `/api/tenders`
- GET `/api/tenders/{tenderId}`
- GET `/api/tenders/{tenderId}/bids`
- POST `/api/bids/{bidId}/run-verification`
- GET `/api/bids/{bidId}/assessment`
- POST `/api/bids/{bidId}/decision`
- GET `/api/bids/{bidId}/audit-events`

## Connector API — Port 8001

- GET `/api/v1/gst/{gstin}`
- GET `/api/v1/pan/{pan}`
- GET `/api/v1/udyam/{udyamNumber}`
- GET `/api/v1/mca/{cin}`
- GET `/api/v1/oem/{authorisationNumber}`
- GET `/api/v1/digilocker/{documentId}`
- GET `/api/v1/blacklist?pan={pan}`