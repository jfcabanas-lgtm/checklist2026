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

# Checklist COMPLETO com 19 itens e palavras-chave
checklist = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo", 
     "palavras": ["nota de empenho", "empenho", "demonstrativo de saldo", "saldo"]},
    
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM", 
     "palavras": ["nota fiscal", "nf", "fatura", "ipem"]},
    
    {"item": 3, "descricao": "Certidão Federal (Receita Federal)", 
     "palavras": ["certidao federal", "receita federal", "divida ativa", "tributos federais"]},
    
    {"item": 4, "descricao": "Certidão FGTS", 
     "palavras": ["certidao fgts", "fgts", "regularidade fgts", "cnd fgts"]},
    
    {"item": 5, "descricao": "Certidão Trabalhista (Justiça do Trabalho)", 
     "palavras": ["certidao trabalho", "justica do trabalho", "trabalhista", "cnd trabalhista"]},
    
    {"item": 6, "descricao": "Indicação de tributos retidos na fonte", 
     "palavras": ["tributos retidos", "retencao", "fonte", "irrf", "pis", "cofins"]},
    
    {"item": 7, "descricao": "Comprovação de não incidência de tributos", 
     "palavras": ["nao incidencia", "isencao", "imunidade", "dispensa"]},
    
    {"item": 8, "descricao": "Portaria de Nomeação de Fiscalização", 
     "palavras": ["portaria", "nomeacao", "fiscal", "gapre", "designacao"]},
    
    {"item": 9, "descricao": "Atestado do Gestor do contrato", 
     "palavras": ["atestado", "gestor", "liquidacao", "servicos prestados", "a contento"]},
    
    {"item": 10, "descricao": "Relação dos funcionários que executaram o serviço", 
     "palavras": ["relacao funcionarios", "relacao de empregados", "funcionarios", "equipe"]},
    
    {"item": 11, "descricao": "Comprovante da GFIP", 
     "palavras": ["gfip", "guia fgts", "conectividade social", "sefp"]},
    
    {"item": 12, "descricao": "Comprovante de pagamento do INSS", 
     "palavras": ["inss", "guia inss", "gps", "previdencia"]},
    
    {"item": 13, "descricao": "Comprovante de pagamento do FGTS", 
     "palavras": ["fgts", "guia fgts", "recolhimento fgts"]},
    
    {"item": 14, "descricao": "Protocolo do envio dos arquivos - Conectividade Social", 
     "palavras": ["conectividade social", "protocolo", "transmissao", "conectividade"]},
    
    {"item": 15, "descricao": "Folha de pagamento", 
     "palavras": ["folha de pagamento", "folha", "payroll", "holerite"]},
    
    {"item": 16, "descricao": "Comprovante de pagamento dos salários", 
     "palavras": ["comprovante salario", "recibo salario", "holerite", "contracheque"]},
    
    {"item": 17, "descricao": "Comprovante de pagamento do Vale transporte", 
     "palavras": ["vale transporte", "vt", "vale transport"]},
    
    {"item": 18, "descricao": "Comprovante de pagamento do Vale alimentação / refeição", 
     "palavras": ["vale alimentacao", "va", "vale refeicao", "vr", "alimentacao"]},
    
    {"item": 19, "descricao": "Comprovante de pagamento de rescisão e FGTS", 
     "palavras": ["rescisao", "fgts rescisorio", "termino de contrato", "demissao"]}
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
    st.markdown("⚪ **NA** = Não Aplicável (sem mão-de-obra)")
    st.markdown("---")
    st.caption(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Upload do arquivo
uploaded_file = st.file_uploader("📤 Selecione o PDF do processo", type=['pdf'])

if uploaded_file:
    with st.spinner("🔍 Analisando documento completo..."):
        # Ler o PDF INTEIRO
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        texto_completo = ""
        for page in pdf_reader.pages:
            texto_completo += page.extract_text() or ""
        
        texto_lower = texto_completo.lower()
        
        st.success(f"✅ PDF carregado: {uploaded_file.name}")
        st.info(f"📄 Páginas: {len(pdf_reader.pages)} | Caracteres extraídos: {len(texto_completo)}")
        
        # Extrair informações básicas
        st.subheader("📊 DADOS DO PROCESSO")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto_completo)
            st.markdown("**CNPJ:**")
            st.info(cnpj.group() if cnpj else "Não identificado")
        
        with col2:
            processo = re.search(r'(?:processo|sei)[:\s]*(\d+[.-]?\d*[.-]?\d*)', texto_lower)
            st.markdown("**Processo/SEI:**")
            st.info(processo.group(1) if processo else "Não identificado")
        
        with col3:
            nf = re.search(r'(?:nota fiscal|nf)[:\s]*n[º°]?\s*(\d+)', texto_lower)
            st.markdown("**Nota Fiscal:**")
            st.info(nf.group(1) if nf else "Não identificado")
        
        with col4:
            valor = re.search(r'valor[:\s]*R?\$?\s*([\d.,]+)', texto_lower)
            st.markdown("**Valor:**")
            st.info(f"R$ {valor.group(1) if valor else '0,00'}")
        
        st.markdown("---")
        
        # Verificar se é serviço com mão-de-obra
        palavras_mao_obra = ['mao de obra', 'terceirizado', 'funcionario', 'empregado', 'posto de trabalho']
        tem_mao_obra = any(palavra in texto_lower for palavra in palavras_mao_obra)
        
        if tem_mao_obra:
            st.info("🔧 **Identificado:** Serviço com mão-de-obra - itens 10 a 19 serão verificados")
        
        # RESULTADO DA ANÁLISE
        st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
        
        # Analisar cada documento
        for doc in checklist:
            # Determinar se aplicável
            if doc["item"] >= 10 and not tem_mao_obra:
                status = "NA"
                observacao = "Sem mão-de-obra no processo"
                cor = "⚪"
            else:
                # Buscar palavras no texto
                palavras_encontradas = []
                for palavra in doc["palavras"]:
                    if palavra in texto_lower:
                        palavras_encontradas.append(palavra)
                
                # Definir status
                if len(palavras_encontradas) >= 1:
                    status = "S"
                    cor = "✅"
                    if doc["item"] in [3,4,5]:  # Certidões
                        # Tentar encontrar data
                        data = re.search(r'validade[:\s]*(\d{2}/\d{2}/\d{4})', texto_lower)
                        if data:
                            observacao = f"Válida até: {data.group(1)}"
                        else:
                            observacao = f"Encontrado ({', '.join(palavras_encontradas[:2])})"
                    else:
                        observacao = f"Encontrado ({', '.join(palavras_encontradas[:2])})"
                else:
                    status = "N"
                    cor = "❌"
                    observacao = "Documento não localizado"
            
            # Mostrar resultado
            col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
            
            with col1:
                st.markdown(f"**{doc['item']}**")
            with col2:
                st.markdown(doc["descricao"])
            with col3:
                st.markdown(f"{cor} **{status}**")
            with col4:
                st.caption(observacao)
        
        # RESUMO
        st.markdown("---")
        st.subheader("📊 RESUMO DA ANÁLISE")
        
        # Calcular estatísticas
        total_itens = len(checklist)
        s_count = 0
        n_count = 0
        na_count = 0
        
        for doc in checklist:
            if doc["item"] >= 10 and not tem_mao_obra:
                na_count += 1
            else:
                palavras_encontradas = [p for p in doc["palavras"] if p in texto_lower]
                if len(palavras_encontradas) >= 1:
                    s_count += 1
                else:
                    n_count += 1
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Documentos Encontrados (S)", s_count)
        with col2:
            st.metric("Documentos Faltantes (N)", n_count)
        with col3:
            st.metric("Não Aplicáveis (NA)", na_count)
        
        # CONCLUSÃO
        st.markdown("---")
        st.subheader("📝 CONCLUSÃO")
        
        # Verificar documentos obrigatórios (itens 1-5,8,9)
        docs_obrigatorios = [1,2,3,4,5,8,9]
        obrigatorios_encontrados = 0
        
        for item in docs_obrigatorios:
            doc = next(d for d in checklist if d["item"] == item)
            palavras_encontradas = [p for p in doc["palavras"] if p in texto_lower]
            if len(palavras_encontradas) >= 1:
                obrigatorios_encontrados += 1
        
        if obrigatorios_encontrados == len(docs_obrigatorios):
            st.success("""
            **✅ Nada tem a opor quanto ao prosseguimento**, 
            com fulcro no art. 62, da Lei 4.320/64
            """)
        else:
            st.warning(f"""
            **⚠️ Documentos obrigatórios faltantes: {len(docs_obrigatorios) - obrigatorios_encontrados}**
            
            Após a regularização das exigências, retornar à Auditoria Interna 
            para análise processual, com fulcro no art. 62, da Lei 4.320/64
            """)
        
        # Observações finais
        st.text_area("📌 Observações:", 
                    value=f"Despesa referente a {datetime.now().strftime('%m/%Y')}.", 
                    height=100)
        
        # Mostrar texto completo (opcional)
        with st.expander("📄 Ver texto completo extraído do PDF"):
            st.text(texto_completo[:5000] + "...")
        
else:
    st.info("👆 Faça upload de um PDF para iniciar a análise completa")

st.markdown("---")
st.caption(f"IPEM-RJ - Auditoria Interna | Análise em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
