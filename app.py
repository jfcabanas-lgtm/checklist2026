import streamlit as st

st.set_page_config(page_title="IPEM-RJ", page_icon="✅")

st.title("ANÁLISE DE PROCESSO - IPEM/RJ")
st.write("Versão super simplificada")

nome = st.text_input("Digite seu nome:")
if nome:
    st.success(f"Olá {nome}!")

upload = st.file_uploader("Upload PDF", type="pdf")
if upload:
    st.info(f"Arquivo: {upload.name}")
    st.balloons()