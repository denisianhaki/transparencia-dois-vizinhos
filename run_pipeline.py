"""Orquestrador único do pipeline de auditoria pública de Dois Vizinhos (PR)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.audit.rules import audit_compras, audit_diarias, audit_folha
from src.common.io import load_config
from src.ingest.compras import ingest_licitado_contratado, ingest_requisicoes
from src.ingest.diarias import ingest_diarias
from src.ingest.folha import ingest_folha
from src.report.generator import generate_reports


def main() -> None:
    root = Path(__file__).resolve().parent
    cfg = load_config(root / "config" / "regras.json")

    raw_dir = root / "data" / "raw"
    proc_dir = root / "data" / "processed"
    reports_dir = root / "reports"

    alerts: list[dict] = []
    df_folha = pd.DataFrame()
    folha_stats = None
    diarias_stats = None
    compras_stats = None

    if (raw_dir / "folha").exists() and list((raw_dir / "folha").glob("salarios*.csv")):
        df_folha = ingest_folha(raw_dir / "folha", proc_dir, cfg.get("competencia_folha", ""))
        folha_stats = audit_folha(df_folha, cfg, alerts)
        print(f"[Folha] {folha_stats['total_registros']} registros processados.")

    if (raw_dir / "diarias").exists() and list((raw_dir / "diarias").glob("EmpenhosDiariasConcedidas*.csv")):
        df_diarias = ingest_diarias(raw_dir / "diarias", proc_dir, df_folha)
        diarias_stats = audit_diarias(df_diarias, cfg, alerts)
        print(f"[Diárias] {diarias_stats['total_empenhos']} empenhos processados.")

    if (raw_dir / "compras").exists() and list((raw_dir / "compras").glob("requisicaoCompraProduto*.csv")):
        df_req = ingest_requisicoes(raw_dir / "compras", proc_dir)
        df_rel = ingest_licitado_contratado(raw_dir / "compras")
        compras_stats = audit_compras(df_req, df_rel, cfg, alerts)
        print(f"[Compras] {compras_stats['total_itens']} itens requisitados processados.")

    alerts_df = pd.DataFrame(alerts)
    outputs = generate_reports(
        reports_dir=reports_dir,
        alerts_df=alerts_df,
        folha_stats=folha_stats,
        diarias_stats=diarias_stats,
        compras_stats=compras_stats,
        municipio=cfg.get("municipio", "Município"),
    )

    print(f"[Alertas] {len(alerts_df)} alertas gerados.")
    for k, path in outputs.items():
        print(f"  -> {k}: {path}")


if __name__ == "__main__":
    main()
