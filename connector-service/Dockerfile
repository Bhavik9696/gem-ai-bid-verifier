# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL maintainer="Member 6 — ComplianceOS Connector Service"
LABEL description="Dynamic Demo Connector Service — port 8001"

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source
COPY . .

EXPOSE 8001

CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8001"]
