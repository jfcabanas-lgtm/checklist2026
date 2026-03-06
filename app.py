import streamlit as st
import PyPDF2
import re
from datetime import datetime

st.set_page_config(
    page_title="Análise IPEM-RJ",
    page_icon="✅",
    layout="wide"
)

st.title("📋 ANÁLISE DE PROCESSO DE PAGAMENTO - IPEM/RJ")
st.markdown("---")

# Checklist completo
checklist = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo", "palavras": ["nota de empenho", "empenho", "saldo"]},
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM", "palavras": ["nota fiscal", "nf", "ipem"]},
    {"item": 3, "descricao": "Certidão Federal (Receita Federal)", "palavras": ["certidao federal", "receita federal", "divida ativa"]},
    {"item": 4, "descricao": "Certidão FGTS", "palavras": ["certidao fgts", "fgts", "regularidade fgts"]},
    {"item": 5, "descricao": "Certidão Trabalhista", "palavras": ["certidao trabalho", "justica do trabalho", "trabalhista"]},
    {"item": 8, "descricao": "Portaria de Nomeação", "palavras": ["portaria", "nomeacao", "fiscal"]},
    {"item": 9, "descricao": "Atestado do Gestor", "palavras": ["atestado", "gestor", "liquidacao"]}
]

uploaded_file = st.file_uploader("📤 Selecione o PDF do processo", type=['pdf'])

if uploaded_file:
    with st.spinner("🔍 Analisando documento..."):
        # Ler o PDF
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text() or ""
        
        texto_lower = texto.lower()
        
        st.success(f"✅ PDF carregado: {uploaded_file.name}")
        st.info(f"📄 Páginas: {len(pdf_reader.pages)} | Caracteres extraídos: {len(texto)}")
        
        # Mostrar prévia do texto
        with st.expander("📄 Ver texto extraído do PDF"):
            st.text(texto[:1000] + "...")
        
        st.subheader("✅ RESULTADO DA ANÁLISE")
        
        # Analisar cada documento
        for doc in checklist:
            # Buscar palavras no texto
            encontrou = False
            palavras_encontradas = []
            
            for palavra in doc["palavras"]:
                if palavra in texto_lower:
                    encontrou = True
                    palavras_encontradas.append(palavra)
            
            # Mostrar resultado
            col1, col2, col3 = st.columns([1, 8, 2])
            
            with col1:
                st.markdown(f"**{doc['item']}**")
            
            with col2:
                st.markdown(doc["descricao"])
            
            with col3:
                if encontrou:
                    st.markdown("✅ **S**")
                else:
                    st.markdown("❌ **N**")
            
            # Mostrar observação
            if encontrou:
                st.caption(f"   Encontrado: {', '.join(palavras_encontradas)}")
            else:
                st.caption(f"   Não encontrado")
            
            st.divider()
        
        # Extrair CNPJ
        cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
        if cnpj:
            st.info(f"📊 CNPJ encontrado: {cnpj.group()}")
        
        # Extrair valor
        valor = re.search(r'R?\$?\s*([\d.,]+)', texto)
        if valor:
            st.info(f"💰 Valor encontrado: R$ {valor.group(1)}")

else:
    st.info("👆 Faça upload de um PDF para começar a análise")

st.markdown("---")
st.caption(f"IPEM-RJ - Análise em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
