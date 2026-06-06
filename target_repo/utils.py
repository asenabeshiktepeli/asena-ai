"""Utility functions for the dummy target repo.

This module contains a **deliberate bug** in ``calculate_total`` that
the multi-agent pipeline is expected to detect and fix.
"""


def calculate_total(subtotal: int, tax_rate: str) -> float:
    """Calculate the total price including tax.

    Parameters
    ----------
    subtotal : int
        The pre-tax subtotal.
    tax_rate : str
        The tax rate as a string (e.g. "0.08").

    Returns
    -------
    float
        The total after applying tax.

    .. note::
        **DELIBERATE BUG** — ``tax_rate`` is typed as ``str`` but used
        directly in arithmetic.  The correct fix is to cast it to float.
    """
    # BUG: tax_rate is a string, this will raise TypeError
    return subtotal + subtotal * tax_rate


def format_invoice(
    items: list[dict],
    subtotal: int,
    total: float,
) -> str:
    """Format a human-readable invoice string."""
    lines = ["=" * 40, "INVOICE", "=" * 40]
    for item in items:
        line = f"  {item['name']:<20} {item['quantity']:>3} x ${item['price']:>6} = ${item['price'] * item['quantity']:>8}"
        lines.append(line)
    lines.append("-" * 40)
    lines.append(f"  {'Subtotal':<30} ${subtotal:>8}")
    lines.append(f"  {'Total':<30} ${total:>8.2f}")
    lines.append("=" * 40)
    return "\n".join(lines)
