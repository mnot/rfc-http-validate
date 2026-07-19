"""Integration tests for the Markdown and XML extractors."""

from pathlib import Path
from typing import Dict, Optional

from rfc_http_validate.markdown import extract_md
from rfc_http_validate.validate import RfcHttpValidator
from rfc_http_validate.xml import extract_xml

from test.conftest import RecordingUi


def _md(tmp_path: Path, body: str, field_types: Optional[Dict[str, str]] = None) -> RecordingUi:
    path = tmp_path / "draft.md"
    path.write_text(body, encoding="utf-8")
    ui = RecordingUi()
    validator = RfcHttpValidator(field_types or {}, ui)
    with path.open("r", encoding="utf-8") as fh:
        extract_md(fh, validator)
    return ui


def _xml(tmp_path: Path, body: str, field_types: Optional[Dict[str, str]] = None) -> RecordingUi:
    path = tmp_path / "draft.xml"
    path.write_text(body, encoding="utf-8")
    ui = RecordingUi()
    validator = RfcHttpValidator(field_types or {}, ui)
    with path.open("rb") as fh:
        extract_xml(fh, validator)
    return ui


# -- markdown --------------------------------------------------------------


def test_md_validates_http_message_fence(tmp_path: Path) -> None:
    body = "# Title\n\n```http-message\nFoo: 1\n```\n"
    ui = _md(tmp_path, body, {"foo": "item"})
    assert ui.messages("success") == ["valid"]


def test_md_skips_non_http_message_fence(tmp_path: Path) -> None:
    body = "```python\nprint('hi')\n```\n"
    ui = _md(tmp_path, body)
    assert any("not a 'http-message'" in m for m in ui.messages("skip"))
    assert "success" not in ui.kinds()


def test_md_reports_error_in_message(tmp_path: Path) -> None:
    body = "```http-message\nFoo: :::\n```\n"
    ui = _md(tmp_path, body, {"foo": "list"})
    assert ui.kinds().count("error") == 1


# -- xml -------------------------------------------------------------------


def test_xml_validates_sourcecode(tmp_path: Path) -> None:
    body = '<doc><sourcecode type="http-message">\nFoo: 1\n</sourcecode></doc>'
    ui = _xml(tmp_path, body, {"foo": "item"})
    assert ui.messages("success") == ["valid"]


def test_xml_validates_artwork(tmp_path: Path) -> None:
    body = '<doc><artwork type="http-message">\nFoo: 1\n</artwork></doc>'
    ui = _xml(tmp_path, body, {"foo": "item"})
    assert ui.messages("success") == ["valid"]


def test_xml_skips_other_types(tmp_path: Path) -> None:
    body = '<doc><sourcecode type="python">\nprint(1)\n</sourcecode></doc>'
    ui = _xml(tmp_path, body)
    assert any("not a 'http-message'" in m for m in ui.messages("skip"))
    assert "success" not in ui.kinds()


def test_xml_malformed_is_fatal(tmp_path: Path) -> None:
    body = '<doc><sourcecode type="http-message">\nFoo: 1\n'  # unclosed
    ui = _xml(tmp_path, body)
    assert "fatal" in ui.kinds()
