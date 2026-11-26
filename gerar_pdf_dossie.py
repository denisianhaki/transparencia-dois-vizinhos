"""Gera PDF definitivo do dossiê Giovane Cezar Rosin."""
import sys
import html
import re
import subprocess
import tempfile
from pathlib import Path

BROWSER_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]

ALERT_CLASSES = {
    "[!CAUTION]": ("caution", "⛔ ATENÇÃO CRÍTICA"),
    "[!IMPORTANT]": ("important", "⚠️ IMPORTANTE"),
    "[!WARNING]": ("warning", "⚠️ AVISO"),
    "[!NOTE]": ("note", "📝 NOTA"),
    "[!TIP]": ("tip", "💡 DICA"),
}

def _inline(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    return t

def md_to_html(md_path: Path) -> str:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    body = []
    in_table = in_ul = in_ol = False
    in_alert = None
    alert_label = ""

    def close_all():
        nonlocal in_table, in_ul, in_ol, in_alert
        if in_ul:   body.append("</ul>"); in_ul = False
        if in_ol:   body.append("</ol>"); in_ol = False
        if in_table: body.append("</tbody></table>"); in_table = False
        if in_alert: body.append("</div>"); in_alert = None

    for i, line in enumerate(lines):
        trim = line.strip()

        # Empty line
        if not trim:
            if not in_alert:
                close_all()
            continue

        # Horizontal rule
        if trim == "---":
            close_all()
            body.append("<hr/>")
            continue

        # Blockquote / alert
        if trim.startswith(">"):
            q = trim.lstrip(">").strip()
            # Check if it's an alert marker
            if q in ALERT_CLASSES:
                if in_alert: body.append("</div>")
                cls, label = ALERT_CLASSES[q]
                body.append(f'<div class="alert {cls}"><strong>{label}</strong>')
                in_alert = cls
                continue
            else:
                if not in_alert:
                    body.append('<div class="alert note"><strong>📝 NOTA</strong>')
                    in_alert = "note"
                body.append(f"<p>{_inline(q)}</p>")
                continue

        # If we were in an alert and hit a non-quote line, close it
        if in_alert and not trim.startswith(">"):
            body.append("</div>")
            in_alert = None

        # Headings
        m = re.match(r"^(#{1,4})\s+(.+)$", trim)
        if m:
            close_all()
            lvl = len(m.group(1))
            body.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            continue

        # Code block (skip for now — not in dossie)
        if trim.startswith("```"):
            continue

        # Tables
        if trim.startswith("|") and trim.endswith("|"):
            if in_ul: body.append("</ul>"); in_ul = False
            if in_ol: body.append("</ol>"); in_ol = False
            cells = [c.strip() for c in trim[1:-1].split("|")]
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue  # separator row
            if not in_table:
                next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                is_hdr = bool(re.match(r"^\|[\:\-\s|]+\|$", next_line))
                body.append("<table>")
                if is_hdr:
                    body.append("<thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                else:
                    body.append("<tbody><tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
                in_table = True
            else:
                body.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
            continue

        # Close table on non-table line
        if in_table:
            body.append("</tbody></table>")
            in_table = False

        # Ordered list
        m_ol = re.match(r"^\d+\.\s+(.+)$", trim)
        if m_ol:
            if in_ul: body.append("</ul>"); in_ul = False
            if not in_ol: body.append("<ol>"); in_ol = True
            body.append(f"<li>{_inline(m_ol.group(1))}</li>")
            continue

        # Unordered list
        m_ul = re.match(r"^[-*]\s+(.+)$", trim)
        if m_ul:
            if in_ol: body.append("</ol>"); in_ol = False
            if not in_ul: body.append("<ul>"); in_ul = True
            body.append(f"<li>{_inline(m_ul.group(1))}</li>")
            continue

        # Close lists on paragraph
        if in_ul: body.append("</ul>"); in_ul = False
        if in_ol: body.append("</ol>"); in_ol = False

        body.append(f"<p>{_inline(trim)}</p>")

    close_all()
    return "\n".join(body)


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    padding: 20mm 18mm;
    max-width: 100%;
}
h1 {
    font-size: 18pt;
    color: #7b0000;
    border-bottom: 3px solid #7b0000;
    padding-bottom: 6px;
    margin-bottom: 12px;
    margin-top: 24px;
    page-break-after: avoid;
}
h2 {
    font-size: 13pt;
    color: #2c3e50;
    border-left: 4px solid #c0392b;
    padding-left: 10px;
    margin: 20px 0 10px 0;
    page-break-after: avoid;
}
h3 {
    font-size: 11.5pt;
    color: #34495e;
    margin: 16px 0 8px 0;
    page-break-after: avoid;
}
h4 {
    font-size: 11pt;
    color: #555;
    margin: 12px 0 6px 0;
    font-style: italic;
}
p { margin-bottom: 8px; }
hr {
    border: none;
    border-top: 1.5px solid #ccc;
    margin: 16px 0;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 14px 0;
    font-size: 9.5pt;
    page-break-inside: auto;
}
thead { background: #2c3e50; color: #fff; }
thead th { padding: 7px 8px; text-align: left; }
tbody tr:nth-child(even) { background: #f5f5f5; }
tbody tr:hover { background: #eaf0fb; }
td, th { padding: 5px 8px; border: 1px solid #ddd; vertical-align: top; }
ul, ol { margin: 6px 0 10px 22px; }
li { margin-bottom: 3px; }
code {
    background: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: 'Consolas', monospace;
    font-size: 9pt;
}
strong { color: #1a1a1a; }
em { color: #555; }

/* Alerts */
.alert {
    border-radius: 5px;
    padding: 10px 14px;
    margin: 12px 0;
    page-break-inside: avoid;
}
.alert strong { display: block; margin-bottom: 5px; font-size: 10.5pt; }
.alert p { margin: 3px 0; font-size: 10pt; }
.alert.caution  { background: #fff0f0; border-left: 5px solid #c0392b; }
.alert.caution strong { color: #7b0000; }
.alert.important { background: #fff8e1; border-left: 5px solid #e67e22; }
.alert.important strong { color: #7d4e00; }
.alert.warning  { background: #fffde7; border-left: 5px solid #f39c12; }
.alert.warning strong { color: #7a5500; }
.alert.note     { background: #e8f4fd; border-left: 5px solid #2980b9; }
.alert.note strong { color: #174a6e; }

/* Cover header */
.cover {
    text-align: center;
    padding: 30px 0 20px 0;
    border-bottom: 3px double #7b0000;
    margin-bottom: 24px;
}
.cover .badge {
    display: inline-block;
    background: #7b0000;
    color: white;
    padding: 4px 18px;
    border-radius: 20px;
    font-size: 10pt;
    font-weight: bold;
    margin-bottom: 10px;
    letter-spacing: 1px;
}
.cover h1 {
    border: none;
    font-size: 22pt;
    margin: 6px 0;
}
.cover .sub {
    font-size: 12pt;
    color: #555;
    margin: 4px 0;
}
.cover .meta {
    font-size: 9.5pt;
    color: #888;
    margin-top: 10px;
}

@media print {
    h1, h2, h3 { page-break-after: avoid; }
    table { page-break-inside: auto; }
    tr { page-break-inside: avoid; }
    .alert { page-break-inside: avoid; }
}
"""

def build_pdf(md_path: Path, pdf_path: Path) -> bool:
    browser = next((p for p in BROWSER_CANDIDATES if p.exists()), None)
    if not browser:
        print("ERRO: Nenhum browser (Edge/Chrome) encontrado.")
        return False

    body_html = md_to_html(md_path)

    cover = """
    <div class="cover">
        <div class="badge">DOSSIÊ DE INVESTIGAÇÃO — CONFIDENCIAL</div>
        <div class="sub">Prefeitura Municipal de Dois Vizinhos — PR</div>
        <div class="sub"><strong>Período:</strong> Janeiro a Novembro de 2026</div>
        <div class="meta">
            Fonte: Portal da Transparência (Equiplano) | 
            Análise: Pipeline Python — github.com/denisianhaki/transparencia-dois-vizinhos<br/>
            Elaborado em: 26/11/2026
        </div>
    </div>
    """

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<style>{CSS}</style>
</head>
<body>
{cover}
{body_html}
</body>
</html>"""

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(full_html)
        tmp_html = f.name

    cmd = [
        str(browser),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        "--print-to-pdf-no-header",
        "--no-pdf-header-footer",
        f"file:///{tmp_html}",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    Path(tmp_html).unlink(missing_ok=True)

    if pdf_path.exists() and pdf_path.stat().st_size > 1000:
        print(f"✅ PDF gerado: {pdf_path}")
        print(f"   Tamanho: {pdf_path.stat().st_size / 1024:.1f} KB")
        return True
    else:
        print(f"ERRO ao gerar PDF. Código: {result.returncode}")
        print(result.stderr.decode(errors="replace")[:500])
        return False


if __name__ == "__main__":
    md_path = Path(r"C:\Users\denis.ianhak\.gemini\antigravity\brain\1d1a491e-c078-41af-a955-32c28f1fa1fc\dossie_giovane_rosin.md")
    pdf_path = Path(r"C:\Users\denis.ianhak\.gemini\antigravity\brain\1d1a491e-c078-41af-a955-32c28f1fa1fc\dossie_giovane_rosin.pdf")

    print(f"Convertendo: {md_path.name}")
    ok = build_pdf(md_path, pdf_path)
    if not ok:
        sys.exit(1)
