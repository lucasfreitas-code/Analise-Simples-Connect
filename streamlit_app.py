# app.py
"""
Simples Connect - Dashboard Streamlit
Criado por: Lucas Freitas
Descrição: Dashboard interativo para análise de vendas & compras.
Salve este arquivo como app.py e faça deploy no Streamlit Cloud ou rode localmente.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# -----------------------
# Config e estilo
# -----------------------
st.set_page_config(page_title="Simples Connect", layout="wide", initial_sidebar_state="expanded")

PINK = "#ff2d95"
BG = "#0a0a0a"
TEXT = "#FFFFFF"

st.markdown(f"""
<div style="background:{BG};padding:16px;border-radius:6px">
  <h1 style="color:{PINK};margin:0">Simples Connect</h1>
  <div style="color:{TEXT};">Criado por <b>Lucas Freitas</b></div>
</div>
""", unsafe_allow_html=True)

# small css tweaks
st.markdown(f"""
<style>
.reportview-container .main {{ background-color: {BG}; color: {TEXT}; }}
.sidebar .sidebar-content {{ background-color: #0f0f0f; color: {TEXT}; }}
h1, h2, h3, h4, h5 {{ color: {PINK}; }}
</style>
""", unsafe_allow_html=True)

# -----------------------
# Helper detection
# -----------------------
def find_col(df, candidates):
    for c in candidates:
        for col in df.columns:
            if str(col).strip().lower() == c.lower():
                return col
    # partial match
    for col in df.columns:
        name = str(col).lower()
        for c in candidates:
            if c.lower() in name:
                return col
    return None

def to_excel_bytes(dfs: dict):
    with BytesIO() as b:
        with pd.ExcelWriter(b, engine="openpyxl") as writer:
            for name, df in dfs.items():
                df.to_excel(writer, sheet_name=name[:30], index=False)
        return b.getvalue()

# -----------------------
# Sidebar - Upload / Options
# -----------------------
st.sidebar.header("Upload / Opções")
uploaded_vendas = st.sidebar.file_uploader("Planilha: Vendas (xlsx/csv)", type=["xlsx","csv"])
uploaded_compras = st.sidebar.file_uploader("Planilha: Compras (xlsx/csv)", type=["xlsx","csv"])
use_demo = st.sidebar.checkbox("Usar dados de exemplo (demo)", value=False)

top_n = st.sidebar.number_input("Top N (rankings)", min_value=5, max_value=50, value=10)

# -----------------------
# Load or create data
# -----------------------
if use_demo:
    np.random.seed(42)
    items = [f"SKU-{i:03d}" for i in range(1,201)]
    clients = [f"Cliente {i}" for i in range(1,61)]

    vendas = pd.DataFrame({
        "Item": np.random.choice(items, 1200),
        "Cliente": np.random.choice(clients, 1200),
        "Qtd_Venda": np.random.poisson(3, 1200)+1,
        "Valor_Venda": np.round(np.random.uniform(5,200,1200),2)
    })
    vendas["Valor_Venda"] = vendas["Valor_Venda"] * vendas["Qtd_Venda"]

    compras = pd.DataFrame({
        "Item": np.random.choice(items, 900),
        "Qtd_Compra": np.random.poisson(4,900)+1,
        "Valor_Custo": np.round(np.random.uniform(2,150,900),2)
    })
    compras["Valor_Custo"] = compras["Valor_Custo"] * compras["Qtd_Compra"]
else:
    if uploaded_vendas is None or uploaded_compras is None:
        st.info("Faça upload das planilhas Vendas e Compras no painel lateral ou marque 'Usar dados de exemplo' para demo.")
        st.stop()
    # read uploads
    if uploaded_vendas.name.lower().endswith(".csv"):
        vendas = pd.read_csv(uploaded_vendas)
    else:
        vendas = pd.read_excel(uploaded_vendas)
    if uploaded_compras.name.lower().endswith(".csv"):
        compras = pd.read_csv(uploaded_compras)
    else:
        compras = pd.read_excel(uploaded_compras)

# -----------------------
# Normalize column names (auto-detect)
# -----------------------
# VENDAS detection
item_v_col = find_col(vendas, ['item','produto','descricao','descrição do produto','sku'])
qty_v_col  = find_col(vendas, ['quantidade','qtd','qty','unidades','qtd_venda','qtd venda'])
val_v_col  = find_col(vendas, ['valor_venda','valor total','valor','total','faturamento','valor_total_venda','valor_venda'])
cliente_col = find_col(vendas, ['cliente','customer','nome_cliente','cliente_nome'])

# COMPRAS detection
item_c_col = find_col(compras, ['item','produto','descricao','descrição do produto','sku'])
qty_c_col  = find_col(compras, ['quantidade','qtd','qty','quantidade_recebida','quantidade_compra'])
val_c_col  = find_col(compras, ['valor_custo','total de mercadoria','valor','valor_total','total','custo'])

# fallback to first cols if not found
if item_v_col is None: item_v_col = vendas.columns[0]
if val_v_col is None:
    numeric = vendas.select_dtypes(include=[np.number]).columns
    val_v_col = numeric[0] if len(numeric)>0 else vendas.columns[1] if len(vendas.columns)>1 else vendas.columns[0]
if qty_v_col is None:
    numeric = vendas.select_dtypes(include=[np.number]).columns
    qty_v_col = numeric[1] if len(numeric)>1 else numeric[0] if len(numeric)>0 else None
if cliente_col is None:
    cliente_col = None  # will create later if missing

if item_c_col is None: item_c_col = compras.columns[0]
if val_c_col is None:
    numeric = compras.select_dtypes(include=[np.number]).columns
    val_c_col = numeric[0] if len(numeric)>0 else compras.columns[0]
if qty_c_col is None:
    numeric = compras.select_dtypes(include=[np.number]).columns
    qty_c_col = numeric[1] if len(numeric)>1 else numeric[0] if len(numeric)>0 else None

# rename standard columns
v = vendas.rename(columns={
    item_v_col: "Item",
    qty_v_col: "Qtd_Venda",
    val_v_col: "Valor_Venda",
    cliente_col: "Cliente"
})
c = compras.rename(columns={
    item_c_col: "Item",
    qty_c_col: "Qtd_Compra",
    val_c_col: "Valor_Custo"
})

# ensure columns exist & numeric
if "Qtd_Venda" not in v.columns: v["Qtd_Venda"] = 1
if "Valor_Venda" not in v.columns: v["Valor_Venda"] = 0
if "Qtd_Compra" not in c.columns: c["Qtd_Compra"] = 0
if "Valor_Custo" not in c.columns: c["Valor_Custo"] = 0
if "Cliente" not in v.columns: v["Cliente"] = "Cliente Desconhecido"

v["Qtd_Venda"] = pd.to_numeric(v["Qtd_Venda"], errors="coerce").fillna(0)
v["Valor_Venda"] = pd.to_numeric(v["Valor_Venda"], errors="coerce").fillna(0)
c["Qtd_Compra"] = pd.to_numeric(c["Qtd_Compra"], errors="coerce").fillna(0)
c["Valor_Custo"] = pd.to_numeric(c["Valor_Custo"], errors="coerce").fillna(0)

# -----------------------
# Aggregate and unify
# -----------------------
v_agg = v.groupby("Item", dropna=False).agg({"Valor_Venda":"sum","Qtd_Venda":"sum"}).reset_index()
c_agg = c.groupby("Item", dropna=False).agg({"Valor_Custo":"sum","Qtd_Compra":"sum"}).reset_index()

df = pd.merge(v_agg, c_agg, on="Item", how="outer").fillna(0)

# Calculations
df["Lucro"] = df["Valor_Venda"] - df["Valor_Custo"]
# Percentual = Resultado / Custo (if custo=0 -> handle)
df["Percentual"] = np.where(df["Valor_Custo"]==0,
                            np.where(df["Valor_Venda"]==0, 0, np.inf),
                            df["Lucro"] / df["Valor_Custo"] * 100)
df["Ticket_Medio_Unit"] = np.where(df["Qtd_Venda"]>0, df["Valor_Venda"] / df["Qtd_Venda"], 0)
df["Cash_Burn"] = df["Valor_Custo"] - df["Lucro"]  # proxy
df["Lucro_abs"] = df["Lucro"].abs()

median_qty = df["Qtd_Venda"].median()
df["Categoria"] = df.apply(lambda x:
                           "Margem alta / baixo volume" if (x["Percentual"]>20 and x["Qtd_Venda"]<median_qty) else
                           ("Alto volume / baixa margem" if (x["Percentual"]<10 and x["Qtd_Venda"]>median_qty) else "Normal"),
                           axis=1)

# -----------------------
# Global KPIs
# -----------------------
faturamento = df["Valor_Venda"].sum()
custo_total = df["Valor_Custo"].sum()
lucro_total = df["Lucro"].sum()
margem_geral = (lucro_total / custo_total * 100) if custo_total != 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita (Faturamento)", f"R$ {faturamento:,.2f}")
k2.metric("Custo Total", f"R$ {custo_total:,.2f}")
k3.metric("Lucro Total", f"R$ {lucro_total:,.2f}")
k4.metric("Margem Geral (%)", f"{margem_geral:.2f}%")

st.markdown("---")

# -----------------------
# Layout: Dashboards
# -----------------------
# 1) Lucro individual por produto
st.header("Lucro por Produto")
fig = px.bar(df.sort_values("Lucro", ascending=False).head(50),
             x="Item", y="Lucro", title="Top produtos por Lucro")
fig.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
st.plotly_chart(fig, use_container_width=True)

# 2) Top clients by value and qty
st.header("Top Clientes")
top_val = v.groupby("Cliente")["Valor_Venda"].sum().sort_values(ascending=False).head(top_n).reset_index()
top_qtd = v.groupby("Cliente")["Qtd_Venda"].sum().sort_values(ascending=False).head(top_n).reset_index()

c1, c2 = st.columns(2)
fig1 = px.bar(top_val, x="Cliente", y="Valor_Venda", title=f"Top {top_n} Clientes por Valor")
fig1.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
c1.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(top_qtd, x="Cliente", y="Qtd_Venda", title=f"Top {top_n} Clientes por Quantidade")
fig2.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
c2.plotly_chart(fig2, use_container_width=True)

# 3) Top items vendidos (quantidade)
st.header("Itens mais vendidos")
top_items = df.sort_values("Qtd_Venda", ascending=False).head(top_n)
fig3 = px.bar(top_items, x="Item", y="Qtd_Venda", title=f"Top {top_n} Itens por Quantidade")
fig3.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
st.plotly_chart(fig3, use_container_width=True)

# 4) Produtos - margem boa x volume baixo (oportunidades)
st.header("Oportunidades: Alta margem x Baixo volume")
opp = df[df["Categoria"]=="Margem alta / baixo volume"].sort_values("Percentual", ascending=False)
if opp.shape[0] == 0:
    st.info("Nenhum produto automaticamente classificado como 'Alta margem / Baixo volume'. Ajuste thresholds para detectar.")
else:
    fig4 = px.scatter(opp, x="Qtd_Venda", y="Percentual", size="Lucro_abs",
                      color="Lucro", color_continuous_scale=px.colors.diverging.RdYlGn,
                      hover_name="Item", title="Alta margem x Baixo volume (tamanho = |Lucro|)")
    fig4.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
    st.plotly_chart(fig4, use_container_width=True)

# 5) Produtos - alto volume x baixa margem (riscos)
st.header("Riscos: Alto volume x Baixa margem")
risk = df[df["Categoria"]=="Alto volume / baixa margem"].sort_values("Percentual")
if risk.shape[0] == 0:
    st.info("Nenhum produto automaticamente classificado como 'Alto volume / Baixa margem'. Ajuste thresholds para detectar.")
else:
    fig5 = px.scatter(risk, x="Qtd_Venda", y="Percentual", size="Lucro_abs",
                      color="Lucro", color_continuous_scale=px.colors.diverging.RdYlGn,
                      hover_name="Item", title="Alto volume x Baixa margem (tamanho = |Lucro|)")
    fig5.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
    st.plotly_chart(fig5, use_container_width=True)

# 6) Cash burn
st.header("Cash Burn (proxy)")
cash = df.sort_values("Cash_Burn", ascending=False).head(20)
fig6 = px.bar(cash, x="Item", y="Cash_Burn", title="Produtos que mais consomem caixa (proxy)")
fig6.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
st.plotly_chart(fig6, use_container_width=True)

# 7) Ticket médio
st.header("Ticket médio por produto (distribuição)")
fig7 = px.histogram(df[df["Ticket_Medio_Unit"]>0], x="Ticket_Medio_Unit", nbins=30, title="Distribuição do Ticket Médio por Produto")
fig7.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
st.plotly_chart(fig7, use_container_width=True)

# 8) Frequência comparada dos top clients
st.header(f"Frequência comparada - Top {top_n} Clientes")
cli_agg = v.groupby("Cliente").agg({"Qtd_Venda":"sum","Item":"nunique"}).rename(columns={"Item":"Itens_distintos"}).sort_values("Qtd_Venda", ascending=False).head(top_n).reset_index()
fig8 = px.scatter(cli_agg, x="Itens_distintos", y="Qtd_Venda", size="Qtd_Venda", text="Cliente", title=f"Top {top_n} Clientes: Quantidade vs Itens distintos")
fig8.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
st.plotly_chart(fig8, use_container_width=True)

# 9) Share de vendas
st.header(f"Share de vendas - Top {top_n} Clientes")
share_df = top_val.copy()
share_df["Share_%"] = (share_df["Valor_Venda"] / faturamento * 100).round(2)
fig9 = px.pie(share_df, names="Cliente", values="Valor_Venda", title=f"Share de Vendas - Top {top_n} Clientes")
fig9.update_layout(plot_bgcolor=BG, paper_bgcolor=BG, font_color=TEXT)
st.plotly_chart(fig9, use_container_width=True)

# -----------------------
# Export / Tables
# -----------------------
st.markdown("---")
st.header("Exportar / Tabelas")
st.write("Amostra da tabela unificada (ordenada por Valor de Venda)")
st.dataframe(df.sort_values("Valor_Venda", ascending=False).head(200))

# Export Excel with main sheets
to_export = {
    "Unificado": df,
    "Top_Items": top_items,
    "Top_Clientes_Valor": top_val,
    "Top_Clientes_Qtd": top_qtd
}
excel_bytes = to_excel_bytes(to_export)
st.download_button("📥 Baixar Excel com tabelas", data=excel_bytes, file_name="simples_connect_analise.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("<div style='color:#888888'>Relatório gerado automaticamente • Simples Connect • Analise feita por Lucas Freitas</div>", unsafe_allow_html=True)
