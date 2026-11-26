"""Regras parametrizáveis de triagem para Folha, Diárias e Compras."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _add_alert(
    alerts: list[dict[str, Any]],
    frente: str,
    gravidade: str,
    regra: str,
    entidade: str,
    referencia: str,
    valor: float,
    detalhe: str,
) -> None:
    alerts.append(
        {
            "Frente": frente,
            "Gravidade": gravidade,
            "Regra": regra,
            "Entidade": entidade,
            "Referencia": referencia,
            "ValorEnvolvido": round(float(valor), 2),
            "Detalhe": detalhe,
        }
    )


def audit_folha(df_folha: pd.DataFrame, cfg: dict[str, Any], alerts: list[dict[str, Any]]) -> dict[str, Any]:
    """Executa regras de triagem na folha consolidada."""
    rf = cfg.get("regras_folha", {})
    pct_he = float(rf.get("percentual_alerta_hora_extra", 40.0))
    acum_regex = rf.get("cargos_acumulaveis_regex", "Prof")

    # 1. Horas extras acima do percentual configurado
    he_high = df_folha[df_folha["PctHE_Sobre_Venc"] >= pct_he].sort_values("HorasExtras", ascending=False)
    for _, r in he_high.iterrows():
        _add_alert(
            alerts, "Folha", "Media",
            f"Hora extra >= {pct_he:.0f}% do vencimento",
            f"{r['Matricula']} - {r['Nome']}", r["Lotacao"], r["HorasExtras"],
            f"{r['Cargo']} | Venc: R$ {r['Vencimento']:,.2f} | HE: {r['PctHE_Sobre_Venc']}%",
        )

    # 2. Acúmulo simultâneo de Gratificações + Horas Extras + Outras Vantagens
    acum = df_folha[
        (df_folha["Gratificacoes"] > 0) & (df_folha["HorasExtras"] > 0) & (df_folha["OutrasVantagens"] > 0)
    ].sort_values("TotalVantagens", ascending=False)
    for _, r in acum.iterrows():
        _add_alert(
            alerts, "Folha", "Media",
            "Acúmulo Gratificações + HE + Outras Vantagens",
            f"{r['Matricula']} - {r['Nome']}", r["Lotacao"], r["TotalVantagens"],
            f"{r['Cargo']} | Grat: R$ {r['Gratificacoes']:,.2f} | HE: R$ {r['HorasExtras']:,.2f} | Outras: R$ {r['OutrasVantagens']:,.2f}",
        )

    # 3. Licença = Sim com Gratificações > 0 ou HE > 0
    if rf.get("alertar_licenca_com_gratificacao", True):
        lic = df_folha[(df_folha["Licenca"] == "Sim") & ((df_folha["Gratificacoes"] > 0) | (df_folha["HorasExtras"] > 0))]
        for _, r in lic.iterrows():
            _add_alert(
                alerts, "Folha", "Alta",
                "Servidor em licença recebendo gratificação ou HE",
                f"{r['Matricula']} - {r['Nome']}", r["Cargo"], r["Gratificacoes"] + r["HorasExtras"],
                f"Grat: R$ {r['Gratificacoes']:,.2f} | HE: R$ {r['HorasExtras']:,.2f}",
            )

    # 4. Comissionados / Agentes Políticos / Função de Confiança com HE
    com_he = df_folha[
        (df_folha["Vinculo"].isin(["Comissionado", "Agente Político"]) & ((df_folha["HorasExtras"] > 0) | (df_folha["Gratificacoes"] > 0)))
        | ((df_folha["FuncaoConfianca"].str.strip() != "") & (df_folha["HorasExtras"] > 0))
    ]
    for _, r in com_he.iterrows():
        _add_alert(
            alerts, "Folha", "Alta",
            "Comissionado/Político/FC com HE ou Gratificação",
            f"{r['Matricula']} - {r['Nome']}", r["Vinculo"], r["HorasExtras"] + r["Gratificacoes"],
            f"{r['Cargo']} | FC: {r['FuncaoConfianca']}",
        )

    # 5. Múltiplos vínculos não acumuláveis
    dup_names = df_folha.groupby("Nome").filter(lambda g: len(g) > 1)
    multi_nao_acum = 0
    for nome, grp in dup_names.groupby("Nome"):
        if not grp["Cargo"].str.contains(acum_regex, case=False, regex=True).all():
            multi_nao_acum += 1
            _add_alert(
                alerts, "Folha", "Baixa",
                "Múltiplas matrículas fora dos cargos acumuláveis padrão",
                nome, f"{len(grp)} matrículas", float(grp["TotalVantagens"].sum()),
                " | ".join(f"{x['Matricula']} [{x['Vinculo']}] {x['Cargo']}" for _, x in grp.iterrows()),
            )

    # 6. Indícios de desvio de função / lotação atípica (quando LocalTrabalho está disponível)
    if "LocalTrabalho" in df_folha.columns:
        sup_col = df_folha["Supervisor"] if "Supervisor" in df_folha.columns else pd.Series("", index=df_folha.index)
        # 6a. Professores/Educadores em áreas administrativas/marketing/desenvolvimento econômico
        prof_desvio = df_folha[
            df_folha["Cargo"].str.contains(r"Prof|Educador", case=False, regex=True)
            & ~df_folha["LocalTrabalho"].str.contains(
                r"ESCOLA|CMEI|EDUC|ENSINO|CULTURA|ESPORTE|CRAS|CREAS|AABB", case=False, regex=True
            )
            & (df_folha["LocalTrabalho"].str.strip() != "")
        ]
        for idx, r in prof_desvio.iterrows():
            _add_alert(
                alerts, "Desvio/Lotação", "Alta" if r["Gratificacoes"] > 0 else "Media",
                "Docente/Educador lotado fora da Educação/Cultura/Assistência",
                f"{r['Matricula']} - {r['Nome']}", r["LocalTrabalho"], float(r["TotalVantagens"]),
                f"Cargo: {r['Cargo']} | Sup: {sup_col.loc[idx]} | Grat: R$ {r['Gratificacoes']:,.2f}",
            )

        # 6b. ACS alocado em Pronto Atendimento / fora de PSF/UBS
        acs_desvio = df_folha[
            df_folha["Cargo"].str.contains(r"Agente Comunit|ACS", case=False, regex=True)
            & df_folha["LocalTrabalho"].str.contains(r"PRONTO ATENDIMENTO|UPA|GABINETE|ADMINISTRA", case=False, regex=True)
        ]
        for _, r in acs_desvio.iterrows():
            _add_alert(
                alerts, "Desvio/Lotação", "Media",
                "ACS alocado em unidade de urgência/administrativa (fora de território PSF/UBS)",
                f"{r['Matricula']} - {r['Nome']}", r["LocalTrabalho"], float(r["TotalVantagens"]),
                f"Cargo: {r['Cargo']} | Grat: R$ {r['Gratificacoes']:,.2f}",
            )

        # 6c. Servidores cedidos com ônus
        cedidos = df_folha[df_folha["Vinculo"] == "Cedido com ônus"]
        for idx, r in cedidos.iterrows():
            _add_alert(
                alerts, "Desvio/Lotação", "Media",
                "Servidor cedido com ônus para órgão/entidade externa",
                f"{r['Matricula']} - {r['Nome']}", r["LocalTrabalho"], float(r["TotalVantagens"]),
                f"Cargo: {r['Cargo']} | Sup: {sup_col.loc[idx]}",
            )

        # 6d. Cargos operacionais em Gabinete/Planejamento/Administração/Fazenda
        op_adm = df_folha[
            df_folha["Cargo"].str.contains(r"Operario|Servente|Motorista|Artifice|Mecanico", case=False, regex=True)
            & df_folha["LocalTrabalho"].str.contains(r"GABINETE|ADMINISTRA|PLANEJAMENTO|FAZENDA|TRIBUTA", case=False, regex=True)
        ]
        for idx, r in op_adm.iterrows():
            _add_alert(
                alerts, "Desvio/Lotação", "Baixa",
                "Cargo operacional lotado em secretaria meio/gabinete",
                f"{r['Matricula']} - {r['Nome']}", r["LocalTrabalho"], float(r["TotalVantagens"]),
                f"Cargo: {r['Cargo']} | Sup: {sup_col.loc[idx]}",
            )

    return {
        "total_registros": int(len(df_folha)),
        "total_vantagens": float(df_folha["TotalVantagens"].sum()),
        "total_liquido": float(df_folha["TotalLiquido"].sum()),
        "total_horas_extras": float(df_folha["HorasExtras"].sum()),
        "qtd_he_alta": int(len(he_high)),
        "qtd_acumulo": int(len(acum)),
        "qtd_licenca_grat": int(len(df_folha[(df_folha["Licenca"] == "Sim") & ((df_folha["Gratificacoes"] > 0) | (df_folha["HorasExtras"] > 0))])),
        "qtd_comissionado_he": int(len(com_he)),
        "qtd_multi_nao_acum": multi_nao_acum,
    }


def audit_diarias(df_diarias: pd.DataFrame, cfg: dict[str, Any], alerts: list[dict[str, Any]]) -> dict[str, Any]:
    """Executa regras de triagem nas diárias e gera ranking consolidado."""
    rd = cfg.get("regras_diarias", {})
    min_emp_pol = int(rd.get("min_empenhos_politico_alerta", 10))
    min_val_pol = float(rd.get("min_valor_politico_alerta", 10000.0))
    min_diar_mot = float(rd.get("min_diarias_motorista_alerta", 150.0))

    post_count = int(df_diarias["EmpenhoAposViagem"].sum())
    fds_count = int(df_diarias["IncluiFimDeSemana"].sum())

    if rd.get("alertar_empenho_apos_viagem", True) and post_count > 0:
        pct = round((post_count / len(df_diarias)) * 100, 1)
        _add_alert(
            alerts, "Diárias", "Media",
            "Empenho emitido após início da viagem (padrão sistêmico)",
            "Município de Dois Vizinhos", f"{post_count}/{len(df_diarias)} empenhos ({pct}%)",
            float(df_diarias.loc[df_diarias["EmpenhoAposViagem"], "ValorEmpenho"].sum()),
            "Conferir previsão legal de ressarcimento/indenização frente ao art. 60 da Lei nº 4.320/1964.",
        )

    ranking_rows = []
    for nome, grp in df_diarias.groupby("ServidorNome"):
        first = grp.iloc[0]
        perfil = "Efetivo/Outro"
        if "POLÍTICOS" in str(first["Natureza"]) or first["Vinculo"] == "Agente Político":
            perfil = "Agente Político"
        elif "COMISSIONADOS" in str(first["Natureza"]) or first["Vinculo"] == "Comissionado":
            perfil = "Comissionado"
        elif "Motorista" in str(first["Cargo"]):
            perfil = "Motorista"

        tot_val = float(grp["ValorEmpenho"].sum())
        tot_diar = float(grp["NumeroDiarias"].sum())
        fds = int(grp["IncluiFimDeSemana"].sum())
        top_dest_s = grp[grp["Destino"] != ""]["Destino"].value_counts()
        top_dest = f"{top_dest_s.index[0]} ({top_dest_s.iloc[0]}x)" if not top_dest_s.empty else ""

        ranking_rows.append(
            {
                "ServidorNome": nome,
                "Perfil": perfil,
                "Cargo": first["Cargo"],
                "Lotacao": first["Lotacao"],
                "Empenhos": int(len(grp)),
                "MesesDistintos": int(grp[grp["MesEmpenho"] != ""]["MesEmpenho"].nunique()),
                "TotalDiariasN": round(tot_diar, 1),
                "ValorTotal": round(tot_val, 2),
                "HorasExtrasFolha": float(first["HorasExtrasFolha"]),
                "EmpenhosFds": fds,
                "PrincipalDestino": top_dest,
            }
        )

        if perfil in ("Agente Político", "Comissionado") and (len(grp) >= min_emp_pol or tot_val >= min_val_pol):
            _add_alert(
                alerts, "Diárias", "Alta",
                f"{perfil} com volume elevado de diárias",
                nome, f"{len(grp)} empenhos | FDS: {fds}", tot_val,
                f"Cargo: {first['Cargo']} | Principal destino: {top_dest}",
            )
        elif perfil == "Motorista" and tot_diar >= min_diar_mot and float(first["HorasExtrasFolha"]) > 0:
            _add_alert(
                alerts, "Diárias", "Baixa",
                "Motorista com alto volume anual de diárias + HE na folha",
                nome, f"{tot_diar:.1f} diárias", tot_val,
                f"HE Folha (ref.): R$ {float(first['HorasExtrasFolha']):,.2f} | Destino principal: {top_dest}",
            )

    df_rank = pd.DataFrame(ranking_rows).sort_values("ValorTotal", ascending=False)
    return {
        "total_empenhos": int(len(df_diarias)),
        "pessoas_distintas": int(len(df_rank)),
        "valor_total": float(df_diarias["ValorEmpenho"].sum()),
        "empenho_pos_viagem": post_count,
        "inclui_fds": fds_count,
        "ranking_df": df_rank,
    }


def audit_compras(
    df_req: pd.DataFrame,
    df_rel: pd.DataFrame,
    cfg: dict[str, Any],
    alerts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Executa regras de triagem em Dispensas, Inexigibilidades, Concentração e Aditivos."""
    rc = cfg.get("regras_compras", {})
    teto_serv = float(rc.get("teto_dispensa_servicos_compras", 62725.59))
    conc_pct = float(rc.get("alerta_concentracao_fornecedor_pct", 10.0))

    tot_geral = float(df_req["Total"].sum())

    # 1. Dispensas acima do teto de baixo valor ou múltiplas dispensas no mesmo ano para o mesmo fornecedor
    disp = df_req[df_req["Modalidade"] == "Dispensa"]
    for forn, grp in disp.groupby("FornecedorNome"):
        if not forn:
            continue
        val = float(grp["Total"].sum())
        procs = sorted(grp["Licitacao"].unique())
        procs_2026 = [p for p in procs if p.endswith("2026")]
        if val > teto_serv:
            _add_alert(
                alerts, "Compras", "Alta",
                "Dispensa de licitação acima do teto de baixo valor (Lei 14.133)",
                forn, ", ".join(procs), val,
                f"{len(grp)} itens requisitados. Conferir enquadramento legal (art. 75).",
            )
        if len(procs_2026) >= 2:
            _add_alert(
                alerts, "Compras", "Alta",
                "Múltiplas dispensas no mesmo exercício (possível fracionamento)",
                forn, ", ".join(procs_2026), val,
                f"{len(procs_2026)} dispensas em 2026 para o mesmo fornecedor.",
            )

    # 2. Inexigibilidades de grande vulto (>= R$ 1 milhão)
    inex = df_req[df_req["Modalidade"] == "Inexigibilidade"]
    for forn, grp in inex.groupby("FornecedorNome"):
        if not forn:
            continue
        val = float(grp["Total"].sum())
        if val >= 1_000_000.0:
            procs = sorted(grp["Licitacao"].unique())
            _add_alert(
                alerts, "Compras", "Media",
                "Inexigibilidade >= R$ 1 milhão (conferir exclusividade/credenciamento)",
                forn, ", ".join(procs), val,
                f"{len(grp)} itens requisitados em 2026.",
            )

    # 3. Concentração de fornecedor no total requisitado
    for forn, grp in df_req.groupby("FornecedorNome"):
        if not forn or tot_geral <= 0:
            continue
        val = float(grp["Total"].sum())
        pct = (val / tot_geral) * 100.0
        if pct >= conc_pct:
            _add_alert(
                alerts, "Compras", "Media",
                f"Concentração de fornecedor >= {conc_pct:.0f}% do total requisitado",
                forn, f"{pct:.1f}% do município", val,
                f"Modalidades: {', '.join(sorted(grp['Modalidade'].unique()))}",
            )

    # 4. Itens licitados vs contratados (rel (4).csv)
    qtd_acima = 0
    if not df_rel.empty and "Valor Total Contratado_num" in df_rel.columns:
        acima = df_rel[df_rel["Valor Total Contratado_num"] > df_rel["Valor Total Licitado_num"]]
        # Filtra linhas onde houve deslocamento de texto (Valor Total Licitado_num == 0 mas texto não numérico)
        acima_valid = acima[acima["Valor Total Licitado_num"] > 0]
        qtd_acima = int(len(acima_valid))
        for _, r in acima_valid.iterrows():
            v_lic = float(r["Valor Total Licitado_num"])
            v_cont = float(r["Valor Total Contratado_num"])
            pct_up = round(((v_cont - v_lic) / v_lic) * 100.0, 2)
            _add_alert(
                alerts, "Compras", "Baixa",
                "Valor contratado superior ao valor licitado",
                r["Produto"], f"+{pct_up}%", v_cont - v_lic,
                f"Licitado: R$ {v_lic:,.2f} | Contratado: R$ {v_cont:,.2f}",
            )

    return {
        "total_itens": int(len(df_req)),
        "valor_total": tot_geral,
        "por_modalidade": df_req.groupby("Modalidade")["Total"].agg(["count", "sum"]).sort_values("sum", ascending=False),
        "qtd_contratado_acima_licitado": qtd_acima,
    }
