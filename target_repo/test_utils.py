"""Tests for the dummy target repo — these SHOULD fail until the bug is fixed."""

import pytest

from target_repo.utils import calculate_total, format_invoice


def test_calculate_total_basic() -> None:
    """calculate_total should return subtotal * (1 + tax_rate)."""
    # This will raise TypeError because tax_rate is a str
    result = calculate_total(100, "0.08")
    assert result == pytest.approx(108.0)


def test_calculate_total_zero_tax() -> None:
    result = calculate_total(50, "0.0")
    assert result == pytest.approx(50.0)


def test_format_invoice() -> None:
    items = [{"name": "Test", "price": 10, "quantity": 2}]
    output = format_invoice(items, 20, 21.6)
    assert "INVOICE" in output
    assert "Subtotal" in output
    assert "21.60" in output
