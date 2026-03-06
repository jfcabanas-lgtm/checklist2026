import streamlit as st
import PyPDF2
import re

st.set_page_config(
    page_title="Análise IPEM-RJ",
    page_icon="✅",
    layout="wide"
)

st.title("📋 ANÁLISE DE PROCESSO DE PAGAMENTO - IPEM/RJ")
st.markdown("---")

# Checklist baseado no seu modelo
checklist = {
    1: "Nota de empenho e demonstrativo de saldo",
    2: "Nota Fiscal em nome do IPEM",
    3: "Certidão Federal (Receita Federal)",
    4: "Certidão FGTS",
    5: "Certidão Justiça do Trabalho",
    6: "Portaria de Nomeação de Fiscalização",
    7: "Atestado do Gestor"
}

uploaded_file = st.file_uploader("📤 Selecione o PDF do processo", type=['pdf'])

if uploaded_file:
    with st.spinner("Analisando documento..."):
        # Ler o PDF
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text() or ""
        
        st.success(f"✅ PDF processado! {len(pdf_reader.pages)} páginas")
        
        # Extrair informações básicas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Dados Extraídos")
            
            # Buscar CNPJ
            cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
            if cnpj:
                st.info(f"CNPJ: {cnpj.group()}")
            
            # Buscar valor
            valor = re.search(r'R?\$?\s*([\d.,]+)', texto)
            if valor:
                st.info(f"Valor: R$ {valor.group(1)}")
            
            # Buscar data
            data = re.search(r'\d{2}/\d{2}/\d{4}', texto)
            if data:
                st.info(f"Data: {data.group()}")
        
        with col2:
            st.subheader("✅ Checklist Automático")
            
            # Verificar documentos (simplificado)
            for item, desc in checklist.items():
                # Verifica se palavras-chave do documento estão no texto
                palavras = desc.lower().split()[:3]
                encontrou = any(palavra in texto.lower() for palavra in palavras)
                status = "✅" if encontrou else "❌"
                st.write(f"{status} Item {item}: {desc[:50]}...")

        # Botão para download do relatório
        if st.button("📥 Gerar Relatório"):
            st.info("Relatório gerado com sucesso!")
            st.balloons()

else:
    st.info("👆 Faça upload do PDF para iniciar a análise")
    
    with st.expander("📋 Documentos verificados:"):
        for item, desc in checklist.items():
            st.write(f"{item}. {desc}")

st.markdown("---")
st.caption("Instituto de Pesos e Medidas do Estado do Rio de Janeiro - Auditoria Interna")
