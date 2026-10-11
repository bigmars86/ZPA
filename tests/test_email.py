"""Email markup and provider-independent TLS policy."""

import importlib
import ssl
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from zpa.main import DataLoadWorker, ZoomPollAnalyzer


def window(settings=None):
    return SimpleNamespace(
        meeting_data={"topic": '<img src="https://example.invalid/pixel">'},
        _meeting_datetime_display=lambda: "<date>",
        translations=SimpleNamespace(get=lambda key: key),
        settings_manager=SimpleNamespace(load_settings=lambda: settings or {}),
        processed_data=[
            {"Name": "<b>Person & name</b>", "Poll Answer": "<script>bad</script>"}
        ],
        status_label=MagicMock(),
        update_status_info=MagicMock(),
        build_email_html=lambda: "<html>Safe report</html>",
        email_sent=False,
    )


def test_external_content_is_escaped():
    html = ZoomPollAnalyzer.build_email_html(window())
    assert "<img" not in html
    assert "<script>" not in html
    assert "&lt;img" in html
    assert "&lt;b&gt;Person &amp; name&lt;/b&gt;" in html
    assert "&lt;date&gt;" in html


@pytest.mark.parametrize("starttls", [True, False])
@pytest.mark.parametrize("invalid_certificate", [True, False])
def test_email_validates_tls_before_credentials(
    monkeypatch, starttls, invalid_certificate
):
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    constructor = MagicMock(return_value=smtp)
    module = importlib.import_module("zpa.main")
    monkeypatch.setattr(module.smtplib, "SMTP", constructor)
    monkeypatch.setattr(module.smtplib, "SMTP_SSL", constructor)
    monkeypatch.setattr(module.QApplication, "processEvents", lambda: None)
    dialogs = MagicMock()
    monkeypatch.setattr(module, "QMessageBox", dialogs)
    if invalid_certificate:
        error = ssl.SSLCertVerificationError("certificate rejected")
        if starttls:
            smtp.starttls.side_effect = error
        else:
            constructor.side_effect = error
    fixture = window(
        {
            "email_recipients": ["recipient@example.invalid"],
            "smtp_server": "smtp.example.invalid",
            "smtp_port": 587 if starttls else 465,
            "smtp_username": "sender@example.invalid",
            "smtp_password": "example",
            "smtp_use_tls": starttls,
        }
    )
    ZoomPollAnalyzer.send_email(fixture)
    context = (
        smtp.starttls.call_args.kwargs["context"]
        if starttls
        else constructor.call_args.kwargs["context"]
    )
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
    if invalid_certificate:
        smtp.login.assert_not_called()
        smtp.sendmail.assert_not_called()
        dialogs.critical.assert_called_once()
        assert not fixture.email_sent
    else:
        smtp.login.assert_called_once()
        smtp.sendmail.assert_called_once()
        assert fixture.email_sent


def test_poll_error_reaches_worker_error_signal():
    api = MagicMock()
    api.get_poll_results.side_effect = TimeoutError("report request timed out")
    fixture = SimpleNamespace(
        debug=False,
        meeting_id="123",
        meeting_uuid=None,
        zoom_api=api,
        progress=MagicMock(),
        finished=MagicMock(),
        error=MagicMock(),
    )
    DataLoadWorker.run(fixture)
    fixture.error.emit.assert_called_once_with("report request timed out")
    fixture.finished.emit.assert_not_called()
