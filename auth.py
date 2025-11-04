import streamlit as st

USERS = {
    "admin": "123",  # coloque user/senha real depois
    "lucas": "123"
}

def login():
    st.title("🔐 Login - Simples Connect")

    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user in USERS and USERS[user] == pwd:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")
