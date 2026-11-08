import pytest
from app.main import _IP_REQUEST_TIMESTAMPS


@pytest.fixture(autouse=True)
def reset_rate_limit_timestamps():
    """Reset IP request timestamps between test cases to prevent test-suite rate limiting."""
    _IP_REQUEST_TIMESTAMPS.clear()
