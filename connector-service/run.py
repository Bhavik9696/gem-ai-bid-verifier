"""
ComplianceOS — Dynamic Demo Connector Service
Port: 8001
Owner: Member 6

This service acts as the source-integration boundary for the prototype.
Every connector looks up identifiers dynamically in seeded source data.
Results are always labelled mode=DEMO so prototype data is never
mistaken for live government portal results.
"""

import uvicorn
from app.main import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8001, reload=True)
