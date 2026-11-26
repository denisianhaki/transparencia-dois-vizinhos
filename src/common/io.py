"""Funções compartilhadas de I/O, encoding e conversão de formatos brasileiros."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4})")


def detect_encoding(path: Path) -> str:
    """Detecta se o arquivo é UTF-8 (com ou sem BOM) ou Windows-1252."""
    raw = path.read_bytes()
    try:
        raw.decode("utf-8-sig")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "cp1252"


def parse_ptbr_decimal(val: Any) -> float:
    """Converte string numérica PT-BR (ex: '12.500,00') em float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    text = str(val).strip()
    if not text:
        return 0.0
    # Se já estiver no formato float padrão (sem vírgula, com ponto decimal único)
    if "," not in text and text.count(".") <= 1:
        try:
            return float(text)
        except ValueError:
            return 0.0
    clean = text.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def parse_ptbr_date(val: Any) -> date | None:
    """Extrai a primeira data dd/mm/aaaa de um texto."""
    if not val:
        return None
    m = DATE_RE.search(str(val))
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%d/%m/%Y").date()
    except ValueError:
        return None


def load_config(config_path: Path) -> dict[str, Any]:
    """Carrega o arquivo JSON de configuração de regras."""
    return json.loads(config_path.read_text(encoding="utf-8"))


def find_latest_csv(folder: Path, pattern: str) -> Path | None:
    """Retorna o arquivo CSV mais recente (ou maior em empate) correspondente ao padrão."""
    if not folder.exists():
        return None
    matches = list(folder.glob(pattern))
    if not matches:
        return None
    return max(matches, key=lambda p: (p.stat().st_mtime, p.stat().st_size))
