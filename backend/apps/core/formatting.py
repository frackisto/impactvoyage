from decimal import Decimal

CURRENCY_LABELS = {"XOF": "FCFA"}


def format_amount(amount, currency="XOF", language="fr"):
    """125000 → « 125 000 FCFA » ; 12.5 EUR → « 12,50 EUR » ; en anglais « 125,000 FCFA »."""
    decimals = 0 if currency == "XOF" else 2
    text = f"{Decimal(amount):,.{decimals}f}"
    if language != "en":
        text = text.replace(",", " ").replace(".", ",")
    return f"{text} {CURRENCY_LABELS.get(currency, currency)}"
