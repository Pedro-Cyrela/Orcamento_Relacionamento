from __future__ import annotations

def format_currency(value: float) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    formatted = f"R$ {numeric:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
