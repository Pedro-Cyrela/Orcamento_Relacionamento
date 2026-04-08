from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd

from utils.constants import VALUE_FILL_RULES
from utils.helpers import AppError, normalize_text, parse_filename_metadata, safe_to_float, uploaded_file_to_bytes


class ForecastReader:
    @staticmethod
    def read_forecast(uploaded_file) -> dict[str, Any]:
        file_bytes = uploaded_file_to_bytes(uploaded_file)
        filename = getattr(uploaded_file, "name", "arquivo.xlsx")
        metadata = parse_filename_metadata(filename)
        raw_sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)
        if not raw_sheets:
            raise AppError(f"O arquivo '{filename}' não possui abas legíveis.")

        best_sheet_name, extracted = ForecastReader._extract_best_sheet(raw_sheets, filename)
        warnings = list(extracted.get("warnings", []))
        if metadata.mensagem:
            warnings.append(metadata.mensagem)

        return {
            "filename": filename,
            "administradora": metadata.administradora,
            "empreendimento": metadata.empreendimento,
            "sheet_name": best_sheet_name,
            "raw_data": extracted["raw_data"],
            "warnings": warnings,
        }

    @staticmethod
    def _extract_best_sheet(raw_sheets: dict[str, pd.DataFrame], filename: str) -> tuple[str, dict[str, Any]]:
        best_name = None
        best_result = None
        best_score = -1

        for sheet_name, df in raw_sheets.items():
            result = ForecastReader._extract_rows_from_sheet(df)
            score = len(result["raw_data"])
            if score > best_score:
                best_name = sheet_name
                best_result = result
                best_score = score

        if best_result is None or best_result["raw_data"].empty:
            raise AppError(
                f"Não foi possível identificar a tabela principal de previsão em '{filename}'. Revise o layout ou ajuste a camada de configuração."
            )
        return best_name or "Plan1", best_result

    @staticmethod
    def _extract_rows_from_sheet(df: pd.DataFrame) -> dict[str, Any]:
        working = df.copy().fillna("")
        warnings: list[str] = []

        header_row_idx = ForecastReader._find_header_row(working)
        if header_row_idx is not None:
            extracted = ForecastReader._parse_matrix_layout(working, header_row_idx)
            if not extracted.empty:
                return {"raw_data": extracted, "warnings": warnings}

        extracted = ForecastReader._parse_single_value_layout(working)
        if not extracted.empty:
            warnings.append(
                "Arquivo com apenas uma coluna principal de valores. A coluna de cota plena foi replicada a partir do valor disponível para manter a comparação funcional."
            )
            return {"raw_data": extracted, "warnings": warnings}

        return {"raw_data": pd.DataFrame(), "warnings": warnings}

    @staticmethod
    def _find_header_row(df: pd.DataFrame) -> int | None:
        for idx in range(min(len(df), 80)):
            row_values = [normalize_text(value) for value in df.iloc[idx].tolist()]
            if any("90 dias" in value for value in row_values) and any("cota plena" in value or value == "cota" for value in row_values):
                return idx
        return None

    @staticmethod
    def _parse_matrix_layout(df: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
        header_values = [normalize_text(value) for value in df.iloc[header_row_idx].tolist()]
        desc_col = ForecastReader._find_best_column(
            header_values,
            ["previsao de despesas", "historico da despesa", "descrição", "descricao"],
        )
        code_col = ForecastReader._find_best_column(header_values, ["item", "codigo", "código"])
        if code_col is None and ForecastReader._column_looks_like_codes(df, 0, start_row=header_row_idx + 1):
            code_col = 0
        col_90 = ForecastReader._find_best_column(header_values, ["90 dias"])
        col_cota = ForecastReader._find_best_column(header_values, ["cota plena", "cota"])

        if desc_col is None or col_90 is None or col_cota is None:
            return pd.DataFrame()

        rows: list[dict[str, Any]] = []
        for idx in range(header_row_idx + 1, len(df)):
            row = df.iloc[idx]
            description = str(row.iloc[desc_col]).strip()
            code = str(row.iloc[code_col]).strip() if code_col is not None else ""
            v90 = safe_to_float(row.iloc[col_90])
            vcota = safe_to_float(row.iloc[col_cota])

            if not description:
                continue
            if ForecastReader._is_terminal_row(description):
                break
            if ForecastReader._is_group_total_row(df, idx, code, description):
                continue
            if ForecastReader._is_section_row(code, description, v90, vcota):
                continue
            if v90 == 0 and vcota == 0 and not ForecastReader._looks_like_detail_row(description):
                continue

            rows.append(
                {
                    "codigo_item": code,
                    "descricao_original": description,
                    "valor_90_dias": v90,
                    "valor_cota_plena": vcota,
                    "observacao": str(row.iloc[col_cota + 1]).strip() if col_cota + 1 < len(row) else "",
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def _parse_single_value_layout(df: pd.DataFrame) -> pd.DataFrame:
        candidate_columns = ForecastReader._identify_numeric_columns(df)
        if not candidate_columns:
            return pd.DataFrame()
        value_col = candidate_columns[-1]

        rows: list[dict[str, Any]] = []
        for idx in range(len(df)):
            description = str(df.iat[idx, 0]).strip() if df.shape[1] > 0 else ""
            if not description:
                continue
            value = safe_to_float(df.iat[idx, value_col]) if value_col < df.shape[1] else 0.0
            if ForecastReader._is_terminal_row(description):
                break
            if ForecastReader._is_single_layout_section(description, value):
                continue
            if value == 0 and not ForecastReader._looks_like_detail_row(description):
                continue

            rows.append(
                {
                    "codigo_item": "",
                    "descricao_original": description,
                    "valor_90_dias": value,
                    "valor_cota_plena": value if VALUE_FILL_RULES["duplicate_single_value_to_cota"] else 0.0,
                    "observacao": "",
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def _identify_numeric_columns(df: pd.DataFrame) -> list[int]:
        candidates: list[tuple[int, int]] = []
        for col_idx in range(df.shape[1]):
            numeric_count = 0
            for value in df.iloc[:, col_idx].tolist():
                if safe_to_float(value) != 0:
                    numeric_count += 1
            if numeric_count >= 5:
                candidates.append((col_idx, numeric_count))
        candidates.sort(key=lambda item: (item[1], item[0]))
        return [col for col, _ in candidates]

    @staticmethod
    def _find_best_column(headers: list[str], tokens: list[str]) -> int | None:
        for idx, header in enumerate(headers):
            for token in tokens:
                if token in header:
                    return idx
        return None

    @staticmethod
    def _column_looks_like_codes(df: pd.DataFrame, col_idx: int, start_row: int) -> bool:
        sample = []
        for idx in range(start_row, min(len(df), start_row + 25)):
            value = str(df.iat[idx, col_idx]).strip() if col_idx < df.shape[1] else ""
            if value:
                sample.append(value)
        hits = sum(1 for value in sample if re.fullmatch(r"\d+(\.\d+)*\.?", value))
        return hits >= 3

    @staticmethod
    def _is_terminal_row(description: str) -> bool:
        text = normalize_text(description)
        terminal_tokens = [
            "previsao de receita",
            "previsão de receita",
            "observacoes",
            "observações",
            "nao fazem parte",
            "não fazem parte",
            "ticket medio",
            "ticket médio",
        ]
        return any(token in text for token in terminal_tokens)

    @staticmethod
    def _is_group_total_row(df: pd.DataFrame, row_idx: int, code: str, description: str) -> bool:
        code_text = str(code).strip()
        if not re.fullmatch(r"\d+\.\d+", code_text):
            return False

        norm_desc = normalize_text(description)
        for next_idx in range(row_idx + 1, min(len(df), row_idx + 6)):
            next_code = str(df.iat[next_idx, 0]).strip() if df.shape[1] > 0 else ""
            if next_code.startswith(code_text + "."):
                return True

        return norm_desc.isupper() or norm_desc in {"contratos", "administrativas", "tarifas e taxas", "pessoal"}

    @staticmethod
    def _is_section_row(code: str, description: str, v90: float, vcota: float) -> bool:
        code_text = normalize_text(code)
        desc_text = normalize_text(description)

        if desc_text.startswith("total"):
            return True
        if re.fullmatch(r"\d+(\.\d+)?", code_text) and v90 == 0 and vcota == 0:
            return True
        if code_text and v90 == 0 and vcota == 0 and desc_text.isupper():
            return True
        if not code_text and v90 == 0 and vcota == 0 and not ForecastReader._looks_like_detail_row(description):
            return True
        return False

    @staticmethod
    def _looks_like_detail_row(description: str) -> bool:
        text = normalize_text(description)
        return any(char.isalpha() for char in text) and len(text) > 2

    @staticmethod
    def _is_single_layout_section(description: str, value: float) -> bool:
        text = normalize_text(description)
        if text.startswith("empreendimento") or text.startswith("demonstrativo") or text.startswith("numero de unidades"):
            return True
        if text.startswith("apuracao") or text.startswith("apuração") or text.startswith("vigencia"):
            return True
        if text.startswith("observacoes") or text.startswith("observações"):
            return True
        if value == 0 and re.match(r"^[a-z]\)", text):
            return True
        if text.startswith("sub total") or text.startswith("total geral") or text.startswith("taxa de administracao"):
            return True
        return False
