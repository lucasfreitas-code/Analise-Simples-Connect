import streamlit as st

def apply_style():
    st.markdown("""
    <style>
    body { font-family: 'Poppins', sans-serif; }
    .main { background-color: #0e0e0e; color: white; }
    </style>
    """, unsafe_allow_html=True)
