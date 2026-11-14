import pytest
from app.main import _IP_REQUEST_TIMESTAMPS


@pytest.fixture(autouse=True)
def reset_rate_limit_timestamps():
    """Reset IP request timestamps between test cases to prevent test-suite rate limiting."""
    _IP_REQUEST_TIMESTAMPS.clear()


def ter(scheme_id: str) -> str:
    """Current TER from the fact store; the daily refresh moves it, so tests must not hard-code it."""
    from app.rag.facts import get_fact_from_db
    return get_fact_from_db(scheme_id, "ter_direct")["value"]
