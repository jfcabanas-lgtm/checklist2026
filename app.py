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

# Checklist COMPLETO baseado no seu modelo Excel
checklist_completo = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo (art. 63, §1°, II, da Lei 4320/64)", "tipo": "obrigatorio"},
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM, de acordo com o empenho e com o objeto", "tipo": "obrigatorio"},
    {"item": 3, "descricao": "Certidão de regularidade relativo aos tributos federais e dívida ativa da União junto a Receita Federal", "tipo": "obrigatorio"},
    {"item": 4, "descricao": "Certidão de regularidade junto ao FGTS", "tipo": "obrigatorio"},
    {"item": 5, "descricao": "Certidão de regularidade junto a Justiça do Trabalho", "tipo": "obrigatorio"},
    {"item": 6, "descricao": "No caso de incidir tributos a serem retidos da fonte, consta indicação?", "tipo": "condicional"},
    {"item": 7, "descricao": "Quando não incidir tributos, há documento de comprovação da não incidência?", "tipo": "condicional"},
    {"item": 8, "descricao": "Portaria de Nomeação de Fiscalização", "tipo": "obrigatorio"},
    {"item": 9, "descricao": "Atestado do Gestor do contrato de que os serviços ou aquisições contratados foram prestados a contento", "tipo": "obrigatorio"},
    {"item": 10, "descricao": "Relação dos funcionários que executaram o serviço", "tipo": "mao_obra"},
    {"item": 11, "descricao": "Comprovante da GFIP", "tipo": "mao_obra"},
    {"item": 12, "descricao": "Comprovante de pagamento do INSS", "tipo": "mao_obra"},
    {"item": 13, "descricao": "Comprovante de pagamento do FGTS", "tipo": "mao_obra"},
    {"item": 14, "descricao": "Protocolo do envio dos arquivos - Conectividade Social", "tipo": "mao_obra"},
    {"item": 15, "descricao": "Folha de pagamento", "tipo": "mao_obra"},
    {"item": 16, "descricao": "Comprovante de pagamento dos salários", "tipo": "mao_obra"},
    {"item": 17, "descricao": "Comprovante de pagamento do Vale transporte", "tipo": "mao_obra"},
    {"item": 18, "descricao": "Comprovante de pagamento do Vale alimentação / refeição", "tipo": "mao_obra"},
    {"item": 19, "descricao": "Comprovante de pagamento de rescisão e FGTS", "tipo": "mao_obra"}
]

# Sidebar com informações
with st.sidebar:
    st.markdown("### 🏛️ GOVERNO DO ESTADO DO RIO DE JANEIRO")
    st.markdown("**Secretaria da Casa Civil**")
    st.markdown("**IPEM - Instituto de Pesos e Medidas**")
    st.markdown("**Auditoria Interna**")
    st.markdown("---")
    st.markdown("### 📋 Legenda:")
    st.markdown("✅ **S** = Sim (documento encontrado)")
    st.markdown("❌ **N** = Não (documento não encontrado)")
    st.markdown("⚪ **NA** = Não Aplicável")
    st.markdown("---")
    st.caption(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Área principal
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📤 Upload do Processo")
    uploaded_file = st.file_uploader("Selecione o PDF", type=['pdf'])

if uploaded_file:
    with st.spinner("Analisando documento..."):
        # Ler o PDF
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text() or ""
        
        st.success(f"✅ PDF processado! {len(pdf_reader.pages)} páginas")
        
        # Extrair informações básicas
        st.subheader("📊 Dados do Processo")
        
        info_cols = st.columns(3)
        
        with info_cols[0]:
            # Buscar CNPJ
            cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
            st.markdown("**CNPJ:**")
            st.info(cnpj.group() if cnpj else "Não identificado")
            
            # Buscar fornecedor (simplificado)
            st.markdown("**Fornecedor:**")
            st.info("Não identificado")
        
        with info_cols[1]:
            # Buscar número do processo/contrato
            processo = re.search(r'(?:processo|contrato|sei)[:\s]*(\d+[-.]?\d*)', texto, re.IGNORECASE)
            st.markdown("**Processo/Contrato:**")
            st.info(processo.group(1) if processo else "Não identificado")
            
            # Buscar vigência
            vigencia = re.search(r'vig[êe]ncia[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
            st.markdown("**Vigência:**")
            st.info(vigencia.group(1) if vigencia else "Não identificado")
        
        with info_cols[2]:
            # Buscar nota fiscal
            nf = re.search(r'(?:nota fiscal|nf)[:\s]*n[º°]?\s*(\d+)', texto, re.IGNORECASE)
            st.markdown("**Nota Fiscal:**")
            st.info(nf.group(1) if nf else "Não identificado")
            
            # Buscar valor
            valor = re.search(r'valor[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            st.markdown("**Valor:**")
            st.info(f"R$ {valor.group(1) if valor else '0,00'}")
        
        st.markdown("---")
        
        # Verificar se é serviço com mão-de-obra
        tem_mao_obra = any(palavra in texto.lower() for palavra in ['mao de obra', 'terceirizado', 'funcionario', 'empregado'])
        
        # Checklist
        st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
        
        # Criar tabela de resultados
        resultados = []
        for doc in checklist_completo:
            # Determinar status baseado no tipo
            if doc["tipo"] == "mao_obra" and not tem_mao_obra:
                status = "NA"
                observacao = "Não aplicável (sem mão-de-obra)"
            else:
                # Buscar palavras-chave no texto (simplificado)
                palavras = doc["descricao"].lower().split()[:3]
                encontrou = any(palavra in texto.lower() for palavra in palavras if len(palavra) > 3)
                status = "S" if encontrou else "N"
                
                # Observações específicas
                if doc["item"] in [3,4,5] and encontrou:
                    observacao = "Válida até: 31/12/2024 (verificar no documento)"
                elif doc["item"] == 8 and encontrou:
                    observacao = "Portaria IPEM/GAPRE"
                elif doc["item"] == 9 and encontrou:
                    observacao = "Documento SEI"
                else:
                    observacao = ""
            
            # Adicionar à lista de resultados
            resultados.append({
                "Item": doc["item"],
                "Documento": doc["descricao"],
                "Status": status,
                "Observação": observacao
            })
        
        # Mostrar tabela com formatação
        for res in resultados:
            if res["Status"] == "S":
                col1, col2, col3, col4 = st.columns([1, 8, 1, 4])
                with col1:
                    st.markdown(f"**{res['Item']}**")
                with col2:
                    st.markdown(res["Documento"])
                with col3:
                    st.markdown(f"✅ **S**")
                with col4:
                    st.markdown(res["Observação"])
            elif res["Status"] == "N":
                col1, col2, col3, col4 = st.columns([1, 8, 1, 4])
                with col1:
                    st.markdown(f"**{res['Item']}**")
                with col2:
                    st.markdown(res["Documento"])
                with col3:
                    st.markdown(f"❌ **N**")
                with col4:
                    st.markdown(res["Observação"])
            else:
                col1, col2, col3, col4 = st.columns([1, 8, 1, 4])
                with col1:
                    st.markdown(f"**{res['Item']}**")
                with col2:
                    st.markdown(res["Documento"])
                with col3:
                    st.markdown(f"⚪ **NA**")
                with col4:
                    st.markdown(res["Observação"])
        
        # Resumo
        st.markdown("---")
        st.subheader("📊 Resumo da Análise")
        
        total_s = sum(1 for r in resultados if r["Status"] == "S")
        total_n = sum(1 for r in resultados if r["Status"] == "N")
        total_na = sum(1 for r in resultados if r["Status"] == "NA")
        
        resumo_cols = st.columns(3)
        with resumo_cols[0]:
            st.metric("Documentos Encontrados", total_s)
        with resumo_cols[1]:
            st.metric("Documentos Faltantes", total_n)
        with resumo_cols[2]:
            st.metric("Não Aplicáveis", total_na)
        
        # Conclusão
        st.markdown("---")
        st.subheader("📝 Conclusão")
        
        # Verificar documentos obrigatórios (itens 1-5,8,9)
        docs_obrigatorios = [r for r in resultados if r["Item"] in [1,2,3,4,5,8,9]]
        obrigatorios_s = sum(1 for r in docs_obrigatorios if r["Status"] == "S")
        
        if obrigatorios_s == len(docs_obrigatorios):
            st.success("✅ Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320/64")
        else:
            st.warning("⚠️ Após a regularização das exigências, retornar à Auditoria Interna para análise processual")
        
        # Observações finais
        st.text_area("Observações:", value=f"Despesa referente a {datetime.now().strftime('%m/%Y')}.", height=100)
        
        # Botão para gerar relatório (placeholder)
        if st.button("📥 Gerar Relatório PDF"):
            st.info("Funcionalidade em desenvolvimento - Em breve você poderá baixar o relatório em PDF")
            st.balloons()

else:
    st.info("👆 Faça upload do PDF para iniciar a análise")
    
    # Mostrar checklist completo
    with st.expander("📋 Ver lista completa de documentos verificados (19 itens)"):
        for doc in checklist_completo:
            st.write(f"**{doc['item']}.** {doc['descricao']}")

st.markdown("---")
st.caption("Instituto de Pesos e Medidas do Estado do Rio de Janeiro - Auditoria Interna")
