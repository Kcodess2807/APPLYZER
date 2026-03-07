import os
from pathlib import Path
import pytest

def _load_env_once():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    root = Path(__file__).resolve().parent.parent
    env_test = root / ".env.test"
    env_default = root / ".env"
    if env_test.exists():
        load_dotenv(env_test, override=False)
    elif env_default.exists():
        load_dotenv(env_default, override=False)

@pytest.fixture(scope="session", autouse=True)
def load_env_for_tests():
    _load_env_once()

@pytest.fixture(autouse=True)
def ensure_dummy_keys(monkeypatch):
    required = [
        "DATABASE_URL", "SECRET_KEY",
        "GROQ_API_KEY", "OPENAI_API_KEY",
        "REED_API_KEY", "ADZUNA_APP_ID", "ADZUNA_APP_KEY",
    ]
    for key in required:
        if not os.getenv(key):
            monkeypatch.setenv(key, "dummy")
    yield