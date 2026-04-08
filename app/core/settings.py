from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BIBLIOTECA_PATH = PROJECT_ROOT / "app" / "data" / "biblioteca" / "biblioteca_padronizacao_gastos_modelo_v2.xlsx"
BIBLIOTECA_GASTOS_PATH = Path(
    os.getenv("BIBLIOTECA_GASTOS_PATH", str(DEFAULT_BIBLIOTECA_PATH))
).resolve()
