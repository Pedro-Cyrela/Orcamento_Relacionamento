from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


class AppError(Exception):
    pass


@dataclass
class ParseResult:
    administradora: str
    empreendimento: str
    valido: bool
    mensagem: str | None = None


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = strip_accents(text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def normalize_column_name(name: Any) -> str:
    text = normalize_text(name)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def safe_to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)) and pd.notna(value):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    text = text.replace("R$", "").replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9\-\.]", "", text)
    if text in {"", "-", ".", "-."}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def bool_from_any(value: Any, default: bool = True) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    normalized = normalize_text(value)
    if normalized in {"", "nan"}:
        return default
    if normalized in {"1", "true", "t", "sim", "s", "yes", "y", "ativo", "ok"}:
        return True
    if normalized in {"0", "false", "f", "nao", "não", "n", "inativo", "off"}:
        return False
    return default


def parse_filename_metadata(filename: str) -> ParseResult:
    name = Path(filename).name
    base = re.sub(r"\.xlsx$", "", name, flags=re.IGNORECASE)
    parts = base.split(" - ", 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return ParseResult(
            administradora="Não identificado",
            empreendimento=base,
            valido=False,
            mensagem="Nome fora do padrão esperado 'Administradora - Empreendimento.xlsx'. Os dados foram carregados, mas revise o arquivo para melhor identificação.",
        )
    return ParseResult(administradora=parts[0].strip(), empreendimento=parts[1].strip(), valido=True)


def ensure_excel_file(filename: str) -> None:
    if not filename.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        raise AppError(f"O arquivo '{filename}' não é um Excel compatível.")


def uploaded_file_to_bytes(uploaded_file: Any) -> bytes:
    if uploaded_file is None:
        raise AppError("Nenhum arquivo foi enviado.")
    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue()
    if isinstance(uploaded_file, (bytes, bytearray)):
        return bytes(uploaded_file)
    if isinstance(uploaded_file, io.BytesIO):
        return uploaded_file.getvalue()
    raise AppError("Não foi possível ler o conteúdo do arquivo enviado.")
