from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from app.core.settings import BIBLIOTECA_GASTOS_PATH

REQUIRED_COLUMNS = {
    "Tipos_Padrao": {
        "id_tipo_gasto",
        "tipo_gasto_padrao",
        "subtipo_gasto",
        "grupo_macro",
        "descricao_tipo",
    }
}

ALIASES = {
    "subtipo_gasto": "tipo_gasto_padrao",
    "descricao_tipo": "descricao_padrao",
}

ORDERED_MAIN_COLUMNS = [
    "id_tipo_gasto",
    "tipo_gasto_padrao",
    "subtipo_gasto",
    "grupo_macro",
    "descricao_tipo",
]


def _normalize_columns(columns: Iterable[str]) -> list[str]:
    return [str(c).strip() if c is not None else "" for c in columns]


def _resolver_path(path: str | Path | None = None) -> Path:
    resolved = Path(path) if path else BIBLIOTECA_GASTOS_PATH
    if not resolved.exists():
        raise FileNotFoundError(
            "Biblioteca não encontrada em: "
            f"{resolved}. Verifique se o arquivo está em app/data/biblioteca "
            "ou configure a variável BIBLIOTECA_GASTOS_PATH."
        )
    return resolved


def carregar_biblioteca(path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    arquivo = _resolver_path(path)
    xls = pd.ExcelFile(arquivo)

    if "Tipos_Padrao" not in xls.sheet_names:
        raise ValueError("A biblioteca não possui a aba obrigatória 'Tipos_Padrao'.")

    tipos = pd.read_excel(arquivo, sheet_name="Tipos_Padrao")
    tipos.columns = _normalize_columns(tipos.columns)

    for expected, fallback in ALIASES.items():
        if expected not in tipos.columns and fallback in tipos.columns:
            tipos[expected] = tipos[fallback]

    missing = REQUIRED_COLUMNS["Tipos_Padrao"] - set(tipos.columns)
    if missing:
        faltando = ", ".join(sorted(missing))
        raise ValueError(
            "A aba 'Tipos_Padrao' não possui todas as colunas mínimas obrigatórias. "
            f"Faltando: {faltando}."
        )

    tipos = tipos[
        ORDERED_MAIN_COLUMNS
        + [c for c in tipos.columns if c not in set(ORDERED_MAIN_COLUMNS)]
    ].copy()

    retorno = {"Tipos_Padrao": tipos}

    if "Biblioteca_Map" in xls.sheet_names:
        retorno["Biblioteca_Map"] = pd.read_excel(arquivo, sheet_name="Biblioteca_Map")

    if "Template_Novos_Map" in xls.sheet_names:
        retorno["Template_Novos_Map"] = pd.read_excel(arquivo, sheet_name="Template_Novos_Map")

    if "Contrato_Codigo" in xls.sheet_names:
        retorno["Contrato_Codigo"] = pd.read_excel(arquivo, sheet_name="Contrato_Codigo")

    return retorno


def carregar_biblioteca_padrao() -> dict[str, pd.DataFrame]:
    return carregar_biblioteca(BIBLIOTECA_GASTOS_PATH)
