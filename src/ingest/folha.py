"""Ingestão e consolidação dos dados de Folha de Pagamento e Quadro Funcional."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.io import detect_encoding, find_latest_csv, parse_ptbr_decimal

VINCULOS_VALIDOS = {
    "Agente Político",
    "Cedido com ônus",
    "Comissionado",
    "Conselheiro Tutelar",
    "Efetivo",
    "Empregado Público",
    "Pensionista",
    "Recebido sem ônus",
    "Temporário",
}

MATRICULA_NOME_RE = re.compile(r"^(\d+)\s*-\s*(.+)$")
DATE_ONLY_RE = re.compile(r"\d{2}/\d{2}/\d{4}")


def _get_col(fields: list[str], col_map: dict[str, int], key: str, allow_left_fallback: bool = True) -> str:
    idx = col_map.get(key)
    if idx is None:
        return ""
    if idx < len(fields):
        val = fields[idx].replace("\r", " ").replace("\n", " ").strip()
        if val:
            return val
    if allow_left_fallback and idx - 1 >= 1 and idx - 1 < len(fields):
        val_left = fields[idx - 1].replace("\r", " ").replace("\n", " ").strip()
        if val_left:
            return val_left
    return ""


def parse_quadro_funcional(path: Path, competencia: str = "") -> pd.DataFrame:
    """Limpa o relatório visual Equiplano SRH 500.2082y (Quadro Funcional)."""
    enc = detect_encoding(path)
    records: list[dict[str, Any]] = []
    current_vinculo = ""
    current_rec: dict[str, Any] | None = None
    col_map: dict[str, int] = {}

    def flush() -> None:
        nonlocal current_rec
        if current_rec is not None:
            records.append(current_rec)
            current_rec = None

    with path.open("r", encoding=enc, newline="") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        for fields in reader:
            if not fields:
                continue
            first = fields[0].replace("\r", " ").replace("\n", " ").strip()
            non_empty = [c.strip() for c in fields if c.strip()]
            if not non_empty:
                continue
            joined = " | ".join(non_empty)

            if any(
                marker in joined
                for marker in (
                    "SRH 500.2082y",
                    "MUNICÍPIO DE DOIS VIZINHOS",
                    "Quadro Funcional",
                    "Tipo Cálculo:",
                    "Tipo carga horária:",
                    "Tipos de pessoa pública:",
                    "Ordenador por:",
                )
            ) or re.search(r"página \d+", joined, re.IGNORECASE):
                continue

            if first in ("Total:", "Nome"):
                continue

            if first in VINCULOS_VALIDOS:
                flush()
                current_vinculo = first
                continue

            # Cabeçalho linha 1
            h1_found = False
            for idx, cell in enumerate(fields):
                v = cell.strip()
                if v == "Data admissão":
                    if not h1_found:
                        col_map = {}
                    col_map["DataAdmissao"] = idx
                    h1_found = True
                elif v == "Data Término Contrato":
                    col_map["DataTermino"] = idx
                    h1_found = True
                elif v == "Nível salarial":
                    col_map["NivelSalarial"] = idx
                    h1_found = True
                elif v == "Carga horária":
                    col_map["CargaHoraria"] = idx
                    h1_found = True
                elif v == "Horário expediente":
                    col_map["HorarioExpediente"] = idx
                    h1_found = True
            if h1_found:
                continue

            # Cabeçalho linha 2
            h2_found = False
            for idx, cell in enumerate(fields):
                v = cell.strip()
                if v == "Investidura":
                    col_map["Investidura"] = idx
                    h2_found = True
                elif v == "Cargo":
                    col_map["Cargo"] = idx
                    h2_found = True
                elif v == "Local de trabalho":
                    col_map["LocalTrabalho"] = idx
                    h2_found = True
                elif v == "Situação":
                    col_map["Situacao"] = idx
                    h2_found = True
            if h2_found:
                continue

            if "Supervisor" in joined and current_rec is not None:
                for cell in fields:
                    if re.search(r"Supervisor\s*:", cell):
                        current_rec["Supervisor"] = re.sub(r"^.*Supervisor\s*:\s*", "", cell).strip()
                        break
                continue

            if "Total vantagens" in joined and current_rec is not None:
                for idx, cell in enumerate(fields):
                    if re.search(r"Total vantagens\s*:", cell):
                        for next_cell in fields[idx + 1 :]:
                            if next_cell.strip():
                                current_rec["TotalVantagensQuadro"] = parse_ptbr_decimal(next_cell)
                                break
                        break
                continue

            if "Data de exoneração" in joined and current_rec is not None:
                for cell in fields:
                    m = DATE_ONLY_RE.search(cell)
                    if m:
                        current_rec["DataExoneracao"] = m.group(0)
                        break
                continue

            m_srv = MATRICULA_NOME_RE.match(first)
            if m_srv:
                flush()
                current_rec = {
                    "Competencia": competencia,
                    "Vinculo": current_vinculo,
                    "Matricula": m_srv.group(1).strip(),
                    "Nome": m_srv.group(2).strip(),
                    "DataAdmissao": _get_col(fields, col_map, "DataAdmissao", False),
                    "DataTermino": _get_col(fields, col_map, "DataTermino", False),
                    "DataExoneracao": "",
                    "Investidura": _get_col(fields, col_map, "Investidura", True),
                    "CargoQuadro": _get_col(fields, col_map, "Cargo", True),
                    "NivelSalarial": _get_col(fields, col_map, "NivelSalarial", True),
                    "LocalTrabalho": _get_col(fields, col_map, "LocalTrabalho", True),
                    "CargaHoraria": _get_col(fields, col_map, "CargaHoraria", True),
                    "HorarioExpediente": _get_col(fields, col_map, "HorarioExpediente", True),
                    "SituacaoQuadro": _get_col(fields, col_map, "Situacao", True),
                    "Supervisor": "",
                    "TotalVantagensQuadro": 0.0,
                }

    flush()
    return pd.DataFrame(records)


def ingest_folha(raw_folha_dir: Path, processed_dir: Path, competencia: str) -> pd.DataFrame:
    """Consolida quadro funcional, salários e relação de licenças por Matrícula."""
    quadro_path = find_latest_csv(raw_folha_dir, "quadroFuncional*.csv")
    salarios_path = find_latest_csv(raw_folha_dir, "salarios*.csv")
    relacao_path = find_latest_csv(raw_folha_dir, "*Servidores*.csv")

    if not salarios_path:
        raise FileNotFoundError(f"Nenhum arquivo salarios*.csv encontrado em {raw_folha_dir}")

    df_sal = pd.read_csv(salarios_path, sep=";", encoding=detect_encoding(salarios_path), dtype=str).fillna("")
    df_sal["Matricula"] = df_sal["Matrícula"].str.strip()

    money_cols = {
        "Vencimento": "Vencimento",
        "Grat. de Assiduidade": "GratAssiduidade",
        "Gratificações": "Gratificacoes",
        "Horas Extras": "HorasExtras",
        "Férias": "Ferias",
        "Décimo Terceiro": "DecimoTerceiro",
        "Outras Vantagens": "OutrasVantagens",
        "total vantagens": "TotalVantagens",
        "Descontos Legais": "DescontosLegais",
        "Descontos Pessoais": "DescontosPessoais",
        "total líquido": "TotalLiquido",
    }
    for src_col, dst_col in money_cols.items():
        df_sal[dst_col] = df_sal[src_col].map(parse_ptbr_decimal)

    df_sal["PctHE_Sobre_Venc"] = df_sal.apply(
        lambda r: round((r["HorasExtras"] / r["Vencimento"]) * 100.0, 1) if r["Vencimento"] > 0 else 0.0,
        axis=1,
    )

    df_sal = df_sal.rename(
        columns={
            "Nome": "Nome",
            "Cargo": "Cargo",
            "Função de Confiança": "FuncaoConfianca",
            "Lotação": "Lotacao",
            "Situação": "Situacao",
        }
    )
    keep_sal = [
        "Matricula", "Nome", "Cargo", "FuncaoConfianca", "Lotacao", "Situacao",
        "Vencimento", "GratAssiduidade", "Gratificacoes", "HorasExtras",
        "PctHE_Sobre_Venc", "Ferias", "DecimoTerceiro", "OutrasVantagens",
        "TotalVantagens", "DescontosLegais", "DescontosPessoais", "TotalLiquido",
    ]
    df_out = df_sal[keep_sal].copy()
    df_out.insert(0, "Competencia", competencia)

    if quadro_path:
        df_q = parse_quadro_funcional(quadro_path, competencia)
        df_q = df_q.drop_duplicates(subset=["Matricula"])
        q_cols = [
            "Matricula", "Vinculo", "NivelSalarial", "LocalTrabalho",
            "Supervisor", "CargaHoraria", "DataAdmissao", "DataExoneracao",
        ]
        df_out = df_out.merge(df_q[q_cols], on="Matricula", how="left").fillna("")
    else:
        for c in ("Vinculo", "NivelSalarial", "LocalTrabalho", "Supervisor", "CargaHoraria", "DataAdmissao", "DataExoneracao"):
            df_out[c] = ""

    if relacao_path:
        df_r = pd.read_csv(relacao_path, sep=";", encoding=detect_encoding(relacao_path), dtype=str).fillna("")
        df_r["Matricula"] = df_r["Matrícula"].str.strip()
        df_r = df_r.drop_duplicates(subset=["Matricula"])[["Matricula", "Licença"]].rename(columns={"Licença": "Licenca"})
        df_out = df_out.merge(df_r, on="Matricula", how="left").fillna("")
    else:
        df_out["Licenca"] = ""

    processed_dir.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(processed_dir / "folha_consolidada.csv", sep=";", index=False, encoding="utf-8-sig")
    return df_out
