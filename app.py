import streamlit as st
from modules.auth import login
from modules.ui_components import apply_style

st.set_page_config(page_title="Simples Connect", layout="wide")

apply_style()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login()
else:
    st.sidebar.success(f"Usuário: {st.session_state['user']}")
    st.write("# 👋 Bem-vindo à Simples Connect")
    st.write("Sistema de análise de vendas e compras.")
    st.write("Selecione uma página ao lado para começar.")
