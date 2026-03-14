# tests/test_utils.py
import pytest
from src.utils import retry_on_exception
from src.exceptions import ScraperException


def test_retry_succeeds_on_first_attempt():
    call_count = 0

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retry_succeeds_after_failures():
    call_count = 0

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"

    result = eventually_successful()
    assert result == "success"
    assert call_count == 3


def test_retry_fails_after_max_retries():
    call_count = 0

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Permanent failure")

    with pytest.raises(ConnectionError, match="Permanent failure"):
        always_fails()

    assert call_count == 3


def test_retry_does_not_retry_non_retryable_errors():
    call_count = 0

    @retry_on_exception(max_retries=3, backoff=[1, 2, 4])
    def raises_value_error():
        nonlocal call_count
        call_count += 1
        raise ValueError("Non-retryable error")

    with pytest.raises(ValueError, match="Non-retryable error"):
        raises_value_error()

    assert call_count == 1
