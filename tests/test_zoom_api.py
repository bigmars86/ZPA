"""Offline Zoom authentication, transport and response-report regressions."""

import json
import urllib.error
import urllib.request
from io import BytesIO
from unittest.mock import MagicMock

import pytest

from zpa.core.zoom_api import ZoomAPI, resolve_proxy


def response(payload):
    result = MagicMock()
    result.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return result


def client():
    api = ZoomAPI("example", "example", "example", timeout=12)
    api.opener = MagicMock()
    return api


def test_token_reused_and_refreshed_before_expiry(monkeypatch):
    monkeypatch.setattr("zpa.core.zoom_api.time.monotonic", lambda: 100)
    api = client()
    api.opener.open.side_effect = [
        response({"access_token": "first", "expires_in": 3600}),
        response({"questions": []}),
        response({"questions": []}),
        response({"access_token": "second", "expires_in": 3600}),
        response({"questions": []}),
    ]
    api.get_poll_results("123")
    api.get_poll_results("123")
    assert api.opener.open.call_count == 3
    monkeypatch.setattr("zpa.core.zoom_api.time.monotonic", lambda: 3700)
    api.get_poll_results("123")
    assert api.access_token == "second"  # noqa: S105
    assert all(call.kwargs["timeout"] == 12 for call in api.opener.open.call_args_list)


def test_unauthorized_retried_once():
    api = client()
    api.opener.open.side_effect = [
        response({"access_token": "first", "expires_in": 3600}),
        urllib.error.HTTPError("https://api.zoom.us", 401, "expired", {}, BytesIO()),
        response({"access_token": "second", "expires_in": 3600}),
        urllib.error.HTTPError("https://api.zoom.us", 401, "denied", {}, BytesIO()),
    ]
    with pytest.raises(urllib.error.HTTPError):
        api.get_poll_results("123")
    assert api.opener.open.call_count == 4


def test_poll_results_use_report_only():
    api = client()
    api.make_api_request = MagicMock(return_value={"questions": []})
    assert api.get_poll_results("123") == {"questions": []}
    api.make_api_request.assert_called_once_with(
        "https://api.zoom.us/v2/report/meetings/123/polls"
    )
    api.make_api_request.return_value = {"polls": []}
    with pytest.raises(ValueError):
        api.get_poll_results("123")


def test_no_proxy_ignores_environment(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://example.invalid:8080")
    monkeypatch.setenv("https_proxy", "http://example.invalid:8080")
    api = ZoomAPI("example", "example", "example", proxy=resolve_proxy(False))
    assert not any(
        isinstance(handler, urllib.request.ProxyHandler)
        for handler in api.opener.handlers
    )


def test_proxy_modes(monkeypatch):
    monkeypatch.setattr(
        urllib.request, "getproxies", lambda: {"https": "http://auto.invalid:8080"}
    )
    assert resolve_proxy(False) is None
    assert resolve_proxy(True) == "http://auto.invalid:8080"
    assert (
        resolve_proxy(False, "http://manual.invalid:8080")
        == "http://manual.invalid:8080"
    )


def test_untrusted_url_rejected_before_authentication():
    api = client()
    with pytest.raises(ValueError):
        api.make_api_request("https://example.invalid/")
    api.opener.open.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("timed out"),
        urllib.error.HTTPError("https://api.zoom.us", 403, "forbidden", {}, BytesIO()),
    ],
    ids=["timeout", "forbidden"],
)
def test_other_failures_are_not_retried(error):
    api = client()
    api.opener.open.side_effect = [
        response({"access_token": "first", "expires_in": 3600}),
        error,
    ]
    with pytest.raises(type(error)):
        api.get_poll_results("123")
    assert api.opener.open.call_count == 2


def test_xml_export_round_trip(tmp_path):
    import xml.etree.ElementTree as ET

    from zpa.core.export_manager import ExportManager

    path = tmp_path / "report.xml"
    assert ExportManager().export_to_xml(
        [{"name": "<Person & name>", "answer": "1"}], str(path)
    )
    assert ET.parse(path).findtext("data/record/name") == "<Person & name>"  # noqa: S314
