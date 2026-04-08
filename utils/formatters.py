from __future__ import annotations

import pandas as pd


def format_currency(value: float) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    formatted = f"R$ {numeric:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")



def apply_difference_style(value: float) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    if numeric < 0:
        return "diff-negative"
    if numeric > 0:
        return "diff-positive"
    return "diff-neutral"



def format_dataframe_for_display(df: pd.DataFrame, currency_columns: list[str]) -> pd.DataFrame:
    display_df = df.copy()
    for column in currency_columns:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(format_currency)
    return display_df
