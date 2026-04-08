from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ForecastData:
    forecast_id: str
    label: str
    filename: str
    administradora: str
    empreendimento: str
    sheet_name: str
    raw_data: pd.DataFrame
    standardized_data: pd.DataFrame
    consolidated_data: pd.DataFrame
    unclassified_data: pd.DataFrame
    warnings: list[str] = field(default_factory=list)


@dataclass
class LibraryData:
    tipos_padrao: pd.DataFrame
    mapa: pd.DataFrame
    warnings: list[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    comparison_label: str
    base_forecast_id: str
    compared_forecast_id: str
    summary: pd.DataFrame
    detail: pd.DataFrame
    total_unclassified: int
