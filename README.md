# Transparência Dois Vizinhos (PR)

Pipeline automatizado em Python (`pandas` + `pytest`) para ingestão, limpeza, cruzamento de bases e triagem de anomalias nos dados públicos do município de **Dois Vizinhos (PR)** (Portal da Transparência / Equiplano, DIOEMS e TCE-PR).

> **Nota metodológica:** Anomalias estatísticas ou documentais identificadas pelo pipeline funcionam exclusivamente como **indícios técnicos para triagem**, não equivalendo automaticamente a irregularidade ou ilegalidade. Qualquer achado deve ser confrontado com processos administrativos, DIOEMS (`dioems.com.br`), legislação municipal (`doisvizinhos.pr.gov.br`) e TCE-PR.

## Estrutura do Projeto

```text
transparencia-dois-vizinhos/
├── config/
│   └── regras.json          # Limites legais (Lei 14.133), % de HE e parâmetros de alerta
├── data/
│   ├── raw/                 # CSVs brutos do portal (folha/, diarias/, compras/, orcamento/)
│   └── processed/           # Bases consolidadas geradas pelo pipeline
├── src/
│   ├── common/              # Utilitários de encoding, datas e moeda PT-BR
│   ├── ingest/              # Parsers por domínio (folha, diárias, compras)
│   ├── audit/               # Motor de regras parametrizáveis de triagem
│   └── report/              # Gerador automático de CSV de alertas, Markdown e PDF
├── reports/                 # Saídas geradas (alertas_triagem.csv, ranking_diarias.csv, relatorio_auditoria.md/.pdf)
├── docs/                    # Documentação e relatórios arquivados
├── tests/                   # Testes automatizados (pytest)
└── run_pipeline.py          # Ponto único de execução
```

## Como Usar

1. Salve as planilhas CSV baixadas do Portal da Transparência nas subpastas correspondentes em `data/raw/`:
   - `data/raw/folha/` (`salarios*.csv`, `quadroFuncional*.csv`, `*Servidores*.csv`)
   - `data/raw/diarias/` (`EmpenhosDiariasConcedidas*.csv`)
   - `data/raw/compras/` (`requisicaoCompraProduto*.csv`, `rel*.csv`)
2. Execute o pipeline completo com um único comando:
   ```powershell
   .\.venv\Scripts\python.exe run_pipeline.py
   ```
3. Consulte os resultados gerados em `reports/`:
   - `reports/alertas_triagem.csv` (todos os alertas ordenados por gravidade e valor, pronto para Excel)
   - `reports/ranking_diarias.csv` (ranking por perfil: Agentes Políticos, Comissionados, Motoristas e Efetivos)
   - `reports/relatorio_auditoria.md` e `reports/relatorio_auditoria.pdf`

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```
