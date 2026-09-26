import subprocess
import sys
import time
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def live_connector_service():
    """
    Ensures Member 6's dynamic demo connector service (Port 8001) is running
    during the test session. If not already active, launches it and shuts it down
    at session teardown.
    """
    health_url = "http://localhost:8001/health"
    proc = None

    # Check if already running
    already_running = False
    try:
        r = httpx.get(health_url, timeout=0.8)
        if r.status_code == 200:
            already_running = True
    except Exception:
        already_running = False

    if not already_running:
        repo_root = backend_dir.parent
        cs_dir = repo_root / "connector-service"
        proc = subprocess.Popen([sys.executable, "run.py"], cwd=str(cs_dir))

        # Wait for service to be healthy
        started = False
        for _ in range(30):
            time.sleep(0.2)
            try:
                r = httpx.get(health_url, timeout=0.5)
                if r.status_code == 200:
                    started = True
                    break
            except Exception:
                pass

        if not started:
            if proc:
                proc.terminate()
            raise RuntimeError("Could not start connector-service on port 8001 for test session.")

    yield

    if proc is not None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
