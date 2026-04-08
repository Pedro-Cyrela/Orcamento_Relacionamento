from __future__ import annotations

REQUIRED_LIBRARY_SHEETS = {
    "tipos_padrao": "Tipos_Padrao",
    "biblioteca_map": "Biblioteca_Map",
}

EXPECTED_LIBRARY_COLUMNS = {
    "Tipos_Padrao": [
        "id_tipo_gasto",
        "tipo_gasto_padrao",
    ],
    "Biblioteca_Map": [
        "administradora",
        "descricao_original",
        "id_tipo_gasto",
        "tipo_gasto_padrao",
    ],
}

OPTIONAL_LIBRARY_COLUMNS = {
    "Tipos_Padrao": [
        "subtipo_gasto",
        "descricao_tipo",
        "ativo",
    ],
    "Biblioteca_Map": [
        "subtipo_gasto",
        "regra_observacao",
        "ativo",
    ],
}

GENERAL_ADMIN_ALIASES = {
    "",
    "geral",
    "general",
    "todos",
    "todas",
    "padrao",
    "padrão",
    "default",
    "global",
    "all",
    "*",
    "-",
    "n/a",
    "na",
    "null",
    "none",
}

DEFAULT_UNCLASSIFIED_LABEL = "Não classificado"
DEFAULT_UNCLASSIFIED_SUBTYPE = "Sem mapeamento"

VALUE_FILL_RULES = {
    "duplicate_single_value_to_cota": True,
}

EXPORT_SHEET_NAMES = {
    "summary": "Resumo_Comparativo",
    "detail": "Detalhamento_Classificacoes",
    "unclassified": "Nao_Classificados",
}
