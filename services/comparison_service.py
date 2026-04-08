from __future__ import annotations

import pandas as pd

from services.models import ComparisonResult, ForecastData


class ComparisonService:
    @staticmethod
    def compare(base: ForecastData, compared: ForecastData) -> ComparisonResult:
        base_summary = base.consolidated_data.rename(
            columns={
                "valor_90_dias": "base_90_dias",
                "valor_cota_plena": "base_cota_plena",
            }
        )
        compared_summary = compared.consolidated_data.rename(
            columns={
                "valor_90_dias": "comparada_90_dias",
                "valor_cota_plena": "comparada_cota_plena",
            }
        )

        merged = pd.merge(
            base_summary,
            compared_summary,
            on=["tipo_gasto_padrao", "subtipo_gasto"],
            how="outer",
        ).fillna(0)
        merged["dif_90_dias"] = merged["comparada_90_dias"] - merged["base_90_dias"]
        merged["dif_cota_plena"] = merged["comparada_cota_plena"] - merged["base_cota_plena"]
        merged = merged.sort_values(["tipo_gasto_padrao", "subtipo_gasto"]).reset_index(drop=True)

        base_detail = base.standardized_data.rename(
            columns={
                "valor_90_dias": "base_90_dias",
                "valor_cota_plena": "base_cota_plena",
                "descricao_original": "descricao_base",
            }
        )
        compared_detail = compared.standardized_data.rename(
            columns={
                "valor_90_dias": "comparada_90_dias",
                "valor_cota_plena": "comparada_cota_plena",
                "descricao_original": "descricao_comparada",
            }
        )

        base_grouped = (
            base_detail.groupby(["tipo_gasto_padrao", "subtipo_gasto", "descricao_base"], as_index=False)[
                ["base_90_dias", "base_cota_plena"]
            ]
            .sum()
        )
        compared_grouped = (
            compared_detail.groupby(["tipo_gasto_padrao", "subtipo_gasto", "descricao_comparada"], as_index=False)[
                ["comparada_90_dias", "comparada_cota_plena"]
            ]
            .sum()
        )

        base_grouped = base_grouped.rename(columns={"descricao_base": "descricao_original"})
        compared_grouped = compared_grouped.rename(columns={"descricao_comparada": "descricao_original"})
        detail = pd.merge(
            base_grouped,
            compared_grouped,
            on=["tipo_gasto_padrao", "subtipo_gasto", "descricao_original"],
            how="outer",
        ).fillna(0)
        detail["dif_90_dias"] = detail["comparada_90_dias"] - detail["base_90_dias"]
        detail["dif_cota_plena"] = detail["comparada_cota_plena"] - detail["base_cota_plena"]
        detail = detail.sort_values(["tipo_gasto_padrao", "subtipo_gasto", "descricao_original"]).reset_index(drop=True)

        total_unclassified = len(base.unclassified_data) + len(compared.unclassified_data)
        return ComparisonResult(
            comparison_label=f"{compared.label} vs {base.label}",
            base_forecast_id=base.forecast_id,
            compared_forecast_id=compared.forecast_id,
            summary=merged,
            detail=detail,
            total_unclassified=total_unclassified,
        )
