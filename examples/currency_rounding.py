#!/usr/bin/env python3
"""Convert and round money for a static bilingual page.

Two rules make the output readable. The rate is a constant, because a static
page cannot show a number that changes between two visits. Rounding depends
on magnitude, so a converted figure reads as an estimate instead of a
spreadsheet cell. Payback is derived from the converted price, which means
two locales can legitimately disagree.

Usage:
    python3 currency_rounding.py
"""

RATE = 4.00  # fictional units of local currency per dollar

# magnitude ceiling -> rounding step
BANDS = ((1_000, 10), (10_000, 100), (100_000, 1_000), (1_000_000, 10_000))
TOP_STEP = 50_000


def round_banded(value: float) -> int:
    """Round to the step that matches the magnitude of the value."""
    for ceiling, step in BANDS:
        if value < ceiling:
            return int(round(value / step) * step)
    return int(round(value / TOP_STEP) * TOP_STEP)


def to_dollars(local: float) -> int:
    return round_banded(local / RATE)


def to_local(dollars: float) -> int:
    return round_banded(dollars * RATE)


def money(value: int, locale: str) -> str:
    """Thousands separator follows the locale, not the currency."""
    if locale == "pt":
        return "R$ " + f"{value:,}".replace(",", ".")
    return "US$ " + f"{value:,}"


def payback_months(price: int, monthly_saving: int) -> int:
    """Months until the hardware pays for itself, in the page's currency."""
    return int(round(price / monthly_saving))


CASES = [
    # local price, monthly saving in local currency
    {"name": "Small studio", "price": 16_000, "saving": 1_200},
    {"name": "Agency", "price": 240_000, "saving": 11_000},
]

if __name__ == "__main__":
    for case in CASES:
        print(case["name"])
        for locale in ("pt", "en"):
            price = case["price"] if locale == "pt" else to_dollars(case["price"])
            saving = case["saving"] if locale == "pt" else to_dollars(case["saving"])
            months = payback_months(price, saving)
            print(f"  {locale}: {money(price, locale)} / {money(saving, locale)} per month -> {months} months")
    print()
    print("conversion samples")
    for local in (950, 4_800, 96_000, 1_400_000):
        print(f"  {money(local, 'pt')} -> {money(to_dollars(local), 'en')}")
