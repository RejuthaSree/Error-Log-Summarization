"""Tests for signature normalization."""

from errorsum.signature import compute_signature, normalize_message, signature_id


def test_numbers_replaced():
    assert normalize_message("Retrying request 3 of 5") == "Retrying request <NUM> of <NUM>"


def test_floats_replaced():
    assert normalize_message("took 12.5 seconds") == "took <NUM> seconds"


def test_uuid_replaced():
    msg = "id 550e8400-e29b-41d4-a716-446655440000 missing"
    assert normalize_message(msg) == "id <UUID> missing"


def test_ipv4_replaced():
    assert normalize_message("connect to 10.0.0.1 failed") == "connect to <IP> failed"


def test_url_and_email_replaced():
    msg = "GET https://api.example.com/v1/users -> notify ops@example.com"
    assert normalize_message(msg) == "GET <URL> -> notify <EMAIL>"


def test_hex_replaced():
    assert normalize_message("bad frame 0xDEADBEEF") == "bad frame <HEX>"


def test_embedded_timestamp_replaced():
    msg = "connect failed at 2024-03-01 08:15:30"
    assert normalize_message(msg) == "connect failed at <TS>"


def test_file_line_replaced():
    assert normalize_message("error in foo.py:42") == "error in <FILE>"


def test_quoted_string_replaced():
    assert normalize_message("table 'users' missing") == "table <STR> missing"


def test_messages_differing_only_by_volatiles_collapse():
    a, a_id = compute_signature("timeout after 30 seconds on 10.0.0.1")
    b, b_id = compute_signature("timeout after 45 seconds on 10.0.0.2")
    assert a == b
    assert a_id == b_id


def test_signature_id_is_stable_and_short():
    sig = "connection refused"
    assert signature_id(sig) == signature_id(sig)
    assert len(signature_id(sig)) == 12


def test_whitespace_is_collapsed():
    assert normalize_message("  too   many\tspaces  ") == "too many spaces"
