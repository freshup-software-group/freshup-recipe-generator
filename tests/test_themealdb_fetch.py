"""Tests for fetch_all_meals(). urlopen is mocked, so no network is used."""
import io
import json
import string
from pathlib import Path
from unittest import mock
from urllib.error import URLError

import pytest

from app.themealdb import (
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
    TheMealDBError,
    fetch_all_meals,
)

SAMPLE_PATH = Path(__file__).parent / "data" / "themealdb_sample.json"
NO_MEALS = b'{"meals": null}'


def fake_urlopen(responses):
    """Return a urlopen stand-in answering from {letter: bytes or exception}.

    Letters not in responses get {"meals": null}, as the real API does.
    """
    def _urlopen(request, timeout):
        letter = request.full_url.rsplit("f=", 1)[1]
        answer = responses.get(letter, NO_MEALS)
        if isinstance(answer, Exception):
            raise answer
        return io.BytesIO(answer)  # BytesIO supports read() and "with", like a response
    return _urlopen


def test_returns_meals_from_all_letters():
    sample = SAMPLE_PATH.read_bytes()
    with mock.patch("app.themealdb.urlopen", side_effect=fake_urlopen({"b": sample})):
        meals = fetch_all_meals()
    assert [meal["idMeal"] for meal in meals] == ["52767", "53150", "99990001"]


def test_requests_every_letter_with_timeout_and_user_agent():
    with mock.patch("app.themealdb.urlopen", side_effect=fake_urlopen({})) as urlopen:
        assert fetch_all_meals() == []

    requests = [call.args[0] for call in urlopen.call_args_list]
    assert [r.full_url[-1] for r in requests] == list(string.ascii_lowercase)
    assert all(r.full_url.startswith("https://www.themealdb.com/api/json/v1/1/")
               for r in requests)
    # urllib stores header names capitalized this way ("User-agent").
    assert all(r.get_header("User-agent") == USER_AGENT for r in requests)
    assert all(call.kwargs["timeout"] == REQUEST_TIMEOUT_SECONDS
               for call in urlopen.call_args_list)


def test_unreachable_api_raises_clear_error():
    responses = {"a": URLError("Name or service not known")}
    with mock.patch("app.themealdb.urlopen", side_effect=fake_urlopen(responses)):
        with pytest.raises(TheMealDBError, match="Could not reach TheMealDB.*f=a"):
            fetch_all_meals()


def test_failure_on_a_later_letter_returns_nothing():
    # All or nothing: letters a-p succeed, q times out, so no meals come back.
    sample = SAMPLE_PATH.read_bytes()
    responses = {"b": sample, "q": TimeoutError("timed out")}
    with mock.patch("app.themealdb.urlopen", side_effect=fake_urlopen(responses)) as urlopen:
        with pytest.raises(TheMealDBError, match="f=q"):
            fetch_all_meals()
    assert urlopen.call_count == 17  # stopped at q, did not keep going


def test_invalid_json_raises_clear_error():
    with mock.patch("app.themealdb.urlopen", side_effect=fake_urlopen({"a": b"<html>"})):
        with pytest.raises(TheMealDBError, match="invalid JSON"):
            fetch_all_meals()


@pytest.mark.parametrize("payload", [[], {"other": 1}, {"meals": "oops"}])
def test_unexpected_response_shape_raises_error(payload):
    body = json.dumps(payload).encode()
    with mock.patch("app.themealdb.urlopen", side_effect=fake_urlopen({"a": body})):
        with pytest.raises(TheMealDBError, match="unexpected response"):
            fetch_all_meals()
