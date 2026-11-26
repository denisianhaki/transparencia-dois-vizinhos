# Transparência Dois Vizinhos (PR)

Projeto para estruturação, cruzamento e análise exploratória de dados públicos do município de **Dois Vizinhos (PR)** a partir do Portal da Transparência, do Diário Oficial Eletrônico (DIOEMS), da legislação municipal e de bases do TCE-PR.

> **Nota metodológica:** Anomalias estatísticas ou documentais identificadas em cruzamentos de dados funcionam exclusivamente como **indícios para triagem técnica**, não equivalendo automaticamente a irregularidade ou ilegalidade. Qualquer achado deve ser confrontado com portarias, leis municipais, contratos e processos administrativos.

## Estrutura do Projeto

- `data/raw/` — Arquivos brutos exportados (CSVs/planilhas do Portal da Transparência). Ignorados no Git por padrão.
- `data/processed/` — Bases tratadas e consolidadas para cruzamento.
- `scripts/` — Scripts de limpeza, padronização e cruzamento de dados.
- `docs/` — Referências normativas, dicionários de dados e notas de análise.

## Frentes de Análise

1. **Folha de Pagamento e RH:** acúmulo de rubricas/gratificações, horas extras recorrentes, desvio de função via lotação e diárias.
2. **Licitações, Dispensas e Contratos (Lei nº 14.133/2021):** fracionamento de despesas, aditivos próximos aos limites legais, concentração de fornecedores e adesões a atas.
3. **Execução Orçamentária:** inversão de estágios da despesa (Lei nº 4.320/1964) e repasses ao terceiro setor (Lei nº 13.019/2014).
4. **Cruzamentos Externos:** DIOEMS (`dioems.com.br`), Atos Públicos/Legislação Municipal (`doisvizinhos.pr.gov.br`) e TCE-PR.
