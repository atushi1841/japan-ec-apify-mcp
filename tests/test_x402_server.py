#!/usr/bin/env python3
"""Test script for mcp_x402_server.py — verifies x402 protocol signals and tool execution."""

import json
import sys
from pathlib import Path

# Add scripts dir to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import mcp_x402_server as srv
from mcp_x402_server import (
    build_payment_required,
    verify_x402_payment,
    DEFAULT_PRICE_USDC_ATOMIC,
    DEFAULT_PAY_TO,
)


def test_build_payment_required():
    req = build_payment_required(
        resource_url="mcp://test/tool",
        description="Test search",
        amount_atomic="1000",
    )
    assert req["x402Version"] == 2
    assert len(req["accepts"]) == 1
    assert req["accepts"][0]["scheme"] == "exact"
    assert req["accepts"][0]["amount"] == "1000"
    assert req["accepts"][0]["network"] == "eip155:84532"
    print("✓ test_build_payment_required")


def test_verify_payment_invalid():
    valid, reason, _ = verify_x402_payment(
        {"x402Version": 2, "scheme": "exact", "accepted": {"amount": "9999", "payTo": DEFAULT_PAY_TO}},
        expected_amount_atomic="1000",
        expected_pay_to=DEFAULT_PAY_TO,
    )
    assert not valid
    assert "Amount mismatch" in reason
    print("✓ test_verify_payment_invalid (amount mismatch)")


def test_verify_payment_missing_sig():
    valid, reason, _ = verify_x402_payment(
        {"x402Version": 2, "scheme": "exact", "accepted": {"amount": "1000", "payTo": DEFAULT_PAY_TO}},
        expected_amount_atomic="1000",
        expected_pay_to=DEFAULT_PAY_TO,
    )
    assert not valid
    assert "Missing payment signature" in reason
    print("✓ test_verify_payment_missing_sig")


def test_verify_payment_bad_scheme():
    valid, reason, _ = verify_x402_payment(
        {"x402Version": 2, "scheme": "upto", "accepted": {"amount": "1000", "payTo": DEFAULT_PAY_TO}},
        expected_amount_atomic="1000",
        expected_pay_to=DEFAULT_PAY_TO,
    )
    assert not valid
    assert "Unsupported scheme" in reason
    print("✓ test_verify_payment_bad_scheme")


def test_verify_payment_bad_payto():
    valid, reason, _ = verify_x402_payment(
        {"x402Version": 2, "scheme": "exact", "accepted": {"amount": "1000", "payTo": "0x0000000000000000000000000000000000000000"}},
        expected_amount_atomic="1000",
        expected_pay_to=DEFAULT_PAY_TO,
    )
    assert not valid
    assert "PayTo mismatch" in reason
    print("✓ test_verify_payment_bad_payto")


def test_verify_payment_bad_version():
    valid, reason, _ = verify_x402_payment(
        {"x402Version": 1, "scheme": "exact", "accepted": {"amount": "1000", "payTo": DEFAULT_PAY_TO}},
        expected_amount_atomic="1000",
        expected_pay_to=DEFAULT_PAY_TO,
    )
    assert not valid
    assert "Unsupported x402 version" in reason
    print("✓ test_verify_payment_bad_version")


def test_tool_raises_toolerror_on_unpaid_call():
    """Calling the tool without payment must raise ToolError carrying the
    x402 PaymentRequired JSON (canonical FastMCP error shape)."""
    import asyncio
    from fastmcp.exceptions import ToolError

    try:
        asyncio.run(srv.search_mercari_japan(keyword="CBR250RR", _meta=None))
    except ToolError as e:
        payload = json.loads(str(e))
        assert payload["x402Version"] == 2
        assert payload["error"] == "Payment required to call this tool"
        assert payload["accepts"][0]["amount"] == DEFAULT_PRICE_USDC_ATOMIC
        print("✓ test_tool_raises_toolerror_on_unpaid_call")
        return
    raise AssertionError("expected ToolError, got return value")


def test_tool_raises_toolerror_on_invalid_payment():
    """A malformed payment payload must raise ToolError with the Invalid signal."""
    import asyncio
    from fastmcp.exceptions import ToolError

    bad = {
        "x402Version": 2,
        "scheme": "exact",
        "accepted": {"amount": "9999", "payTo": DEFAULT_PAY_TO},
        "payload": {"signature": "0xdeadbeef"},
    }
    try:
        asyncio.run(srv.search_mercari_japan(keyword="CBR250RR", _meta={"x402/payment": bad}))
    except ToolError as e:
        payload = json.loads(str(e))
        assert payload["error"].startswith("Payment Invalid")
        assert "Amount mismatch" in payload["error"]
        print("✓ test_tool_raises_toolerror_on_invalid_payment")
        return
    raise AssertionError("expected ToolError, got return value")


def main():
    print("Running mcp_x402_server tests...")
    test_build_payment_required()
    test_verify_payment_invalid()
    test_verify_payment_missing_sig()
    test_verify_payment_bad_scheme()
    test_verify_payment_bad_payto()
    test_verify_payment_bad_version()
    test_tool_raises_toolerror_on_unpaid_call()
    test_tool_raises_toolerror_on_invalid_payment()
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    main()