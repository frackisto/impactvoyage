from decimal import Decimal

CURRENCY_LABELS = {"XOF": "FCFA"}


def format_amount(amount, currency="XOF"):
    """125000 → « 125 000 FCFA » ; 12.5 EUR → « 12,50 EUR »."""
    decimals = 0 if currency == "XOF" else 2
    text = f"{Decimal(amount):,.{decimals}f}".replace(",", " ").replace(".", ",")
    return f"{text} {CURRENCY_LABELS.get(currency, currency)}"
