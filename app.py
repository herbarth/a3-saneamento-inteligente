"""Dashboard municipal da A3. Executar: streamlit run app.py."""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "processed" / "saneamento_municipios_2024_parcial.csv"
COLORS = ["#087f8c", "#143b63", "#ee9b34", "#7956a8", "#c44e52"]
PORTES = ["até 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "mais de 500 mil"]
LABELS = {
    "municipio": "Município", "uf": "UF", "regiao": "Região",
    "porte_populacional": "Porte populacional", "cod_ibge": "Código IBGE",
    "respondeu_sinisa": "Respondeu ao SINISA", "populacao_ibge_2024": "População IBGE 2024",
    "despesa_manejo_por_hab_ibge2024": "DEX por habitante residente (R$/ano)",
    "despesa_manejo_por_hab_coberto_sinisa_oficial": "DEX por habitante coberto (R$/ano)",
    "despesa_manejo_por_t_rsu": "DEX por tonelada coletada (R$/t)",
    "recuperacao_total_sinisa_oficial_pct": "Recuperação de secos e orgânicos (%)",
    "recuperacao_secos_sinisa_oficial_pct": "Recuperação de secos (%)",
    "recuperacao_organicos_sinisa_oficial_pct": "Recuperação de orgânicos (%)",
    "cobertura_coleta_sinisa_oficial_pct": "Cobertura da coleta (%)",
    "cobertura_seletiva_sinisa_oficial_pct": "Cobertura da coleta seletiva (%)",
    "despesa_exploracao_manejo_rs_ano": "DEX anual de manejo (R$)",
    "massa_rsu_coletada_t_ano": "Massa de RSU coletada (t/ano)",
    "massa_recuperada_secos_organicos_t_ano": "Massa recuperada: secos e orgânicos (t/ano)",
    "vinculos_formais_totais_3112": "Vínculos formais: todos os setores",
    "vinculos_formais_totais_por_1000_hab": "Vínculos totais por mil residentes",
    "vinculos_cnae38_3112": "Vínculos formais nas atividades de resíduos",
    "vinculos_coleta_381_3112": "Vínculos formais na coleta",
    "vinculos_tratamento_382_3112": "Vínculos formais no tratamento e disposição",
    "vinculos_recuperacao_383_3112": "Vínculos formais na recuperação de materiais",
    "vinculos_residuos_por_1000_hab": "Vínculos em resíduos por mil residentes",
    "participacao_cnae38_no_emprego_formal_pct": "Participação do setor de resíduos no emprego formal (%)",
    "flag_qualidade": "Alerta de qualidade", "apta_analise_custo_recuperacao": "Elegível para análise inicial",
    "flag_compatibilidade_territorial_rais": "Alerta de compatibilidade territorial RAIS",
}


def br(value, decimals=0, suffix=""):
    """Apresentação numérica brasileira, incluindo ausência explícita."""
    if value is None or pd.isna(value):
        return "Sem dados"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".") + suffix


def bool_col(frame, name):
    if name not in frame:
        return pd.Series(False, index=frame.index)
    return frame[name].astype("string").str.lower().isin(["true", "1", "sim"])


@st.cache_data(show_spinner=False)
def load_data(path, modified_ns):
    """O carimbo invalida o cache quando o ETL atualiza a base."""
    frame = pd.read_csv(path, dtype={"cod_ibge": "string", "uf": "string"}, encoding="utf-8-sig")
    if frame["cod_ibge"].duplicated().any():
        raise ValueError("A base contém códigos municipais repetidos. Execute a validação do ETL.")
    return frame


def numeric_data(frame, columns, positive=()):
    if any(c not in frame for c in columns):
        return frame.iloc[0:0].copy()
    result = frame.dropna(subset=columns).copy()
    for col in columns:
        result = result[np.isfinite(pd.to_numeric(result[col], errors="coerce"))]
    for col in positive:
        result = result[result[col] > 0]
    return result


def chart(fig):
    fig.update_layout(
        font={"family": "sans-serif", "size": 13, "color": "#18324a"},
        margin={"l": 12, "r": 12, "t": 35, "b": 16},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=COLORS, legend_title_text="", height=390,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e5edf2", zerolinecolor="#e5edf2")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def median_metric(container, title, frame, column, decimals=1, suffix=""):
    values = frame[column].dropna() if column in frame else pd.Series(dtype=float)
    container.metric(title, br(values.median(), decimals, suffix))
    container.caption(f"Mediana municipal • {br(len(values))} valores informados")


def sector_column(frame):
    """Nunca substituir a medida setorial pela variável de todos os setores."""
    preferred = [
        "vinculos_cnae38_3112",
        "vinculos_formais_residuos_3112", "vinculos_formais_residuos_2024",
        "vinculos_residuos_3112", "vinculos_formais_setor_residuos_3112",
    ]
    other = [c for c in frame if "vinculos" in c and "residu" in c and "por_" not in c]
    return next((c for c in preferred + other if c in frame and pd.api.types.is_numeric_dtype(frame[c])), None)


st.set_page_config(page_title="Saneamento Inteligente | A3 UNIFACS", page_icon="♻️", layout="wide")
st.markdown("""
<style>
.stApp {background: #f6f9fb;}
.block-container {padding-top: 4rem; padding-bottom: 3rem; max-width: 1440px;}
[data-testid="stMetric"] {background: white; border: 1px solid #dfe9ef; border-radius: 12px; padding: 15px 18px;}
[data-testid="stMetricValue"] {color: #143b63;}
[data-testid="stSidebar"] {background: #eef4f7;}
h1, h2, h3 {color: #143b63;}
.eyebrow {font-size: .82rem; font-weight: 700; letter-spacing: .11em; color: #087f8c;}
.intro {color: #4b6579; max-width: 950px; font-size: 1.05rem;}
</style>
""", unsafe_allow_html=True)

if not DATA_PATH.exists():
    st.error("A base municipal ainda não está disponível nesta pasta. Execute o ETL antes de abrir o painel.")
    st.stop()
try:
    data = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
except (ValueError, OSError) as exc:
    st.error(f"Não foi possível abrir a base validada: {exc}")
    st.stop()

with st.sidebar:
    st.markdown("### Seu recorte de análise")
    st.caption("Referência 2024 • município")
    regions = st.multiselect("Regiões", sorted(data["regiao"].dropna().unique()), key="regions", placeholder="Todas as regiões")
    filtered = data[data["regiao"].isin(regions)].copy() if regions else data.copy()
    ufs = st.multiselect("Estados", sorted(filtered["uf"].dropna().unique()), key="ufs", placeholder="Todos os estados")
    if ufs:
        filtered = filtered[filtered["uf"].isin(ufs)].copy()
    actual_portes = filtered["porte_populacional"].dropna().unique().tolist()
    ordered_portes = [p for p in PORTES if p in actual_portes] + sorted(set(actual_portes) - set(PORTES))
    portes = st.multiselect("Porte populacional", ordered_portes, key="portes", placeholder="Todos os portes")
    if portes:
        filtered = filtered[filtered["porte_populacional"].isin(portes)].copy()
    localities = filtered[["cod_ibge", "municipio", "uf"]].sort_values(["municipio", "uf"])
    options = {f"{r.municipio} / {r.uf} · {r.cod_ibge}": r.cod_ibge for r in localities.itertuples()}
    municipality = st.selectbox("Município", ["Todos os municípios", *options], key="municipality")
    if municipality != "Todos os municípios":
        filtered = filtered[filtered["cod_ibge"].eq(options[municipality])].copy()
    st.divider()
    use_validated = st.checkbox("Aplicar critérios de qualidade à análise", value=True, key="quality")
    st.caption("Despesas e recuperação usam registros elegíveis definidos no ETL. O panorama de respostas sempre preserva os municípios do filtro.")
    st.caption("Deixe um filtro vazio para incluir todas as opções.")

st.markdown('<div class="eyebrow">UNIFACS · ANÁLISE DE DADOS E BIG DATA · A3</div>', unsafe_allow_html=True)
st.title("Saneamento Inteligente")
st.markdown('<p class="intro">Custos de manejo de resíduos, recuperação de materiais e contexto do emprego formal nos municípios brasileiros.</p>', unsafe_allow_html=True)
st.caption("Base integrada · SINISA 2025, referência 2024 · IBGE 2024 · RAIS 2024")
st.info("Este painel compara registros declarados. Diferenças de gasto podem refletir cobertura, porte, distâncias e qualidade do serviço; os gráficos, isoladamente, não demonstram economia causal ou eficiência.")

if filtered.empty:
    st.warning("Nenhum município corresponde aos filtros. Amplie a seleção na barra lateral.")
    st.stop()

responded = filtered["respondeu_sinisa"].eq("Sim")
eligible = bool_col(filtered, "apta_analise_custo_recuperacao")
analysis = filtered[eligible].copy() if use_validated else filtered[responded].copy()
year_label = ", ".join(map(str, sorted(filtered["ano"].dropna().unique())))
st.caption(f"Recorte atual: {br(len(filtered))} municípios • {br(int(responded.sum()))} respondentes ao SINISA • referência {year_label}")

tabs = st.tabs(["Panorama", "Despesas", "Recuperação", "Emprego formal", "Qualidade e fontes"])

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Municípios selecionados", br(len(filtered)))
    c2.metric("Responderam ao SINISA", br(int(responded.sum())))
    c3.metric("Não responderam", br(int((~responded).sum())))
    c4.metric("Cobertura de respostas", br(100 * responded.mean(), 1, "%"))
    st.caption("O denominador da cobertura de respostas é o conjunto de municípios selecionados. Não resposta não significa serviço, gasto ou recuperação igual a zero.")
    st.subheader("Onde há informação disponível")
    geography = "uf" if ufs or len(filtered["regiao"].unique()) == 1 else "regiao"
    response_table = filtered.assign(Resposta=np.where(responded, "Respondeu", "Não respondeu")).groupby([geography, "Resposta"]).size().rename("Municípios").reset_index()
    chart(px.bar(response_table, x=geography, y="Municípios", color="Resposta", barmode="stack", labels=LABELS, color_discrete_map={"Respondeu": COLORS[0], "Não respondeu": "#b9c8d4"}))
    st.subheader("Cobertura dos serviços declarada")
    c1, c2 = st.columns(2)
    median_metric(c1, "Coleta domiciliar", filtered[responded], "cobertura_coleta_sinisa_oficial_pct", suffix="%")
    median_metric(c2, "Coleta seletiva", filtered[responded], "cobertura_seletiva_sinisa_oficial_pct", suffix="%")
    st.caption("Indicadores oficiais SINISA. Cobertura é proporção da população atendida, com frequência mínima semanal; difere da proporção de massa recuperada. As medianas municipais não são uma taxa de atendimento agregada do Brasil.")

with tabs[1]:
    st.subheader("Despesa de exploração do manejo")
    st.write("A despesa de exploração (DEX) reúne a operação do manejo de resíduos. Inclui pessoal, terceiros, tributos e outras despesas operacionais; investimento é registrado separadamente.")
    st.caption(f"Amostra de análise: {br(len(analysis))} municípios. Cada medida informa a quantidade de valores disponíveis.")
    c1, c2, c3 = st.columns(3)
    median_metric(c1, "Por habitante residente", analysis, "despesa_manejo_por_hab_ibge2024", 2, " R$/ano")
    median_metric(c2, "Por habitante coberto", analysis, "despesa_manejo_por_hab_coberto_sinisa_oficial", 2, " R$/ano")
    median_metric(c3, "Por tonelada de RSU coletada", analysis, "despesa_manejo_por_t_rsu", 2, " R$/t")
    st.caption("Habitante residente: população IBGE total. Habitante coberto: população atendida pela coleta, denominador do IFR2002 oficial. A razão por tonelada usa toda a DEX de manejo; não mede o custo exclusivo da coleta nem o custo marginal da reciclagem.")
    cost_options = {
        "Por tonelada coletada": "despesa_manejo_por_t_rsu",
        "Por habitante residente": "despesa_manejo_por_hab_ibge2024",
        "Por habitante coberto": "despesa_manejo_por_hab_coberto_sinisa_oficial",
    }
    cost_label = st.radio("Comparar despesas", list(cost_options), horizontal=True, key="cost_measure")
    cost_col = cost_options[cost_label]
    cost_data = numeric_data(analysis, [cost_col])
    if cost_data.empty:
        st.info("O recorte não contém valores suficientes desta medida.")
    else:
        group = st.selectbox("Comparar municípios por", ["Porte populacional", "Região", "UF"], key="cost_group")
        group_col = {"Porte populacional": "porte_populacional", "Região": "regiao", "UF": "uf"}[group]
        controls = st.columns(2)
        log_cost = controls[0].checkbox("Escala logarítmica para despesas", value=True, key="cost_log")
        central_cost = controls[1].checkbox("Exibir faixa central: percentis 1 a 99", value=False, key="cost_central")
        cost_view = cost_data.copy()
        if central_cost:
            low, high = cost_data[cost_col].quantile([.01, .99])
            cost_view = cost_view[cost_view[cost_col].between(low, high)]
        if log_cost:
            cost_view = cost_view[cost_view[cost_col] > 0]
        if not cost_view.empty:
            chart(px.box(cost_view, x=group_col, y=cost_col, color=group_col, points="outliers", log_y=log_cost, labels=LABELS, hover_data=["municipio", "uf"], category_orders={"porte_populacional": ordered_portes}))
        else:
            st.info("A configuração visual não contém despesas positivas. Desative a escala logarítmica para consultar valores iguais a zero.")
        st.caption(f"Gráfico: {br(len(cost_view))} de {br(len(cost_data))} valores informados. A escala logarítmica mostra somente despesas positivas; o corte opcional atua apenas no gráfico. Medianas, tabela e download preservam o recorte completo.")
        st.caption("Despesas extremas exigem investigação na fonte e no contexto local. A ordenação da tabela descreve valores e não constitui ranking de eficiência.")
        st.dataframe(cost_data[["municipio", "uf", "porte_populacional", cost_col]].rename(columns=LABELS).sort_values(LABELS[cost_col], ascending=False), hide_index=True, use_container_width=True)

with tabs[2]:
    st.subheader("Recuperação e coleta seletiva")
    c1, c2, c3 = st.columns(3)
    median_metric(c1, "Secos e orgânicos", analysis, "recuperacao_total_sinisa_oficial_pct", suffix="%")
    median_metric(c2, "Apenas secos", analysis, "recuperacao_secos_sinisa_oficial_pct", suffix="%")
    median_metric(c3, "Apenas orgânicos", analysis, "recuperacao_organicos_sinisa_oficial_pct", suffix="%")
    st.caption("Taxas oficiais em relação à massa total de resíduos sólidos urbanos coletada. A definição SINISA para orgânicos considera a massa da rota encaminhada à compostagem; não comprova o rendimento final do tratamento. Medianas de componentes não precisam somar a mediana do total.")
    recovery_choices = {"Secos e orgânicos": "recuperacao_total_sinisa_oficial_pct", "Apenas secos": "recuperacao_secos_sinisa_oficial_pct", "Apenas orgânicos": "recuperacao_organicos_sinisa_oficial_pct"}
    recovery_label = st.radio("Tipo de recuperação", list(recovery_choices), horizontal=True, key="recovery_type")
    recovery_col = recovery_choices[recovery_label]
    x_choices = {"Cobertura da coleta seletiva": "cobertura_seletiva_sinisa_oficial_pct", "DEX por tonelada coletada": "despesa_manejo_por_t_rsu"}
    x_label = st.selectbox("Relacionar recuperação com", list(x_choices), key="recovery_x")
    x_col = x_choices[x_label]
    recovery_data = numeric_data(analysis, [x_col, recovery_col])
    if recovery_data.empty:
        st.info("Não há pares completos das medidas escolhidas neste recorte.")
    else:
        log_x = False
        recovery_view = recovery_data.copy()
        if x_col == "despesa_manejo_por_t_rsu":
            log_x = st.checkbox("Escala logarítmica para DEX por tonelada", value=True, key="recovery_log")
            if log_x:
                recovery_view = recovery_view[recovery_view[x_col] > 0]
        if not recovery_view.empty:
            chart(px.scatter(recovery_view, x=x_col, y=recovery_col, color="regiao", log_x=log_x, labels=LABELS, hover_name="municipio", hover_data=["uf", "populacao_ibge_2024"], opacity=.65))
        st.caption(f"Gráfico: {br(len(recovery_view))} de {br(len(recovery_data))} municípios com as duas medidas informadas. A escala logarítmica usa despesas positivas. O gráfico mostra associação observada; não estabelece que maior despesa cause maior recuperação.")
    pair = numeric_data(analysis, ["massa_rsu_coletada_t_ano", "massa_recuperada_secos_organicos_t_ano"], positive=["massa_rsu_coletada_t_ano"])
    if not pair.empty:
        recovery_ratio = 100 * pair["massa_recuperada_secos_organicos_t_ano"].sum() / pair["massa_rsu_coletada_t_ano"].sum()
        st.metric("Recuperação do conjunto com massas informadas", br(recovery_ratio, 2, "%"))
        st.caption(f"Soma da massa recuperada dividida pela soma da massa coletada, em {br(len(pair))} municípios. Essa razão difere da média e da mediana das taxas municipais e não preenche os municípios ausentes.")

with tabs[3]:
    st.subheader("Emprego formal: alcance da informação")
    st.write("A RAIS registra vínculos ativos em 31 de dezembro de 2024 no município do estabelecimento. Uma pessoa pode ter mais de um vínculo; o município de trabalho pode diferir do município de residência.")
    sector_col = sector_column(filtered)
    if sector_col is None:
        st.info("O recorte municipal das atividades de resíduos ainda está pendente. Os números abaixo abrangem todos os setores da economia e servem como contexto; não representam empregos verdes, vagas ou empregos gerados pela reciclagem.")
    else:
        sector = pd.to_numeric(filtered[sector_col], errors="coerce")
        c1, c2 = st.columns(2)
        c1.metric("Vínculos nas atividades de resíduos", br(sector.sum(min_count=1)))
        c2.metric("Municípios com dado setorial", f"{br(sector.notna().sum())} / {br(len(filtered))}")
        if sector_col == "vinculos_cnae38_3112":
            st.caption("Recorte das atividades de coleta, tratamento, disposição e recuperação de materiais (divisão 38 da CNAE). Inclui atividades com resíduos perigosos e não perigosos. É um retrato do setor formal, não uma contagem certificada de empregos verdes, pessoas únicas ou postos criados no ano.")
        st.caption("A soma considera somente municípios com informação. Ausências permanecem sem informação; o valor zero só é apresentado quando registrado pela extração validada. As atividades selecionadas não abrangem todo o trabalho verde nem certificam a qualidade do emprego.")
        subsectors = {"vinculos_coleta_381_3112": "Coleta", "vinculos_tratamento_382_3112": "Tratamento e disposição", "vinculos_recuperacao_383_3112": "Recuperação de materiais"}
        available_groups = {col: label for col, label in subsectors.items() if col in filtered}
        if available_groups:
            group_values = pd.DataFrame([{"Atividade": label, "Vínculos formais": pd.to_numeric(filtered[col], errors="coerce").sum(min_count=1)} for col, label in available_groups.items()])
            chart(px.bar(group_values, x="Atividade", y="Vínculos formais", color_discrete_sequence=[COLORS[0]]))
        if "vinculos_residuos_por_1000_hab" in filtered:
            c1, c2 = st.columns(2)
            median_metric(c1, "Resíduos: vínculos por mil residentes", filtered, "vinculos_residuos_por_1000_hab", 2)
            median_metric(c2, "Participação no emprego formal", filtered, "participacao_cnae38_no_emprego_formal_pct", 2, "%")
            st.caption("Medianas municipais dos valores informados. A participação divide vínculos do setor de resíduos por vínculos de todos os setores; não mede proporção da população empregada. Indicadores proporcionais seguem as ressalvas territoriais do ETL.")
    c1, c2, c3 = st.columns(3)
    total_col = "vinculos_formais_totais_3112"
    total_values = filtered[total_col].dropna() if total_col in filtered else pd.Series(dtype=float)
    c1.metric("Vínculos em todos os setores", br(total_values.sum(min_count=1)))
    c2.metric("Municípios com total RAIS", f"{br(len(total_values))} / {br(len(filtered))}")
    median_metric(c3, "Vínculos totais por mil residentes", filtered, "vinculos_formais_totais_por_1000_hab", 1)
    st.caption("A razão por mil residentes é uma medida de contexto do mercado formal, não taxa de ocupação. Razões são suspensas onde o ETL identificou incompatibilidade territorial. Catadores informais e autônomos não são cobertos integralmente pela RAIS.")
    if total_col in filtered and not total_values.empty:
        employment = filtered.groupby("uf", dropna=False)[total_col].sum(min_count=1).rename("Vínculos formais: todos os setores").reset_index()
        chart(px.bar(employment, x="uf", y="Vínculos formais: todos os setores", labels=LABELS, color_discrete_sequence=[COLORS[1]]))

with tabs[4]:
    st.subheader("Qualidade da base selecionada")
    c1, c2, c3 = st.columns(3)
    c1.metric("Não respondentes SINISA", br((~responded).sum()))
    c2.metric("Municípios com alerta", br(bool_col(filtered, "flag_qualidade").sum()))
    c3.metric("Alerta territorial RAIS", br(bool_col(filtered, "flag_compatibilidade_territorial_rais").sum()))
    st.caption("Alertas apoiam a revisão e não certificam todos os demais registros. O filtro de qualidade da barra lateral atua nas abas Despesas e Recuperação. A falta de resposta continua visível no panorama.")
    quality_columns = ["despesa_exploracao_manejo_rs_ano", "massa_rsu_coletada_t_ano", "recuperacao_total_sinisa_oficial_pct", "recuperacao_secos_sinisa_oficial_pct", "cobertura_seletiva_sinisa_oficial_pct", "vinculos_formais_totais_3112"]
    if sector_col:
        quality_columns.append(sector_col)
    completeness = pd.DataFrame([{"Medida": LABELS.get(col, col), "Informados": int(filtered[col].notna().sum()), "Ausentes": int(filtered[col].isna().sum()), "Cobertura (%)": round(100 * filtered[col].notna().mean(), 1)} for col in quality_columns if col in filtered])
    st.dataframe(completeness, hide_index=True, use_container_width=True)
    alert_path = ROOT / "evidencias" / "validacoes_por_municipio.csv"
    if alert_path.exists():
        alerts = pd.read_csv(alert_path, dtype={"cod_ibge": "string"}, encoding="utf-8-sig")
        if "cod_ibge" in alerts:
            alerts = alerts[alerts["cod_ibge"].isin(filtered["cod_ibge"])]
        if not alerts.empty:
            with st.expander("Ver registros de validação do recorte"):
                st.dataframe(alerts, hide_index=True, use_container_width=True)
    st.subheader("Fontes e decisões de leitura")
    st.markdown("""
- [SINISA 2025 — resultados oficiais, referência 2024](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025): despesas, massas, recuperação e cobertura autodeclaradas.
- [IBGE — estimativas municipais de população 2024](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/): denominador residente da versão DOU de 29/08/2024, compatível com a população SINISA usada na base.
- [MTE — RAIS 2024](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/rais/rais-2024): estoque formal em 31/12/2024. A delimitação setorial deve acompanhar qualquer interpretação sobre resíduos.
""")
    st.write("O recorte é transversal: não permite concluir tendências temporais ou criação anual de empregos. Comparações devem considerar porte, cobertura, distância de destinação, contratos, informalidade e qualidade dos registros. O arquivo mantém ausências e os valores originais; as decisões estão documentadas junto ao projeto.")
    with st.expander("Consultar os dados deste recorte"):
        st.dataframe(filtered.rename(columns=LABELS), hide_index=True, use_container_width=True)

st.divider()
st.download_button(
    "Baixar dados do recorte (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="saneamento_2024_recorte.csv", mime="text/csv",
    help="Inclui todos os municípios selecionados, suas ausências e os indicadores de validação.",
)
st.caption("Projeto A3 • UNIFACS • Dados de 2024 • Versão em desenvolvimento, com limitações de cobertura explicitadas.")
