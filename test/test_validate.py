"""Tests for the core RfcHttpValidator logic."""

from test.conftest import run


# -- empty / degenerate messages -------------------------------------------


def test_empty_message_reports_error_without_crashing() -> None:
    ui = run("")
    assert ui.kinds() == ["error"]
    assert "Empty http-message" in ui.messages("error")[0]


def test_newline_only_message_reports_empty() -> None:
    ui = run("\n\n\n")
    assert "Empty http-message" in ui.messages("error")[0]


def test_whitespace_only_message_reports_empty() -> None:
    ui = run("   ")
    assert "Empty http-message" in ui.messages("error")[0]


# -- status lines ----------------------------------------------------------


def test_valid_status_line() -> None:
    ui = run("HTTP/1.1 200 OK\nFoo: bar", {"foo": "list"})
    assert "error" not in ui.kinds()


def test_status_line_wrong_version() -> None:
    ui = run("HTTP/2 200 OK\nFoo: bar")
    assert any("HTTP/1.1" in m for m in ui.messages("error"))


def test_status_line_too_short() -> None:
    ui = run("HTTP/1.1 200")
    assert any("status_code" in m or "status_phrase" in m for m in ui.messages("error"))


def test_non_numeric_status_code() -> None:
    ui = run("HTTP/1.1 XX Nope")
    assert any("Non-numeric status code" in m for m in ui.messages("error"))


def test_status_code_out_of_range() -> None:
    ui = run("HTTP/1.1 700 Nope")
    assert any("out of range" in m for m in ui.messages("error"))


# -- request lines ---------------------------------------------------------


def test_valid_request_line() -> None:
    ui = run("GET / HTTP/1.1\nFoo: bar", {"foo": "list"})
    assert "error" not in ui.kinds()


def test_unknown_method() -> None:
    ui = run("FROB / HTTP/1.1")
    assert any("Method not recognised" in m for m in ui.messages("error"))


def test_request_line_bad_version() -> None:
    ui = run("GET / HTTP/2")
    assert any("HTTP/1.1" in m for m in ui.messages("error"))


def test_request_line_extra_text() -> None:
    ui = run("GET / HTTP/1.1 extra")
    assert any("extra text" in m for m in ui.messages("error"))


def test_request_line_too_short() -> None:
    ui = run("GET /")
    assert any("Request line isn't" in m for m in ui.messages("error"))


def test_start_line_leading_whitespace() -> None:
    ui = run(" GET / HTTP/1.1")
    assert any("starts with whitespace" in m for m in ui.messages("error"))


# -- header-only messages (no start line) ----------------------------------


def test_header_only_message_has_no_start_line_error() -> None:
    # A line whose first token ends in ':' is treated as a header, not a start line.
    ui = run("Foo: 1", {"foo": "item"})
    assert ui.messages("success") == ["valid"]


# -- header combining ------------------------------------------------------


def test_line_folding_is_unfolded() -> None:
    ui = run("Foo: one,\n     two", {"foo": "list"})
    assert "error" not in ui.kinds()
    assert ui.messages("success") == ["valid"]


def test_duplicate_headers_are_combined() -> None:
    # foo: a  and  foo: b  become the list "a, b"
    ui = run("Foo: a\nFoo: b", {"foo": "list"})
    assert ui.messages("success") == ["valid"]


def test_whitespace_in_field_name() -> None:
    ui = run("HTTP/1.1 200 OK\nFo o: bar")
    assert any("Whitespace in field name" in m for m in ui.messages("error"))


def test_first_header_line_leading_whitespace() -> None:
    ui = run("HTTP/1.1 200 OK\n   foo: bar")
    assert any("starts with whitespace" in m for m in ui.messages("error"))


def test_non_field_line() -> None:
    ui = run("HTTP/1.1 200 OK\nnotaheader")
    assert any("Non-field line" in m for m in ui.messages("error"))


def test_body_without_headers() -> None:
    ui = run("HTTP/1.1 200 OK\n\nbody")
    assert any("Body without headers" in m for m in ui.messages("error"))


def test_body_after_headers_is_ignored() -> None:
    ui = run("HTTP/1.1 200 OK\nFoo: 1\n\nsome body\nmore body", {"foo": "item"})
    assert "error" not in ui.kinds()
    assert ui.messages("success") == ["valid"]


# -- structured field type checking ----------------------------------------


def test_valid_structured_item() -> None:
    ui = run("Foo: 1", {"foo": "item"})
    assert ui.messages("success") == ["valid"]


def test_invalid_structured_field_reports_error() -> None:
    ui = run("Foo: :::", {"foo": "list"})
    assert ui.kinds().count("error") == 1


def test_unknown_field_is_skipped() -> None:
    ui = run("Foo: bar")
    assert any("no type information" in m for m in ui.messages("skip"))


# -- RFC 8792 line unwrapping ----------------------------------------------


def test_rfc8792_unwrapping() -> None:
    message = (
        "# NOTE: '\\' line wrapping per RFC 8792\n"
        "\n"
        "Foo: aaaa\\\n"
        "    bbbb\\\n"
        "    cccc\n"
    )
    ui = run(message, {"foo": "item"})
    # The three physical lines unwrap to a single token "aaaabbbbcccc".
    assert ui.messages("success") == ["valid"]
    assert "error" not in ui.kinds()
