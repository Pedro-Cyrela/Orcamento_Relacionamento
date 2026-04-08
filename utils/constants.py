from __future__ import annotations

APP_TITLE = "Comparador de Previsões Orçamentárias"
APP_SUBTITLE = (
    "Compare 2 ou mais previsões em Excel com padronização por biblioteca, "
    "detalhamento por classificação e exportação profissional."
)

REQUIRED_LIBRARY_SHEETS = {
    "tipos_padrao": "Tipos_Padrao",
    "biblioteca_map": "Biblioteca_Map",
}

EXPECTED_LIBRARY_COLUMNS = {
    "Tipos_Padrao": [
        "id_tipo_gasto",
        "tipo_gasto_padrao",
        "subtipo_gasto",
        "descricao_tipo",
        "ativo",
    ],
    "Biblioteca_Map": [
        "administradora",
        "descricao_original",
        "id_tipo_gasto",
        "tipo_gasto_padrao",
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

COLUMN_ALIASES = {
    "descricao": [
        "previsao de despesas",
        "previsão de despesas",
        "historico da despesa",
        "histórico da despesa",
        "descricao",
        "descrição",
        "despesa",
        "item",
    ],
    "valor_90_dias": [
        "90 dias",
        "valor 90 dias",
        "prev 90 dias",
        "90d",
        "90dias",
    ],
    "valor_cota_plena": [
        "cota plena",
        "cota plena    ",
        "valor cota plena",
        "plena",
        "cota",
    ],
    "codigo_item": ["item", "cod", "codigo", "código"],
}

VALUE_FILL_RULES = {
    "duplicate_single_value_to_cota": True,
}

EXPORT_SHEET_NAMES = {
    "summary": "Resumo_Comparativo",
    "detail": "Detalhamento_Classificacoes",
    "unclassified": "Nao_Classificados",
}
