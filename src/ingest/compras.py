"""Ingestão de Requisições de Compra e Itens Licitados vs. Contratados."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.io import detect_encoding, find_latest_csv, parse_ptbr_decimal

PRODUTO_COD_RE = re.compile(r"^Produto:\s*(\d+)\s+(.+)$")
PRODUTO_SEM_COD_RE = re.compile(r"^Produto:\s*(.+)$")
FORNECEDOR_RE = re.compile(r"Fornecedor:\s*(\d+)\s+(.+)$")
CONTRATO_RE = re.compile(r"^\d+\s*/\s*\d{4}$")


def _classify_modalidade(licitacao: str) -> str:
    if not licitacao:
        return "Não informada"
    for mod in ("Dispensa", "Inexigibilidade", "Pregão", "Concorrência", "Tomada"):
        if licitacao.startswith(mod):
            return mod
    if licitacao.startswith(("Adesão", "Carona")):
        return "Adesão/Carona"
    return licitacao.split()[0]


def ingest_requisicoes(raw_compras_dir: Path, processed_dir: Path) -> pd.DataFrame:
    """Limpa o relatório requisicaoCompraProduto*.csv para tabela plana."""
    path = find_latest_csv(raw_compras_dir, "requisicaoCompraProduto*.csv")
    if not path:
        raise FileNotFoundError(f"Nenhum arquivo requisicaoCompraProduto*.csv encontrado em {raw_compras_dir}")

    enc = detect_encoding(path)
    records: list[dict[str, Any]] = []
    cur_prod_cod = ""
    cur_prod_desc = ""
    pending: dict[str, Any] | None = None

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
                    "TOTAIS REQUISITADOS POR PRODUTO",
                    "PERÍODO:",
                    "Página:",
                )
            ) or re.search(r"Requisição\s*\|\s*Data", line_join):
                continue

            c0 = fields[0].strip()
            m_prod = PRODUTO_COD_RE.match(c0)
            if m_prod:
                cur_prod_cod = m_prod.group(1).strip()
                cur_prod_desc = m_prod.group(2).strip()
                continue
            m_prod2 = PRODUTO_SEM_COD_RE.match(c0)
            if m_prod2:
                cur_prod_cod = ""
                cur_prod_desc = m_prod2.group(1).strip()
                continue

            m_forn = FORNECEDOR_RE.search(line_join)
            if m_forn and pending is not None:
                pending["FornecedorCodigo"] = m_forn.group(1).strip()
                pending["FornecedorNome"] = re.sub(r"\|.*$", "", m_forn.group(2)).strip()
                records.append(pending)
                pending = None
                continue

            if (
                len(non_empty) >= 4
                and re.match(r"^\d+$", non_empty[0])
                and re.match(r"^\d{2}/\d{2}/\d{4}$", non_empty[1])
            ):
                if pending is not None:
                    records.append(pending)
                    pending = None

                qtd = parse_ptbr_decimal(non_empty[-3])
                unit = parse_ptbr_decimal(non_empty[-2])
                tot = parse_ptbr_decimal(non_empty[-1])

                contrato = ""
                licitacao = ""
                for val in non_empty[2:-3]:
                    if CONTRATO_RE.match(val) and not contrato:
                        contrato = re.sub(r"\s+", "", val)
                    else:
                        licitacao = re.sub(r"\s{2,}", " ", val).strip()

                pending = {
                    "ProdutoCodigo": cur_prod_cod,
                    "ProdutoDescricao": cur_prod_desc,
                    "Requisicao": non_empty[0],
                    "Data": non_empty[1],
                    "Contrato": contrato,
                    "Licitacao": licitacao,
                    "Modalidade": _classify_modalidade(licitacao),
                    "Quantidade": qtd,
                    "PrecoUnitario": unit,
                    "Total": tot,
                    "FornecedorCodigo": "",
                    "FornecedorNome": "",
                }

    if pending is not None:
        records.append(pending)

    df = pd.DataFrame(records)
    processed_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_dir / "requisicoes_compra.csv", sep=";", index=False, encoding="utf-8-sig")
    return df


def ingest_licitado_contratado(raw_compras_dir: Path) -> pd.DataFrame:
    """Lê o arquivo de itens licitados vs. contratados (rel*.csv), tolerando ';' no nome do produto."""
    path = find_latest_csv(raw_compras_dir, "rel*.csv")
    if not path:
        return pd.DataFrame()
    enc = detect_encoding(path)
    rows: list[list[str]] = []
    with path.open("r", encoding=enc, newline="") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        header = next(reader, None)
        if not header:
            return pd.DataFrame()
        n_cols = len(header)
        for row in reader:
            if len(row) == n_cols:
                rows.append(row)
            elif len(row) > n_cols:
                # Reconstrói descrição do produto quando há ';' sem aspas
                merged_prod = ";".join(row[: len(row) - (n_cols - 1)])
                rows.append([merged_prod] + row[-(n_cols - 1) :])
    df = pd.DataFrame(rows, columns=header).fillna("")
    for col in ("Quant. Licitada", "Valor Total Licitado", "Quant. Contratada", "Valor Total Contratado"):
        if col in df.columns:
            df[f"{col}_num"] = df[col].map(parse_ptbr_decimal)
    return df
