import streamlit as st
import PyPDF2
import re

st.set_page_config(page_title="Análise IPEM-RJ", page_icon="✅")

st.title("ANÁLISE DE PROCESSO - IPEM/RJ")
st.markdown("---")

uploaded_file = st.file_uploader("📤 Selecione o PDF do processo", type=['pdf'])

if uploaded_file:
    # Ler o PDF
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    
    st.success(f"Arquivo carregado: {uploaded_file.name}")
    st.info(f"Número de páginas: {len(pdf_reader.pages)}")
    
    # Extrair texto da primeira página
    primeira_pagina = pdf_reader.pages[0].extract_text()
    
    if primeira_pagina:
        st.subheader("✅ Texto extraído da primeira página:")
        st.text(primeira_pagina[:500])
        
        # Procurar CNPJ
        cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', primeira_pagina)
        if cnpj:
            st.success(f"CNPJ encontrado: {cnpj.group()}")
        else:
            st.warning("CNPJ não encontrado na primeira página")
    else:
        st.error("Não foi possível extrair texto do PDF. Pode ser um PDF escaneado (imagem).")
