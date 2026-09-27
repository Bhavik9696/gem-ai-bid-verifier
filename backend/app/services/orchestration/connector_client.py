import logging
from typing import Any, Optional
from datetime import datetime, timezone
import httpx
from app.core.config import settings

logger = logging.getLogger("complianceos.connector_client")


class ConnectorClient:
    """
    HTTP client for calling Member 6's dynamic demo connector service (Port 8001).
    Ensures mode is always DEMO and handles timeouts / unavailable sources gracefully.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.CONNECTOR_API_BASE_URL).rstrip("/")

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {
                        "source": "CONNECTOR_SERVICE",
                        "mode": "DEMO",
                        "identifier": str(params or endpoint.split("/")[-1]),
                        "status": "NOT_FOUND",
                        "verifiedFacts": {},
                        "checkedAt": datetime.now(timezone.utc).isoformat(),
                        "evidenceReference": f"connector-404:{endpoint}",
                    }
                else:
                    logger.warning("Connector service returned %d for %s", response.status_code, url)
                    return {
                        "source": "CONNECTOR_SERVICE",
                        "mode": "DEMO",
                        "identifier": str(params or endpoint.split("/")[-1]),
                        "status": "SOURCE_UNAVAILABLE",
                        "verifiedFacts": {},
                        "checkedAt": datetime.now(timezone.utc).isoformat(),
                        "evidenceReference": f"error-{response.status_code}",
                    }
        except Exception as e:
            logger.error("Failed to connect to connector service at %s: %s", url, e)
            return {
                "source": "CONNECTOR_SERVICE",
                "mode": "DEMO",
                "identifier": str(params or endpoint.split("/")[-1]),
                "status": "SOURCE_UNAVAILABLE",
                "verifiedFacts": {},
                "checkedAt": datetime.now(timezone.utc).isoformat(),
                "evidenceReference": f"connection-failure:{e}",
            }

    async def check_health(self) -> dict[str, Any]:
        return await self._get("/health")

    async def check_gst(self, gstin: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/gst/{gstin}")

    async def check_pan(self, pan: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/pan/{pan}")

    async def check_udyam(self, udyam_number: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/udyam/{udyam_number}")

    async def check_mca(self, cin: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/mca/{cin}")

    async def check_oem(self, auth_number: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/oem/{auth_number}")

    async def check_digilocker(self, document_id: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/digilocker/{document_id}")

    async def check_blacklist(self, pan: str) -> dict[str, Any]:
        return await self._get("/api/v1/blacklist", params={"pan": pan})

    async def check_statutory(self, source: str, identifier: str) -> dict[str, Any]:
        return await self._get(f"/api/v1/statutory/{source}/{identifier}")
