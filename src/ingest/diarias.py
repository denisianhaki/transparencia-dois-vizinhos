"""Ingestão e enriquecimento de Empenhos de Diárias Concedidas."""

from __future__ import annotations

import csv
import re
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.io import detect_encoding, find_latest_csv, parse_ptbr_date, parse_ptbr_decimal

EMPENHO_NUM_RE = re.compile(r"^\d+/\d{4}$")
SERVIDOR_RE = re.compile(r"^(\S+)\s+(.+?)\s+CPF:")


def _has_weekend(dt_ini, dt_fim) -> bool:
    if dt_ini is None or dt_fim is None:
        return False
    cur = dt_ini
    for _ in range(60):
        if cur > dt_fim:
            break
        if cur.weekday() in (5, 6):
            return True
        cur += timedelta(days=1)
    return False


def ingest_diarias(
    raw_diarias_dir: Path,
    processed_dir: Path,
    df_folha: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Limpa o relatório EmpenhosDiariasConcedidas*.csv e cruza com a folha."""
    path = find_latest_csv(raw_diarias_dir, "EmpenhosDiariasConcedidas*.csv")
    if not path:
        raise FileNotFoundError(f"Nenhum arquivo EmpenhosDiariasConcedidas*.csv encontrado em {raw_diarias_dir}")

    enc = detect_encoding(path)
    records: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    section = ""

    def flush() -> None:
        nonlocal cur
        if cur is None:
            return
        desc = " | ".join(cur["DescParts"]).strip()
        if not cur["Destino"]:
            m_d = re.search(r"DESTINO\s*:\s*([^\r\n|]+)", desc)
            if m_d:
                cur["Destino"] = m_d.group(1).strip()
        if not cur["Objetivo"]:
            m_o = re.search(r"OBJETIVO\s*:\s*([^\r\n|]+)", desc)
            if m_o:
                cur["Objetivo"] = m_o.group(1).strip()

        dt_emp = parse_ptbr_date(cur["DataEmpenho"])
        dt_ini = parse_ptbr_date(cur["DataInicialViagem"])
        dt_fim = parse_ptbr_date(cur["DataFinalViagem"])

        records.append(
            {
                "Empenho": cur["Empenho"],
                "DataEmpenho": cur["DataEmpenho"],
                "MesEmpenho": dt_emp.strftime("%Y-%m") if dt_emp else "",
                "Natureza": cur["Natureza"],
                "ValorEmpenho": cur["ValorEmpenho"],
                "ServidorCodigo": cur["ServidorCodigo"],
                "ServidorNome": cur["ServidorNome"],
                "DataInicialViagem": cur["DataInicialViagem"],
                "DataFinalViagem": cur["DataFinalViagem"],
                "NumeroDiarias": cur["NumeroDiarias"],
                "Destino": cur["Destino"],
                "TipoObjetivo": cur["TipoObjetivo"],
                "LeiConcessao": cur["LeiConcessao"],
                "DataPagamento": cur["DataPagamento"],
                "ValorPagamento": cur["ValorPagamento"],
                "EmpenhoAposViagem": bool(dt_emp and dt_ini and dt_emp > dt_ini),
                "IncluiFimDeSemana": _has_weekend(dt_ini, dt_fim),
                "Objetivo": cur["Objetivo"],
                "Descricao": re.sub(r"\s+", " ", desc).strip(),
            }
        )
        cur = None

    with path.open("r", encoding=enc, newline="") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        for fields in reader:
            if not fields:
                continue
            non_empty = [c.strip() for c in fields if c.strip()]
            if not non_empty:
                continue
            line_join = " | ".join(non_empty)

            if any(
                m in line_join
                for m in (
                    "MUNICÍPIO DE DOIS VIZINHOS",
                    "Empenhos de Diárias Concedidas",
                    "Período de Empenho:",
                    "Total Geral:",
                )
            ) or re.search(r"Página:\s*\d+", line_join):
                continue

            c0 = fields[0].strip()
            if c0 == "Empenho" and "Data:" in line_join:
                section = "EmpenhoHeader"
                continue
            if c0 == "Liquidação" and "Data:" in line_join:
                section = "LiquidacaoHeader"
                continue
            if c0 == "Pagamento" and "Data:" in line_join:
                section = "PagamentoHeader"
                continue

            if EMPENHO_NUM_RE.match(c0):
                if section == "EmpenhoHeader":
                    flush()
                    section = "EmpenhoBody"
                    cur = {
                        "Empenho": c0,
                        "DataEmpenho": non_empty[1] if len(non_empty) >= 2 else "",
                        "Natureza": non_empty[5] if len(non_empty) >= 6 else "",
                        "ValorEmpenho": parse_ptbr_decimal(non_empty[-1]),
                        "ServidorCodigo": "",
                        "ServidorNome": "",
                        "DataInicialViagem": "",
                        "DataFinalViagem": "",
                        "NumeroDiarias": 0.0,
                        "Destino": "",
                        "TipoObjetivo": "",
                        "LeiConcessao": "",
                        "DataPagamento": "",
                        "ValorPagamento": 0.0,
                        "Objetivo": "",
                        "DescParts": [],
                    }
                    continue
                if section == "PagamentoHeader" and cur is not None:
                    section = "PagamentoBody"
                    if len(non_empty) >= 3:
                        cur["DataPagamento"] = non_empty[1]
                        cur["ValorPagamento"] = parse_ptbr_decimal(non_empty[2])
                    continue
                if section == "LiquidacaoHeader" and cur is not None:
                    section = "LiquidacaoBody"
                    continue

            if cur is None:
                continue

            if c0.startswith("Servidor:"):
                srv_cell = next((x for x in non_empty if not x.startswith("Servidor:")), "")
                m_srv = SERVIDOR_RE.match(srv_cell)
                if m_srv:
                    cur["ServidorCodigo"] = m_srv.group(1).strip()
                    cur["ServidorNome"] = m_srv.group(2).strip()
                elif srv_cell:
                    cur["ServidorNome"] = srv_cell.strip()
                continue

            if "Lei/ato concessão:" in line_join:
                for i in range(len(non_empty) - 1):
                    if "Lei/ato concessão:" in non_empty[i]:
                        cur["LeiConcessao"] = non_empty[i + 1]
                        break
                continue

            if "Data inicial:" in line_join:
                for i in range(len(non_empty) - 1):
                    if non_empty[i] == "Data inicial:":
                        cur["DataInicialViagem"] = non_empty[i + 1]
                    elif non_empty[i] == "Data final:":
                        cur["DataFinalViagem"] = non_empty[i + 1]
                    elif non_empty[i] == "Número de diárias:":
                        cur["NumeroDiarias"] = parse_ptbr_decimal(non_empty[i + 1])
                continue

            if "Destino:" in line_join:
                for i in range(len(non_empty) - 1):
                    if non_empty[i] == "Destino:":
                        cur["Destino"] = non_empty[i + 1]
                    elif non_empty[i] == "Tipo objetivo:":
                        cur["TipoObjetivo"] = non_empty[i + 1]
                continue

            if re.match(r"^Descrição:$|^Produto\s*\|\s*Marca", line_join):
                continue
            cur["DescParts"].append(line_join)

    flush()
    df = pd.DataFrame(records)

    if df_folha is not None and not df_folha.empty and not df.empty:
        f_dedup = df_folha.copy()
        f_dedup["_key"] = f_dedup["Nome"].str.strip().str.upper()
        f_dedup = f_dedup.drop_duplicates(subset=["_key"])[
            ["_key", "Vinculo", "Cargo", "Lotacao", "Vencimento", "HorasExtras"]
        ].rename(columns={"Vencimento": "VencimentoFolha", "HorasExtras": "HorasExtrasFolha"})
        df["_key"] = df["ServidorNome"].str.strip().str.upper()
        df = df.merge(f_dedup, on="_key", how="left").drop(columns=["_key"])
        df["Vinculo"] = df["Vinculo"].fillna("")
        df["Cargo"] = df["Cargo"].fillna("")
        df["Lotacao"] = df["Lotacao"].fillna("")
        df["VencimentoFolha"] = df["VencimentoFolha"].fillna(0.0)
        df["HorasExtrasFolha"] = df["HorasExtrasFolha"].fillna(0.0)
    else:
        df["Vinculo"] = ""
        df["Cargo"] = ""
        df["Lotacao"] = ""
        df["VencimentoFolha"] = 0.0
        df["HorasExtrasFolha"] = 0.0

    processed_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_dir / "diarias_consolidada.csv", sep=";", index=False, encoding="utf-8-sig")
    return df
