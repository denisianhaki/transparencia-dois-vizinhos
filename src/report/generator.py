"""Geração automática de alertas CSV, relatório Markdown e PDF."""

from __future__ import annotations

import html
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

BROWSER_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


def _fmt_brl(val: float) -> str:
    s = f"{val:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _inline_md_to_html(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    return t


def markdown_to_pdf(md_path: Path, pdf_path: Path) -> bool:
    """Converte um arquivo Markdown em PDF estilizado usando Edge ou Chrome headless."""
    browser = next((p for p in BROWSER_CANDIDATES if p.exists()), None)
    if browser is None:
        return False

    lines = md_path.read_text(encoding="utf-8").splitlines()
    body: list[str] = []
    in_table = in_ul = in_ol = in_quote = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            body.append("</ul>")
            in_ul = False
        if in_ol:
            body.append("</ol>")
            in_ol = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            body.append("</tbody></table>")
            in_table = False

    def close_quote() -> None:
        nonlocal in_quote
        if in_quote:
            body.append("</blockquote>")
            in_quote = False

    for i, line in enumerate(lines):
        trim = line.strip()
        if not trim:
            close_lists(); close_table(); close_quote()
            continue
        if trim == "---":
            close_lists(); close_table(); close_quote()
            body.append("<hr/>")
            continue
        if trim.startswith(">"):
            close_lists(); close_table()
            q = trim.lstrip(">").strip()
            if q == "[!IMPORTANT]":
                if not in_quote:
                    body.append('<blockquote class="important">')
                    in_quote = True
                continue
            if not in_quote:
                body.append("<blockquote>")
                in_quote = True
            body.append(f"<p>{_inline_md_to_html(q)}</p>")
            continue
        close_quote()

        m_h = re.match(r"^(#{1,3})\s+(.+)$", trim)
        if m_h:
            close_lists(); close_table()
            lvl = len(m_h.group(1))
            body.append(f"<h{lvl}>{_inline_md_to_html(m_h.group(2))}</h{lvl}>")
            continue

        if trim.startswith("|") and trim.endswith("|"):
            close_lists()
            cells = [c.strip() for c in trim[1:-1].split("|")]
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue
            if not in_table:
                is_hdr = i + 1 < len(lines) and bool(re.match(r"^\|[:\-\s|]+\|$", lines[i + 1].strip()))
                body.append("<table>")
                if is_hdr:
                    body.append("<thead><tr>" + "".join(f"<th>{_inline_md_to_html(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                else:
                    body.append("<tbody><tr>" + "".join(f"<td>{_inline_md_to_html(c)}</td>" for c in cells) + "</tr>")
                in_table = True
            else:
                body.append("<tr>" + "".join(f"<td>{_inline_md_to_html(c)}</td>" for c in cells) + "</tr>")
            continue
        close_table()

        m_ol = re.match(r"^\d+\.\s+(.+)$", trim)
        if m_ol:
            if in_ul:
                body.append("</ul>"); in_ul = False
            if not in_ol:
                body.append("<ol>"); in_ol = True
            body.append(f"<li>{_inline_md_to_html(m_ol.group(1))}</li>")
            continue

        m_ul = re.match(r"^[-*]\s+(.+)$", trim)
        if m_ul:
            if in_ol:
                body.append("</ol>"); in_ol = False
            if not in_ul:
                body.append("<ul>"); in_ul = True
            body.append(f"<li>{_inline_md_to_html(m_ul.group(1))}</li>")
            continue

        close_lists()
        body.append(f"<p>{_inline_md_to_html(trim)}</p>")

    close_lists(); close_table(); close_quote()

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"/>
<style>
@page {{ size: A4; margin: 16mm 14mm; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; font-size: 9.8pt; line-height: 1.42; color: #1f2937; }}
h1 {{ font-size: 15.5pt; color: #0f172a; border-bottom: 2px solid #1e3a8a; padding-bottom: 6px; margin-top: 0; }}
h2 {{ font-size: 12pt; color: #1e3a8a; margin-top: 16px; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px; page-break-after: avoid; }}
h3 {{ font-size: 10.5pt; color: #334155; margin-top: 10px; page-break-after: avoid; }}
code {{ font-family: Consolas, monospace; font-size: 8.6pt; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }}
blockquote.important {{ margin: 10px 0; padding: 8px 12px; border-left: 4px solid #1d4ed8; background: #eff6ff; font-size: 9.2pt; }}
table {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px 0; font-size: 8.6pt; page-break-inside: avoid; }}
th, td {{ border: 1px solid #cbd5e1; padding: 4px 6px; text-align: left; }}
th {{ background: #1e3a8a; color: #fff; }}
tr:nth-child(even) td {{ background: #f8fafc; }}
</style></head><body>{"".join(body)}</body></html>"""

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8-sig") as tmp:
        tmp.write(full_html)
        tmp_path = Path(tmp.name)

    try:
        res = subprocess.run(
            [str(browser), "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", tmp_path.as_uri()],
            capture_output=True,
            check=False,
        )
        return res.returncode == 0 and pdf_path.exists()
    finally:
        tmp_path.unlink(missing_ok=True)


def generate_reports(
    reports_dir: Path,
    alerts_df: pd.DataFrame,
    folha_stats: dict[str, Any] | None,
    diarias_stats: dict[str, Any] | None,
    compras_stats: dict[str, Any] | None,
    municipio: str,
) -> dict[str, Path]:
    """Gera alertas_triagem.csv, ranking_diarias.csv, relatorio_auditoria.md e .pdf."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    alerts_path = reports_dir / "alertas_triagem.csv"
    if not alerts_df.empty:
        sev_order = {"Alta": 0, "Media": 1, "Baixa": 2}
        alerts_df = alerts_df.copy()
        alerts_df["_ord"] = alerts_df["Gravidade"].map(sev_order).fillna(9)
        alerts_df = alerts_df.sort_values(["_ord", "ValorEnvolvido"], ascending=[True, False]).drop(columns=["_ord"])
    alerts_df.to_csv(alerts_path, sep=";", index=False, encoding="utf-8-sig")
    outputs["alertas_csv"] = alerts_path

    lines: list[str] = [
        f"# Relatório Automático de Triagem — {municipio}",
        "",
        f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "> [!IMPORTANT]",
        "> **Nota Metodológica:** Os alertas abaixo representam **indícios estatísticos e documentais para triagem**, não prova automática de ilegalidade. Cada ponto deve ser validado com processos administrativos, DIOEMS e TCE-PR.",
        "",
        "---",
        "",
        "## Resumo Executivo de Alertas",
        "",
    ]

    if not alerts_df.empty:
        lines.append("| Gravidade | Quantidade | Valor Envolvido |")
        lines.append("|---|---:|---:|")
        for grav in ("Alta", "Media", "Baixa"):
            sub = alerts_df[alerts_df["Gravidade"] == grav]
            lines.append(f"| {grav} | {len(sub)} | {_fmt_brl(float(sub['ValorEnvolvido'].sum()))} |")
        lines.append("")

    if folha_stats:
        lines += [
            "## 1. Folha de Pagamento",
            f"- **Registros processados:** {folha_stats['total_registros']}",
            f"- **Total de vantagens (bruto):** {_fmt_brl(folha_stats['total_vantagens'])} | **Líquido:** {_fmt_brl(folha_stats['total_liquido'])}",
            f"- **Horas Extras:** {_fmt_brl(folha_stats['total_horas_extras'])} ({folha_stats['qtd_he_alta']} servidores acima do % de alerta)",
            f"- **Acúmulo Gratificação + HE + Outras:** {folha_stats['qtd_acumulo']} casos | **Licença com gratificação:** {folha_stats['qtd_licenca_grat']} | **Comissionado/FC com HE:** {folha_stats['qtd_comissionado_he']}",
            "",
        ]

    if diarias_stats:
        df_rank: pd.DataFrame = diarias_stats["ranking_df"]
        rank_path = reports_dir / "ranking_diarias.csv"
        df_rank.to_csv(rank_path, sep=";", index=False, encoding="utf-8-sig")
        outputs["ranking_diarias_csv"] = rank_path

        lines += [
            "## 2. Diárias Concedidas",
            f"- **Total de empenhos:** {diarias_stats['total_empenhos']} ({diarias_stats['pessoas_distintas']} pessoas) | **Valor:** {_fmt_brl(diarias_stats['valor_total'])}",
            f"- **Empenho após início da viagem:** {diarias_stats['empenho_pos_viagem']} | **Abrange Sáb/Dom:** {diarias_stats['inclui_fds']}",
            "",
            "### Top 10 Agentes Políticos e Comissionados",
            "| Nome | Perfil | Empenhos | FDS | Valor Total | Destino Principal |",
            "|---|---|---:|---:|---:|---|",
        ]
        pol = df_rank[df_rank["Perfil"].isin(["Agente Político", "Comissionado"])].head(10)
        for _, r in pol.iterrows():
            lines.append(f"| {r['ServidorNome']} | {r['Perfil']} | {r['Empenhos']} | {r['EmpenhosFds']} | {_fmt_brl(r['ValorTotal'])} | {r['PrincipalDestino']} |")
        lines.append("")

    if compras_stats:
        lines += [
            "## 3. Compras, Dispensas e Inexigibilidades",
            f"- **Itens requisitados:** {compras_stats['total_itens']} | **Valor total:** {_fmt_brl(compras_stats['valor_total'])}",
            "",
            "| Modalidade | Itens | Valor Total |",
            "|---|---:|---:|",
        ]
        for mod, row in compras_stats["por_modalidade"].iterrows():
            lines.append(f"| {mod} | {int(row['count'])} | {_fmt_brl(float(row['sum']))} |")
        lines.append("")

    if not alerts_df.empty:
        lines += [
            "## 4. Principais Alertas (Gravidade Alta)",
            "| Frente | Regra | Entidade | Referência | Valor |",
            "|---|---|---|---|---:|",
        ]
        for _, r in alerts_df[alerts_df["Gravidade"] == "Alta"].head(20).iterrows():
            lines.append(f"| {r['Frente']} | {r['Regra']} | {r['Entidade']} | {r['Referencia']} | {_fmt_brl(r['ValorEnvolvido'])} |")
        lines.append("")

    md_path = reports_dir / "relatorio_auditoria.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    outputs["relatorio_md"] = md_path

    pdf_path = reports_dir / "relatorio_auditoria.pdf"
    if markdown_to_pdf(md_path, pdf_path):
        outputs["relatorio_pdf"] = pdf_path

    return outputs
