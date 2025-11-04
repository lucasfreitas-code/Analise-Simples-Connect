import streamlit as st
import plotly.express as px
from modules.analytics import load_data, preprocess

c = "data/exemplo/Compras Recebidas.xlsx"
v = "data/exemplo/Vendas Realizadas.xlsx"

st.title("📊 Dashboard de Vendas")

compras, vendas = load_data(c,v)
df = preprocess(compras,vendas)

st.metric("Lucro Total", f"R$ {df['Lucro'].sum():,.2f}")
st.metric("Faturamento", f"R$ {df['Valor_Venda'].sum():,.2f}")

top = df.groupby("Item")["Lucro"].sum().reset_index()

fig = px.bar(top.sort_values("Lucro",ascending=False).head(10),
             x="Item", y="Lucro", title="Top 10 Produtos por Lucro")

st.plotly_chart(fig, use_container_width=True)
