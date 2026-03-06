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

# Checklist COMPLETO com palavras-chave para busca
checklist_completo = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo", 
     "palavras": ["nota de empenho", "empenho", "demonstrativo de saldo", "saldo"], "tipo": "obrigatorio"},
    
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM", 
     "palavras": ["nota fiscal", "nf", "fatura", "ipem"], "tipo": "obrigatorio"},
    
    {"item": 3, "descricao": "Certidão Federal (Receita Federal)", 
     "palavras": ["certidao federal", "receita federal", "divida ativa", "tributos federais"], "tipo": "obrigatorio"},
    
    {"item": 4, "descricao": "Certidão FGTS", 
     "palavras": ["certidao fgts", "fgts", "regularidade fgts", "cnd fgts"], "tipo": "obrigatorio"},
    
    {"item": 5, "descricao": "Certidão Trabalhista (Justiça do Trabalho)", 
     "palavras": ["certidao trabalho", "justica do trabalho", "trabalhista", "cnd trabalhista"], "tipo": "obrigatorio"},
    
    {"item": 6, "descricao": "Indicação de tributos retidos na fonte", 
     "palavras": ["tributos retidos", "retencao", "fonte", "irrf", "pis", "cofins", "cssl"], "tipo": "condicional"},
    
    {"item": 7, "descricao": "Comprovação de não incidência de tributos", 
     "palavras": ["nao incidencia", "isencao", "imunidade", "dispensa"], "tipo": "condicional"},
    
    {"item": 8, "descricao": "Portaria de Nomeação de Fiscalização", 
     "palavras": ["portaria", "nomeacao", "fiscal", "gapre", "designacao"], "tipo": "obrigatorio"},
    
    {"item": 9, "descricao": "Atestado do Gestor do contrato", 
     "palavras": ["atestado", "gestor", "liquidacao", "servicos prestados", "a contento"], "tipo": "obrigatorio"},
    
    {"item": 10, "descricao": "Relação dos funcionários", 
     "palavras": ["relacao funcionarios", "relacao de empregados", "funcionarios", "equipe"], "tipo": "mao_obra"},
    
    {"item": 11, "descricao": "Comprovante da GFIP", 
     "palavras": ["gfip", "guia fgts", "conectividade social", "sefp"], "tipo": "mao_obra"},
    
    {"item": 12, "descricao": "Comprovante de pagamento do INSS", 
     "palavras": ["inss", "guia inss", "gps", "previdencia"], "tipo": "mao_obra"},
    
    {"item": 13, "descricao": "Comprovante de pagamento do FGTS", 
     "palavras": ["fgts", "guia fgts", "recolhimento fgts"], "tipo": "mao_obra"},
    
    {"item": 14, "descricao": "Protocolo - Conectividade Social", 
     "palavras": ["conectividade social", "protocolo", "arquivo", "transmissao"], "tipo": "mao_obra"},
    
    {"item": 15, "descricao": "Folha de pagamento", 
     "palavras": ["folha de pagamento", "folha", "payroll", "holerite"], "tipo": "mao_obra"},
    
    {"item": 16, "descricao": "Comprovante de pagamento dos salários", 
     "palavras": ["comprovante salario", "recibo salario", "holerite", "contracheque"], "tipo": "mao_obra"},
    
    {"item": 17, "descricao": "Comprovante de Vale transporte", 
     "palavras": ["vale transporte", "vt", "vale transport"], "tipo": "mao_obra"},
    
    {"item": 18, "descricao": "Comprovante de Vale alimentação/refeição", 
     "palavras": ["vale alimentacao", "va", "vale refeicao", "vr", "alimentacao"], "tipo": "mao_obra"},
    
    {"item": 19, "descricao": "Comprovante de rescisão e FGTS", 
     "palavras": ["rescisao", "fgts rescisorio", "termino de contrato", "demissao"], "tipo": "mao_obra"}
]

# Sidebar com informações
with st.sidebar:
    st.markdown("### 🏛️ GOVERNO DO ESTADO DO RIO DE JANEIRO")
    st.markdown("**Secretaria da Casa Civil**")
    st.markdown("**IPEM - Instituto de Pesos e Medidas**")
    st.markdown("**Auditoria Interna**")
    st.markdown("---")
    st.markdown("### 📋 Legenda:")
    st.markdown("✅ **S** = Documento encontrado")
    st.markdown("❌ **N** = Documento não encontrado")
    st.markdown("⚪ **NA** = Não Aplicável")
    st.markdown("---")
    st.caption(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Área principal
uploaded_file = st.file_uploader("📤 Selecione o PDF do processo para análise", type=['pdf'])

if uploaded_file:
    with st.spinner("🔍 Analisando documento... Isso pode levar alguns segundos"):
        try:
            # Ler o PDF
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            texto_completo = ""
            for page_num, page in enumerate(pdf_reader.pages):
                texto_pagina = page.extract_text() or ""
                texto_completo += texto_pagina + " "
            
            # Converter para minúsculo para busca
            texto_lower = texto_completo.lower()
            
            st.success(f"✅ PDF processado com sucesso! ({len(pdf_reader.pages)} páginas)")
            
            # Extrair informações básicas
            st.subheader("📊 Dados Extraídos do Processo")
            
            info_cols = st.columns(4)
            
            with info_cols[0]:
                # Buscar CNPJ
                cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
                cnpj = re.search(cnpj_pattern, texto_completo)
                st.markdown("**CNPJ:**")
                st.info(cnpj.group() if cnpj else "Não identificado")
            
            with info_cols[1]:
                # Buscar número do processo/SEI
                processo_pattern = r'(?:processo|sei)[:\s]*(\d+[.-]?\d*[.-]?\d*[.-]?\d*)'
                processo = re.search(processo_pattern, texto_lower)
                st.markdown("**Nº Processo/SEI:**")
                st.info(processo.group(1) if processo else "Não identificado")
            
            with info_cols[2]:
                # Buscar nota fiscal
                nf_pattern = r'(?:nota fiscal|nf)[:\s]*n[º°]?\s*(\d+)'
                nf = re.search(nf_pattern, texto_lower)
                st.markdown("**Nota Fiscal:**")
                st.info(nf.group(1) if nf else "Não identificado")
            
            with info_cols[3]:
                # Buscar valor
                valor_pattern = r'valor[:\s]*R?\$?\s*([\d.,]+)'
                valor = re.search(valor_pattern, texto_lower)
                st.markdown("**Valor:**")
                st.info(f"R$ {valor.group(1) if valor else '0,00'}")
            
            st.markdown("---")
            
            # Verificar se é serviço com mão-de-obra
            palavras_mao_obra = ['mao de obra', 'terceirizado', 'funcionario', 'empregado', 'posto de trabalho']
            tem_mao_obra = any(palavra in texto_lower for palavra in palavras_mao_obra)
            
            if tem_mao_obra:
                st.info("🔧 **Identificado:** Serviço com mão-de-obra - itens 10 a 19 serão verificados")
            
            # ANALISAR cada documento do checklist
            st.subheader("✅ RESULTADO DA ANÁLISE")
            
            # Criar lista para resultados
            resultados = []
            
            for doc in checklist_completo:
                # Determinar se o documento deve ser verificado
                if doc["tipo"] == "mao_obra" and not tem_mao_obra:
                    status = "NA"
                    observacao = "Sem mão-de-obra no processo"
                    encontrados = []
                else:
                    # Buscar cada palavra-chave no texto
                    encontrados = []
                    for palavra in doc["palavras"]:
                        if palavra in texto_lower:
                            encontrados.append(palavra)
                    
                    # Definir status baseado nos encontrados
                    if len(encontrados) >= 2:  # Encontrou pelo menos 2 palavras-chave
                        status = "S"
                    elif len(encontrados) == 1:  # Encontrou apenas 1 palavra
                        status = "S"  # Considera como encontrado
                    else:
                        status = "N"
                    
                    # Gerar observação
                    if status == "S":
                        if doc["item"] in [3,4,5]:  # Certidões
                            # Tentar encontrar data de validade
                            data_pattern = r'validade[:\s]*(\d{2}/\d{2}/\d{4})'
                            data_validade = re.search(data_pattern, texto_lower)
                            if data_validade:
                                observacao = f"Válida até: {data_validade.group(1)}"
                            else:
                                observacao = "Documento encontrado (verificar validade)"
                        elif doc["item"] == 8:
                            observacao = "Portaria IPEM/GAPRE"
                        elif doc["item"] == 9:
                            observacao = "Documento SEI"
                        else:
                            palavras_encontradas = ", ".join(encontrados[:3])
                            observacao = f"Encontrado: {palavras_encontradas}"
                    else:
                        observacao = "Documento não localizado"
                
                # Adicionar aos resultados
                resultados.append({
                    "item": doc["item"],
                    "descricao": doc["descricao"],
                    "status": status,
                    "observacao": observacao,
                    "palavras_encontradas": encontrados if 'encontrados' in locals() else []
                })
            
            # MOSTRAR RESULTADOS EM FORMATO DE TABELA
            for res in resultados:
                if res["status"] == "S":
                    col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
                    with col1:
                        st.markdown(f"**{res['item']}**")
                    with col2:
                        st.markdown(res["descricao"])
                    with col3:
                        st.markdown("✅ **S**")
                    with col4:
                        st.markdown(res["observacao"])
                elif res["status"] == "N":
                    col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
                    with col1:
                        st.markdown(f"**{res['item']}**")
                    with col2:
                        st.markdown(res["descricao"])
                    with col3:
                        st.markdown("❌ **N**")
                    with col4:
                        st.markdown(res["observacao"])
                else:
                    col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
                    with col1:
                        st.markdown(f"**{res['item']}**")
                    with col2:
                        st.markdown(res["descricao"])
                    with col3:
                        st.markdown("⚪ **NA**")
                    with col4:
                        st.markdown(res["observacao"])
            
            # RESUMO DA ANÁLISE
            st.markdown("---")
            st.subheader("📊 Resumo da Análise")
            
            total_s = sum(1 for r in resultados if r["status"] == "S")
            total_n = sum(1 for r in resultados if r["status"] == "N")
            total_na = sum(1 for r in resultados if r["status"] == "NA")
            
            resumo_cols = st.columns(3)
            with resumo_cols[0]:
                st.metric("Documentos Encontrados", total_s, delta=None)
            with resumo_cols[1]:
                st.metric("Documentos Faltantes", total_n, delta=None)
            with resumo_cols[2]:
                st.metric("Não Aplicáveis", total_na, delta=None)
            
            # CONCLUSÃO
            st.markdown("---")
            st.subheader("📝 Conclusão")
            
            # Verificar documentos obrigatórios (itens 1,2,3,4,5,8,9)
            docs_obrigatorios = [r for r in resultados if r["item"] in [1,2,3,4,5,8,9]]
            obrigatorios_s = sum(1 for r in docs_obrigatorios if r["status"] == "S")
            
            if obrigatorios_s == len(docs_obrigatorios):
                st.success("""
                **✅ Nada tem a opor quanto ao prosseguimento**, 
                com fulcro no art. 62, da Lei 4.320, de 17/03/1964
                """)
            else:
                faltantes = [r["item"] for r in docs_obrigatorios if r["status"] == "N"]
                st.warning(f"""
                **⚠️ Documentos obrigatórios faltantes: {faltantes}**
                
                Após a regularização das exigências, retornar à Auditoria Interna 
                para análise processual, com fulcro no art. 62, da Lei 4.320/64
                """)
            
            # Campo para observações
            st.text_area("Observações finais:", 
                        value=f"Despesa referente a {datetime.now().strftime('%m/%Y')}.", 
                        height=100)
            
            # Botão para download (placeholder)
            if st.button("📥 Gerar Relatório PDF"):
                st.info("Funcionalidade de PDF será implementada em breve!")
                st.balloons()
            
            # Mostrar trecho do texto analisado (para debug/transparência)
            with st.expander("🔍 Ver trecho do texto analisado"):
                st.text(texto_completo[:2000] + "...")
            
        except Exception as e:
            st.error(f"Erro ao processar o PDF: {str(e)}")
            st.info("Verifique se o arquivo é um PDF válido e não está protegido por senha")

else:
    st.info("👆 Faça upload do PDF para iniciar a análise automática")
    
    # Mostrar lista de documentos
    with st.expander("📋 Lista completa de documentos verificados (19 itens)"):
        for doc in checklist_completo:
            st.write(f"**{doc['item']}.** {doc['descricao']}")

st.markdown("---")
st.caption("Instituto de Pesos e Medidas do Estado do Rio de Janeiro - Auditoria Interna")
