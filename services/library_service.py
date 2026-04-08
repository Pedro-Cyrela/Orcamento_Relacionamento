from __future__ import annotations

import io
from typing import Iterable

import pandas as pd

from services.models import LibraryData
from utils.constants import (
    DEFAULT_UNCLASSIFIED_LABEL,
    DEFAULT_UNCLASSIFIED_SUBTYPE,
    EXPECTED_LIBRARY_COLUMNS,
    GENERAL_ADMIN_ALIASES,
    REQUIRED_LIBRARY_SHEETS,
)
from utils.helpers import AppError, bool_from_any, normalize_column_name, normalize_text, uploaded_file_to_bytes


class LibraryService:
    @staticmethod
    def load_library(uploaded_file) -> LibraryData:
        file_bytes = uploaded_file_to_bytes(uploaded_file)
        try:
            workbook = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
        except Exception as exc:
            raise AppError(f"Não foi possível abrir a biblioteca Excel: {exc}") from exc

        normalized_sheet_map = {normalize_column_name(name): name for name in workbook.keys()}
        missing = [
            logical_name
            for logical_name in REQUIRED_LIBRARY_SHEETS
            if logical_name not in normalized_sheet_map
        ]
        if missing:
            friendly = ", ".join(REQUIRED_LIBRARY_SHEETS[item] for item in missing)
            raise AppError(f"A biblioteca não contém as abas obrigatórias: {friendly}.")

        tipos_sheet = normalized_sheet_map["tipos_padrao"]
        mapa_sheet = normalized_sheet_map["biblioteca_map"]

        tipos = LibraryService._prepare_sheet(
            workbook[tipos_sheet], EXPECTED_LIBRARY_COLUMNS["Tipos_Padrao"], sheet_name=tipos_sheet
        )
        mapa = LibraryService._prepare_sheet(
            workbook[mapa_sheet], EXPECTED_LIBRARY_COLUMNS["Biblioteca_Map"], sheet_name=mapa_sheet
        )

        tipos = tipos[tipos["ativo"].apply(bool_from_any)]
        mapa = mapa[mapa["ativo"].apply(bool_from_any)]

        tipos["id_tipo_gasto"] = tipos["id_tipo_gasto"].astype(str).str.strip()
        mapa["id_tipo_gasto"] = mapa["id_tipo_gasto"].astype(str).str.strip()
        tipos["tipo_gasto_padrao"] = tipos["tipo_gasto_padrao"].fillna(DEFAULT_UNCLASSIFIED_LABEL)
        tipos["subtipo_gasto"] = tipos["subtipo_gasto"].fillna("")
        mapa["tipo_gasto_padrao"] = mapa["tipo_gasto_padrao"].fillna(DEFAULT_UNCLASSIFIED_LABEL)
        mapa["subtipo_gasto"] = mapa["subtipo_gasto"].fillna("")
        mapa["administradora"] = mapa["administradora"].fillna("")
        mapa["descricao_original"] = mapa["descricao_original"].fillna("")

        tipos["norm_id_tipo_gasto"] = tipos["id_tipo_gasto"].apply(normalize_text)
        tipos["norm_tipo_gasto_padrao"] = tipos["tipo_gasto_padrao"].apply(normalize_text)

        mapa["norm_administradora"] = mapa["administradora"].apply(normalize_text)
        mapa["norm_descricao_original"] = mapa["descricao_original"].apply(normalize_text)
        mapa["is_regra_geral"] = mapa["norm_administradora"].isin(GENERAL_ADMIN_ALIASES)

        tipos_ids = set(tipos["norm_id_tipo_gasto"])
        orphan_rows = mapa.loc[~mapa["id_tipo_gasto"].apply(normalize_text).isin(tipos_ids)]
        warnings: list[str] = []
        if not orphan_rows.empty:
            warnings.append(
                "Algumas linhas da aba Biblioteca_Map possuem id_tipo_gasto inexistente em Tipos_Padrao e foram mantidas para não bloquear a operação."
            )

        return LibraryData(tipos_padrao=tipos, mapa=mapa, warnings=warnings)

    @staticmethod
    def _prepare_sheet(df: pd.DataFrame, required_columns: Iterable[str], sheet_name: str) -> pd.DataFrame:
        prepared = df.copy()
        prepared.columns = [normalize_column_name(column) for column in prepared.columns]

        missing = [column for column in required_columns if column not in prepared.columns]
        if missing:
            raise AppError(
                f"A aba '{sheet_name}' não possui todas as colunas mínimas obrigatórias. Faltando: {', '.join(missing)}."
            )

        prepared = prepared[[column for column in prepared.columns if column]]
        prepared = prepared.dropna(how="all")
        return prepared.reset_index(drop=True)

    @staticmethod
    def build_default_template() -> bytes:
        tipos = pd.DataFrame(
            [
                {
                    "id_tipo_gasto": "1",
                    "tipo_gasto_padrao": "Pessoal",
                    "subtipo_gasto": "Folha e encargos",
                    "descricao_tipo": "Custos com mão de obra, encargos e benefícios",
                    "ativo": True,
                },
                {
                    "id_tipo_gasto": "2",
                    "tipo_gasto_padrao": "Manutenção",
                    "subtipo_gasto": "Serviços periódicos",
                    "descricao_tipo": "Contratos e serviços de manutenção",
                    "ativo": True,
                },
            ]
        )
        mapa = pd.DataFrame(
            [
                {
                    "administradora": "GERAL",
                    "descricao_original": "Elevadores",
                    "id_tipo_gasto": "2",
                    "tipo_gasto_padrao": "Manutenção",
                    "subtipo_gasto": "Elevadores",
                    "regra_observacao": "Exemplo de regra geral",
                    "ativo": True,
                },
                {
                    "administradora": "GERAL",
                    "descricao_original": "Salários + Encargos e Beneficios",
                    "id_tipo_gasto": "1",
                    "tipo_gasto_padrao": "Pessoal",
                    "subtipo_gasto": "Folha e encargos",
                    "regra_observacao": "Exemplo de regra geral",
                    "ativo": True,
                },
            ]
        )
        template = pd.DataFrame(columns=mapa.columns)
        resumo = pd.DataFrame({"observacao": ["Preencha Tipos_Padrao e Biblioteca_Map para usar no app."]})
        instrucoes = pd.DataFrame(
            {
                "passo": [
                    "1. Cadastre os tipos oficiais na aba Tipos_Padrao.",
                    "2. Crie regras na aba Biblioteca_Map.",
                    "3. Use administradora vazia ou GERAL para regra genérica.",
                ]
            }
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            tipos.to_excel(writer, sheet_name="Tipos_Padrao", index=False)
            mapa.to_excel(writer, sheet_name="Biblioteca_Map", index=False)
            template.to_excel(writer, sheet_name="Template_Novos_Map", index=False)
            resumo.to_excel(writer, sheet_name="Resumo", index=False)
            instrucoes.to_excel(writer, sheet_name="Instrucoes", index=False)
        return output.getvalue()
