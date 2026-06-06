"""Simple application entry point for the dummy target repo."""

from target_repo.utils import calculate_total, format_invoice


def main() -> None:
    """Run a sample invoice calculation."""
    items = [
        {"name": "Widget A", "price": 25, "quantity": 4},
        {"name": "Widget B", "price": 15, "quantity": 2},
        {"name": "Widget C", "price": 50, "quantity": 1},
    ]

    subtotal = sum(item["price"] * item["quantity"] for item in items)
    tax_rate = "0.08"  # BUG: tax_rate should be float, but it's a string

    total = calculate_total(subtotal, tax_rate)
    invoice = format_invoice(items, subtotal, total)
    print(invoice)


if __name__ == "__main__":
    main()
