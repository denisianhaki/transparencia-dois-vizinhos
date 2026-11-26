# Relatório Técnico de Triagem de Anomalias — Município de Dois Vizinhos (PR)

**Data de emissão:** 26/11/2026  
**Escopo analisado:** Dados públicos exportados do Portal da Transparência de Dois Vizinhos (Folha/Quadro Funcional de Setembro/2026; Diárias e Requisições de Compra de 01/01/2026 a 26/11/2026; Itens Licitados vs. Contratados; Orçamento LOA 2026).

> [!IMPORTANT]
> **Nota Metodológica:** Anomalias estatísticas, concentrações de valores ou padrões documentais identificados neste relatório constituem **indícios técnicos para triagem e fiscalização**, não equivalendo automaticamente a ilegalidade ou corrupção. A validação conclusiva exige o confronto de cada achado com os processos administrativos correspondentes, publicações no **DIOEMS** (`dioems.com.br`), legislação municipal (`doisvizinhos.pr.gov.br`) e apontamentos do **TCE-PR**.

---

## Fontes Processadas

| Frente | Arquivo Bruto (`data/raw/`) | Base Tratada (`data/processed/`) | Registros |
|---|---|---|---:|
| Quadro Funcional (Set/2026) | `quadroFuncional26_11_2026_13_50_00.csv` | `quadro_funcional_2026_09.csv` | 1.321 |
| Folha / Salários (Set/2026) | `salarios.csv` + `relaçãoServidoresSetembro.csv` | `folha_consolidada_2026_09.csv` | 1.323 |
| Diárias (Jan–Nov/2026) | `EmpenhosDiariasConcedidas.csv` | `diarias_2026_anual.csv` / `ranking_diarias_2026.csv` | 1.740 (205 pessoas) |
| Requisições de Compra (Jan–Nov/2026) | `requisicaoCompraProduto.csv` | `requisicoes_compra_2026.csv` | 17.142 |
| Licitado vs. Contratado | `rel (4).csv` | — | 2.011 |
| Planejamento Orçamentário (LOA 2026) | `OrcSumarioGeralReceitasDespesas.csv` / `OrcQuadroDetDespesaOrcamentaria.csv` | — | — |

---

## 1. Folha de Pagamento e Quadro Funcional (Setembro/2026)

### Panorama Geral
- **Total de vantagens (bruto):** R$ 9.644.680,51 | **Total líquido:** R$ 6.737.466,77
- **Vencimentos:** R$ 7.830.090,93 | **Gratificações:** R$ 395.827,87 | **Grat. Assiduidade:** R$ 135.420,30 | **Horas Extras:** R$ 238.879,35 | **Outras Vantagens:** R$ 854.711,74
- **Pontos conformes na triagem:** **0** comissionados ou agentes políticos recebendo horas extras/gratificações; **0** servidores com `Função de Confiança` recebendo horas extras.

### Indícios para Triagem

1. **Horas Extras entre 40% e ~60% do vencimento base (Setembro/2026):**
   Concentradas no **Fundo Municipal de Saúde** e no **Departamento de Serviços Urbanos**. Embora compatíveis com escalas operacionais em tese, a proporção elevada exige verificar em outros meses se há pagamento habitual no teto legal:
   - `87601` — **Rogerio Luis Nunes** (Técnico em Agropecuária / Serviços Urbanos): Venc. R$ 20.478,33 | HE **R$ 8.524,10 (41,6%)**
   - `46501` — **Itamar Jose Frantz** (Motorista / Saúde): Venc. R$ 13.318,74 | HE **R$ 7.415,21 (55,7%)**
   - `178941` — **Marli Rochemback** (Enfermeiro / Saúde): Venc. R$ 12.608,42 | HE **R$ 7.152,29 (56,7%)**
   - `32041` — **Jose Joel Tomaz de Santiago** (Operário / Serviços Urbanos): Venc. R$ 9.997,90 | HE **R$ 5.793,78 (57,9%)**
   - `133221` — **Jose Gilvani Bertholdo** (Aux. de Enfermagem / Saúde): Venc. R$ 8.773,86 | HE **R$ 5.027,01 (57,3%)**
   - `131541` — **Vanderlei Venassi** (Motorista / Saúde): Venc. R$ 8.619,28 | HE **R$ 4.908,20 (56,9%)**
   - `133331` — **Marivone Belusso** (Aux. de Enfermagem / Saúde): Venc. R$ 8.464,89 | HE **R$ 4.813,24 (56,9%)**
   - `198241` — **Natiele Luize Maronesi** (Enfermeiro / Saúde): Venc. R$ 7.115,81 | HE **R$ 4.248,76 (59,7%)**

2. **Acúmulo simultâneo de `Gratificações > 0` + `Horas Extras > 0` + `Outras Vantagens > 0`:**
   Identificados **8 servidores** nessa condição (6 no Depto. de Serviços Urbanos e 2 na Saúde), com destaque para `32041` Jose Joel Tomaz de Santiago (Total Vantagens R$ 20.112,39) e `133701` Nelson de Farias (Total Vantagens R$ 13.962,76).

3. **Servidores com `Licença = Sim` recebendo `Gratificações > 0` (4 casos):**
   - `185121` **Dieli Geremia Pandolfi** (Agente Administrativo — Grat. R$ 614,39)
   - `179471` **Keli Cristina de Oliveira** (Professor — Grat. R$ 270,47)
   - `179421` **Regiane Cristina Hablich** (Professor — Grat. R$ 270,47)
   - `187621` **Sheila Maria Leite da Silva** (Professor — Grat. R$ 428,70)
   *Ação:* conferir no Estatuto dos Servidores e no DIOEMS qual o tipo de licença e se há amparo legal para manutenção da gratificação durante o afastamento.

---

## 2. Diárias Concedidas (01/01/2026 a 26/11/2026)

### Panorama Geral
- **Total empenhado:** **R$ 958.063,16** em **1.740 empenhos** (205 beneficiários distintos).
- **Picos mensais:** **Fevereiro (R$ 129.362,65)** e **Março (R$ 134.459,37)** — aproximadamente o dobro de Janeiro (R$ 62.668,74) e Julho (R$ 69.816,76).

### Indícios para Triagem

1. **Inversão sistemática de estágio — Empenho posterior ao início da viagem (90,4%):**
   - **1.573 dos 1.740 empenhos** têm `DataEmpenho` posterior à `DataInicialViagem` registrada na liquidação.
   - *Ação:* verificar se a legislação municipal (`Lei 1662/2011` / `Lei 2619/2022`) prevê regime indenizatório/ressarcimento posterior e se esse procedimento tem respaldo nos pareceres do TCE-PR frente ao art. 60 da Lei nº 4.320/1964 (prévio empenho).

2. **Liderança absoluta de servidor comissionado no ranking geral:**
   - **Giovane Cezar Rosin** (Comissionado — Chefe de Relações Políticas e Institucionais) é o **1º lugar geral do município** em valor de diárias em 2026: **R$ 47.110,89** em **49 empenhos** distribuídos pelos **11 meses** (superando todos os motoristas de ambulância/transporte).
   - **30 viagens** tiveram como destino **Curitiba - PR**, e **13 empenhos** abrangeram sábado ou domingo — incluindo viagens em sequência na mesma semana ou em semanas seguidas (ex.: `22/01 a 24/01` e `27/01 a 29/01`; `19/08 a 22/08` e `23/08 a 26/08`; `06/05 a 08/05` e `10/05 a 12/05`).
   - *Ação:* solicitar/conferir relatórios de viagem, atas de reuniões e agendas institucionais em Curitiba que comprovem o interesse público e a finalidade de cada deslocamento, especialmente os de fim de semana.

3. **Demais Agentes Políticos e Comissionados com maior volume:**
   - **Luis Carlos Turatto** (Prefeito Municipal): **R$ 36.310,17** (30 empenhos em 9 meses; 6 em FDS; Curitiba 13×).
   - **Claudete Meurer** (Agente Político): **R$ 14.412,52** (16 empenhos em 11 meses; Francisco Beltrão 8×).
   - **Lucas Souvenir Antonello** (Agente Político): **R$ 11.704,41** (11 empenhos em 5 meses; 6 em FDS).
   - **Leda Maria Ferrari** (Agente Político): **R$ 11.605,33** (8 empenhos em 7 meses).
   - **Bruno Dambros** (Comissionado): **R$ 7.490,96** (19 empenhos em 10 meses, sendo **10 em fins de semana**).

4. **Alto volume de diárias + horas extras em Motoristas e Enfermagem:**
   - **51,1% (890 empenhos)** abrangem sábado ou domingo.
   - Motoristas no topo do ranking acumulam **167 a 218 diárias** no ano (ex.: `Rafael Muttoni` R$ 39.153,66; `Jocemar Aloisio Assmann` R$ 28.725,65; `Vanderlei Venassi` R$ 26.787,71; `Valdecir da Silva` com 218 diárias), além de horas extras expressivas na folha de Setembro/2026 (`Vanderlei Venassi` R$ 4.908,20; `Leocir Paulo Tranker` R$ 3.789,30; `Adenilso Vieira Schmitz` R$ 3.609,32).
   - Na enfermagem, `Micheli Szczepkowski Favero` (R$ 11.055,24; 25 FDS) e `Jose Gilvani Bertholdo` (R$ 8.800,39; 18 FDS + R$ 5.027,01 de HE em Set/26) também acumulam ambos.
   - *Ação:* cruzar folhas-ponto com os dias exatos de diária para descartar eventual sobreposição de pagamento de hora extra durante período já coberto por diária integral.

---

## 3. Compras, Dispensas e Inexigibilidades (01/01/2026 a 26/11/2026)

### Panorama Geral
- **Total requisitado:** **R$ 165.480.776,56** (17.142 itens)
  - Pregão: R$ 63.489.794,25 (174 processos) | Concorrência: R$ 57.387.685,95 (29 processos)
  - **Inexigibilidade:** **R$ 39.444.236,41** (83 processos — **23,8% do total**)
  - **Dispensa:** **R$ 4.624.792,74** (46 processos)
  - Tomada de Preços: R$ 534.267,21 (3 processos)

### Indícios para Triagem

1. **Dispensa de R$ 406 mil para estrutura de eventos (`Dispensa 90015 / 2026`):**
   - Fornecedor: **`ECCO'S PRODUÇÕES E EVENTOS LTDA`** — **R$ 406.003,85** em uma única requisição (`101882`, de `25/05/2026`, 36 itens: pavilhão R$ 44.167,20, sonorização R$ 32.098,80, iluminação R$ 21.060,81, painel de LED R$ 19.083,60, estandes, tendas, geradores, climatizadores, treliça).
   - *Ação:* valor muito superior ao teto de dispensa por baixo valor (art. 75, II, da Lei nº 14.133/2021). Verificar no processo/DIOEMS qual hipótese legal foi invocada (emergência, licitação deserta/fracassada) e se houve pesquisa de preços adequada.

2. **Possível fracionamento ou repetição de dispensas em Eventos e Esportes:**
   - **`XUXU EVENTOS LTDA`:** **R$ 76.500,00** em **2 dispensas no mesmo ano** para serviço de buffet (`Dispensa 90011 / 2026` em `28/04/2026` — R$ 45.000,00; `Dispensa 90027 / 2026` em `26/10/2026` — R$ 31.500,00). A soma ultrapassa o limite anual de dispensa por valor para serviços comuns da Lei nº 14.133/2021. Somando à dispensa da Ecco's Produções, o município requisitou **R$ 482.503,85** em eventos via dispensa em 2026.
   - **`JEVERSON IVAN PAESE - PITTY SPORTS`:** **R$ 40.032,40** em **2 dispensas em 2026** com intervalo de ~35 dias (`Dispensa 90006 / 2026` em `09/04/2026` e `Dispensa 90014 / 2026` em `14/05/2026`), mesmo possuindo atas de pregão vigentes no mesmo período.

3. **Dispensa de R$ 2,01 milhões com descrição genérica (`Dispensa 90001 / 2025`):**
   - Fornecedor: **`INSTITUTO ALICERCE`** — **R$ 2.010.969,05** em 15 requisições em 2026, todas lançadas genericamente como `"CONTRATAÇÃO DE INSTITUIÇÃO ESPECIALIZADA"`.
   - Padrão de repasses mensais regulares de **R$ 117.921,45**, interrompido por um pico atípico em `20/10/2026` (`Req 105489`) de **R$ 647.718,94**.
   - *Ação:* conferir o termo/contrato completo, enquadramento no art. 75, XV (ou MROSC — Lei nº 13.019/2014), objeto efetivo, justificativa do aporte de R$ 647,7 mil em outubro e prestação de contas.

4. **Inexigibilidade de R$ 2,92 milhões em material didático/gráfico (`Inexigibilidade 54 / 2024`):**
   - Fornecedor: **`GRAFICA E EDITORA POSIGRAF LTDA`** — **R$ 2.927.183,70** em 2026 (34 itens — Sistema Aprende Brasil).
   - *Ação:* verificar o laudo/atestado de exclusividade e justificativa de preço frente a alternativas de mercado.

5. **Concentração de obras em único fornecedor:**
   - **`JIRAU ALTO INCORPORADORA E CONSTRUTORA LTDA`** concentra **R$ 32.450.032,80** (39 itens via Concorrência) — cerca de **19,6%** de todo o valor requisitado pelo município no período.
   - *Ação:* acompanhar medições, aditivos de prazo/valor e execução física das obras.

6. **Acréscimos em `rel (4).csv` (Licitado vs. Contratado):**
   - Dos 2.011 itens, 4 itens reais de **Arbitragem** apresentaram `Valor Total Contratado` cerca de **+4,39%** acima do `Valor Total Licitado` (compatível com reajuste/aditivo dentro do limite legal, a confirmar nos termos aditivos).

---

## 4. Próximos Passos Recomendados

1. **Coletar no Portal da Transparência / DIOEMS (`dioems.com.br`):**
   - Íntegra dos processos/extratos de **`Dispensa 90015 / 2026`** (Ecco's), **`Dispensa 90011` e `90027 / 2026`** (Xuxu Eventos), **`Dispensa 90001 / 2025`** (Instituto Alicerce) e **`Inexigibilidade 54 / 2024`** (Posigraf).
   - **Relação Geral de Empenhos/Pagamentos de 2026** (com CNPJ e data de liquidação/pagamento) para verificar inversão de estágios em despesas gerais e cruzar sócios/endereços dos fornecedores.
   - **Contratos e Termos Aditivos (2024–2026)** para auditar acréscimos próximos a 25%/50% (especialmente obras).
2. **Coletar `salarios.csv` de mais 3–5 meses de 2026** para confirmar se as horas extras de ~55–60% são eventuais ou sistemáticas.
3. **Consultar o Mural de Licitações e alertas do TCE-PR** para Dois Vizinhos no exercício de 2026.
