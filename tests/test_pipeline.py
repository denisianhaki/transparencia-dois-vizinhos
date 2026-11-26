"""Testes automatizados para os utilitários e regras de auditoria."""

from datetime import date
from pathlib import Path

import pandas as pd

from src.audit.rules import audit_compras, audit_diarias, audit_folha
from src.common.io import parse_ptbr_date, parse_ptbr_decimal


def test_parse_ptbr_decimal() -> None:
    assert parse_ptbr_decimal("12.500,00") == 12500.0
    assert parse_ptbr_decimal("0,00") == 0.0
    assert parse_ptbr_decimal("4908.20") == 4908.20
    assert parse_ptbr_decimal("") == 0.0
    assert parse_ptbr_decimal(None) == 0.0


def test_parse_ptbr_date() -> None:
    assert parse_ptbr_date("02/09/2026") == date(2026, 9, 2)
    assert parse_ptbr_date("DATA: 28/08/2026") == date(2026, 8, 28)
    assert parse_ptbr_date("invalida") is None


def test_audit_folha_flags_he_and_licenca() -> None:
    df = pd.DataFrame([
        {
            "Matricula": "1", "Nome": "João", "Vinculo": "Efetivo", "Cargo": "Motorista",
            "FuncaoConfianca": "", "Lotacao": "Saúde", "Licenca": "Não",
            "Vencimento": 1000.0, "Gratificacoes": 100.0, "HorasExtras": 500.0,
            "PctHE_Sobre_Venc": 50.0, "OutrasVantagens": 50.0, "TotalVantagens": 1650.0,
            "TotalLiquido": 1400.0,
        },
        {
            "Matricula": "2", "Nome": "Maria", "Vinculo": "Efetivo", "Cargo": "Professor",
            "FuncaoConfianca": "", "Lotacao": "Ensino", "Licenca": "Sim",
            "Vencimento": 2000.0, "Gratificacoes": 200.0, "HorasExtras": 0.0,
            "PctHE_Sobre_Venc": 0.0, "OutrasVantagens": 0.0, "TotalVantagens": 2200.0,
            "TotalLiquido": 1900.0,
        },
    ])
    alerts: list = []
    cfg = {"regras_folha": {"percentual_alerta_hora_extra": 40.0, "cargos_acumulaveis_regex": "Prof", "alertar_licenca_com_gratificacao": True}}
    stats = audit_folha(df, cfg, alerts)
    assert stats["qtd_he_alta"] == 1
    assert stats["qtd_acumulo"] == 1
    assert stats["qtd_licenca_grat"] == 1
    assert len(alerts) == 3


def test_audit_compras_flags_dispensa_teto_e_repeticao() -> None:
    df_req = pd.DataFrame([
        {"FornecedorNome": "EMPRESA X", "Modalidade": "Dispensa", "Licitacao": "Dispensa 90001 / 2026", "Total": 40000.0},
        {"FornecedorNome": "EMPRESA X", "Modalidade": "Dispensa", "Licitacao": "Dispensa 90002 / 2026", "Total": 30000.0},
    ])
    alerts: list = []
    cfg = {"regras_compras": {"teto_dispensa_servicos_compras": 62725.59, "alerta_concentracao_fornecedor_pct": 99.0}}
    audit_compras(df_req, pd.DataFrame(), cfg, alerts)
    regras = {a["Regra"] for a in alerts}
    assert any("acima do teto" in r for r in regras)
    assert any("Múltiplas dispensas" in r for r in regras)


def test_processed_outputs_exist_when_pipeline_ran() -> None:
    root = Path(__file__).resolve().parent.parent
    assert (root / "reports" / "alertas_triagem.csv").exists()
    assert (root / "reports" / "relatorio_auditoria.md").exists()
