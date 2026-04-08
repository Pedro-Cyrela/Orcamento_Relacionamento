from __future__ import annotations

import pandas as pd

from services.models import ForecastData, LibraryData
from utils.constants import DEFAULT_UNCLASSIFIED_LABEL, DEFAULT_UNCLASSIFIED_SUBTYPE
from utils.helpers import normalize_text


class StandardizerService:
    @staticmethod
    def standardize(raw_forecast: dict, library: LibraryData, forecast_id: str, label: str) -> ForecastData:
        df = raw_forecast["raw_data"].copy()
        if df.empty:
            raise ValueError("A previsão não contém linhas úteis para padronização.")

        df["descricao_original"] = df["descricao_original"].fillna("")
        df["norm_descricao_original"] = df["descricao_original"].apply(normalize_text)
        df["administradora"] = raw_forecast["administradora"]
        df["empreendimento"] = raw_forecast["empreendimento"]
        df["forecast_id"] = forecast_id
        df["previsao_label"] = label
        df["norm_administradora"] = df["administradora"].apply(normalize_text)

        standardized = df.apply(lambda row: StandardizerService._apply_mapping(row, library), axis=1)
        standardized_df = pd.concat([df.reset_index(drop=True), standardized.reset_index(drop=True)], axis=1)

        standardized_df["tipo_gasto_padrao"] = standardized_df["tipo_gasto_padrao"].fillna(DEFAULT_UNCLASSIFIED_LABEL)
        standardized_df["subtipo_gasto"] = standardized_df["subtipo_gasto"].fillna(DEFAULT_UNCLASSIFIED_SUBTYPE)
        standardized_df["id_tipo_gasto"] = standardized_df["id_tipo_gasto"].fillna("NC")
        standardized_df["regra_observacao"] = standardized_df["regra_observacao"].fillna("")
        standardized_df["classificado"] = standardized_df["tipo_gasto_padrao"] != DEFAULT_UNCLASSIFIED_LABEL

        consolidated = (
            standardized_df.groupby(["tipo_gasto_padrao", "subtipo_gasto"], dropna=False, as_index=False)[
                ["valor_90_dias", "valor_cota_plena"]
            ]
            .sum()
            .sort_values(["tipo_gasto_padrao", "subtipo_gasto"])
            .reset_index(drop=True)
        )

        unclassified = standardized_df.loc[~standardized_df["classificado"]].copy()
        warnings = list(raw_forecast.get("warnings", []))
        if not unclassified.empty:
            warnings.append(
                f"{len(unclassified)} item(ns) ficaram sem classificação na previsão {label}."
            )

        return ForecastData(
            forecast_id=forecast_id,
            label=label,
            filename=raw_forecast["filename"],
            administradora=raw_forecast["administradora"],
            empreendimento=raw_forecast["empreendimento"],
            sheet_name=raw_forecast["sheet_name"],
            raw_data=df,
            standardized_data=standardized_df,
            consolidated_data=consolidated,
            unclassified_data=unclassified,
            warnings=warnings,
        )

    @staticmethod
    def _apply_mapping(row: pd.Series, library: LibraryData) -> pd.Series:
        mapa = library.mapa
        desc_key = row["norm_descricao_original"]
        admin_key = row["norm_administradora"]

        specific = mapa[
            (mapa["norm_descricao_original"] == desc_key)
            & (mapa["norm_administradora"] == admin_key)
        ]
        if not specific.empty:
            return specific.iloc[0][["id_tipo_gasto", "tipo_gasto_padrao", "subtipo_gasto", "regra_observacao"]]

        general = mapa[
            (mapa["norm_descricao_original"] == desc_key)
            & (mapa["is_regra_geral"])
        ]
        if not general.empty:
            return general.iloc[0][["id_tipo_gasto", "tipo_gasto_padrao", "subtipo_gasto", "regra_observacao"]]

        return pd.Series(
            {
                "id_tipo_gasto": "NC",
                "tipo_gasto_padrao": DEFAULT_UNCLASSIFIED_LABEL,
                "subtipo_gasto": DEFAULT_UNCLASSIFIED_SUBTYPE,
                "regra_observacao": "Sem regra correspondente na biblioteca.",
            }
        )
