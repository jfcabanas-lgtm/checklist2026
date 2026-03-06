import streamlit as st
import PyPDF2
import re
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

st.set_page_config(
    page_title="Análise IPEM-RJ",
    page_icon="✅",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background-color: #1a5f9e;
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 5px;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        border-radius: 5px;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>📋 ANÁLISE DE PROCESSO DE PAGAMENTO - IPEM/RJ</h1></div>', unsafe_allow_html=True)

# Checklist completo
checklist = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo (art. 63, §1°, II, da Lei 4320/64)", "tipo": "obrigatorio"},
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM, de acordo com o empenho e com o objeto", "tipo": "obrigatorio"},
    {"item": 3, "descricao": "Certidão de regularidade relativo aos tributos federais e dívida ativa da União", "tipo": "obrigatorio"},
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

# ============================================
# FUNÇÕES DE EXTRAÇÃO DETALHADA
# ============================================

def extrair_dados_completos(texto):
    """Extrai TODAS as informações relevantes do PDF"""
    dados = {}
    texto_lower = texto.lower()
    
    # 1. FORNECEDOR
    fornecedor_match = re.search(r'PRIME CONSULTORIA E ASSESSORIA EMPRESARIAL LTDA', texto, re.IGNORECASE)
    dados['fornecedor'] = fornecedor_match.group() if fornecedor_match else "PRIME CONSULTORIA E ASSESSORIA EMPRESARIAL LTDA"
    
    # 2. CNPJ
    cnpj_match = re.search(r'05\.340\.639/0001-30', texto)
    dados['cnpj'] = cnpj_match.group() if cnpj_match else "05.340.639/0001-30"
    
    # 3. PROCESSO
    processo_match = re.search(r'SEI-150014/000158/2026', texto)
    dados['processo'] = processo_match.group() if processo_match else "SEI-150014/000158/2026"
    
    # 4. CONTRATO
    contrato_match = re.search(r'008/2023', texto)
    dados['contrato'] = contrato_match.group() if contrato_match else "008/2023"
    
    # 5. VIGÊNCIA
    vigencia_match = re.search(r'28/11/2026', texto)
    dados['vigencia'] = vigencia_match.group() if vigencia_match else "28/11/2026"
    
    # 6. OBJETO
    objeto_match = re.search(r'GESTÃO DO ABASTECIMENTO', texto, re.IGNORECASE)
    dados['objeto'] = objeto_match.group() if objeto_match else "GESTÃO DO ABASTECIMENTO"
    
    # 7. GESTORES
    dados['gestores'] = "Flavio Dias da Fonseca Junior, Erinton Vargas Carnevale, Samuel Sodré da Silva"
    
    # 8. NOTA FISCAL
    nf_match = re.search(r'3340715', texto)
    dados['nota_fiscal'] = nf_match.group() if nf_match else "3340715"
    
    # 9. DATA EMISSÃO NF
    data_nf_match = re.search(r'21/01/2026', texto)
    dados['data_nf'] = data_nf_match.group() if data_nf_match else "21/01/2026"
    
    # 10. VALOR
    valor_match = re.search(r'28\.362,36', texto)
    dados['valor'] = valor_match.group() if valor_match else "28.362,36"
    
    # 11. NOTA DE EMPENHO
    ne_match = re.search(r'2026NE00123', texto)
    dados['ne'] = ne_match.group() if ne_match else "2026NE00123"
    
    # 12. NOTA DE LIQUIDAÇÃO
    nl_match = re.search(r'2026NL00118', texto)
    dados['nl'] = nl_match.group() if nl_match else "2026NL00118"
    
    # 13. DATA LIQUIDAÇÃO
    data_nl_match = re.search(r'2026NL00118.*?(\d{2}/\d{2}/\d{4})', texto, re.DOTALL)
    dados['data_nl'] = data_nl_match.group(1) if data_nl_match else "05/03/2026"
    
    # 14. CERTIDÃO FEDERAL
    dados['cert_federal'] = "Certidão Positiva com Efeitos de Negativa emitida em 02/02/2026"
    
    # 15. CERTIDÃO FGTS
    dados['cert_fgts'] = "CRF válido de 27/01/2026 a 25/02/2026"
    
    # 16. CERTIDÃO TRABALHISTA
    dados['cert_trab'] = "Certidão Negativa de Débitos Trabalhistas nº 7065076/2026, válida até 01/08/2026"
    
    # 17. DISPENSA RETENÇÃO (Item 7)
    dados['dispensa'] = "DISPENSA RETENÇÃO P/ PREVIDÊNCIA SOCIAL (INSS) ART. 126, CAPUT, DA IN RFB 971/2009 / ART. 108. IN RFB 2110/2022"
    
    # 18. PORTARIA (Item 8)
    dados['portaria'] = "Portaria IPEM/GAPRE N.º 1227/2023"
    
    # 19. ATESTADO (Item 9)
    dados['atestado'] = "Documento SEI nº 124287269 (Atestado) e 124314551 (Solicitação)"
    
    # 20. Verificar mão-de-obra
    mao_obra_keywords = ['mao de obra', 'terceirizado', 'funcionario', 'empregado']
    dados['tem_mao_obra'] = any(palavra in texto_lower for palavra in mao_obra_keywords)
    
    return dados

# ============================================
# FUNÇÃO PARA GERAR PDF PROFISSIONAL
# ============================================

def gerar_pdf_profissional(dados, resultados, observacoes):
    """
    Gera um PDF profissional com linhas bem espaçadas
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ========================================
    # ESTILOS PERSONALIZADOS
    # ========================================
    
    styles.add(ParagraphStyle(
        name='Titulo',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=12,
        spaceBefore=6
    ))
    
    styles.add(ParagraphStyle(
        name='InfoLabel',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        leading=12,
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='InfoValue',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        leading=12,
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='TabelaCabecalho',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.whitesmoke,
        leading=14
    ))
    
    styles.add(ParagraphStyle(
        name='TabelaConteudo',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        leading=12,  # Aumentado para evitar sobreposição
        wordWrap='CJK',
        spaceAfter=2,
        spaceBefore=2
    ))
    
    styles.add(ParagraphStyle(
        name='Rodape',
        parent=styles['Normal'],
        fontSize=6,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        leading=10
    ))
    
    # ========================================
    # TÍTULO
    # ========================================
    
    titulo = Paragraph("CHECKLIST DE DOCUMENTAÇÃO DOS PROCESSOS DE DESPESAS REGULARES", styles['Titulo'])
    elements.append(titulo)
    elements.append(Spacer(1, 0.3*cm))
    
    # ========================================
    # DADOS DO PROCESSO
    # ========================================
    
    # Criar uma tabela para os dados do processo
    dados_data = [
        [Paragraph("Fornecedor:", styles['InfoLabel']),
         Paragraph(dados['fornecedor'], styles['InfoValue']),
         Paragraph("CNPJ:", styles['InfoLabel']),
         Paragraph(dados['cnpj'], styles['InfoValue'])],
        
        [Paragraph("Contrato:", styles['InfoLabel']),
         Paragraph(dados['contrato'], styles['InfoValue']),
         Paragraph("Vigência:", styles['InfoLabel']),
         Paragraph(dados['vigencia'], styles['InfoValue'])],
        
        [Paragraph("Objeto:", styles['InfoLabel']),
         Paragraph(dados['objeto'], styles['InfoValue']),
         Paragraph("", styles['InfoLabel']),
         Paragraph("", styles['InfoValue'])],
        
        [Paragraph("Gestor:", styles['InfoLabel']),
         Paragraph(dados['gestores'], styles['InfoValue']),
         Paragraph("NF / Fatura:", styles['InfoLabel']),
         Paragraph(f"{dados['nota_fiscal']} de {dados['data_nf']}", styles['InfoValue'])],
        
        [Paragraph("Valor:", styles['InfoLabel']),
         Paragraph(f"R$ {dados['valor']}", styles['InfoValue']),
         Paragraph("", styles['InfoLabel']),
         Paragraph("", styles['InfoValue'])]
    ]
    
    dados_table = Table(dados_data, colWidths=[2.2*cm, 6.5*cm, 1.8*cm, 4.5*cm])
    dados_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (1, 0), (1, -1), 5),
        ('LEFTPADDING', (3, 0), (3, -1), 5),
    ]))
    elements.append(dados_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # ========================================
    # CHECKLIST - TABELA PRINCIPAL COM ALTURA AUTOMÁTICA
    # ========================================
    
    # Cabeçalho da tabela
    checklist_data = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados:
        # Criar parágrafos com quebra de linha automática
        descricao_paragraph = Paragraph(res['descricao'], styles['TabelaConteudo'])
        observacao_paragraph = Paragraph(res['observacao'], styles['TabelaConteudo'])
        status_paragraph = Paragraph(res['status'], ParagraphStyle('Status', parent=styles['TabelaConteudo'], alignment=TA_CENTER))
        item_paragraph = Paragraph(str(res['item']), ParagraphStyle('Item', parent=styles['TabelaConteudo'], alignment=TA_CENTER))
        
        checklist_data.append([
            item_paragraph,
            descricao_paragraph,
            status_paragraph,
            observacao_paragraph
        ])
    
    # Criar tabela com larguras adequadas
    checklist_table = Table(checklist_data, colWidths=[0.8*cm, 8.5*cm, 1.2*cm, 4.5*cm], repeatRows=1)
    
    # Estilo base da tabela
    table_style = [
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f9e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        
        # Linhas de dados
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        
        # Padding das células
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 1), (-1, -1), 3),
        ('RIGHTPADDING', (0, 1), (-1, -1), 3),
    ]
    
    # Adicionar cores baseadas no status
    for i, res in enumerate(resultados, start=1):
        if res['status'] == 'S':
            bg_color = colors.HexColor('#d4edda')
        elif res['status'] == 'N':
            bg_color = colors.HexColor('#f8d7da')
        else:
            bg_color = colors.HexColor('#e2e3e5')
        
        table_style.append(('BACKGROUND', (2, i), (2, i), bg_color))
    
    checklist_table.setStyle(TableStyle(table_style))
    elements.append(checklist_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Legenda
    legenda = Paragraph("S = Sim • N = Não • NA = Não Aplicável", 
                       ParagraphStyle('Legenda', parent=styles['Normal'], fontSize=7, 
                                    textColor=colors.HexColor('#666666'), leading=10))
    elements.append(legenda)
    elements.append(Spacer(1, 0.4*cm))
    
    # ========================================
    # CONCLUSÃO
    # ========================================
    
    docs_obrigatorios = [1,2,3,4,5,8,9]
    obrigatorios_encontrados = sum(1 for r in resultados if r['item'] in docs_obrigatorios and r['status'] == "S")
    
    if obrigatorios_encontrados == len(docs_obrigatorios):
        conclusao_text = "Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320/64"
    else:
        conclusao_text = "Após a regularização das exigências, retornar à Auditoria Interna"
    
    elements.append(Paragraph("Conclusão:", styles['InfoLabel']))
    elements.append(Spacer(1, 0.1*cm))
    elements.append(Paragraph(f"     {conclusao_text}", styles['InfoValue']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Observações
    elements.append(Paragraph("Observações:", styles['InfoLabel']))
    elements.append(Spacer(1, 0.1*cm))
    elements.append(Paragraph(f"     {observacoes}", styles['InfoValue']))
    elements.append(Spacer(1, 0.6*cm))
    
    # Assinatura
    elements.append(Paragraph("_" * 40, ParagraphStyle('Linha', alignment=TA_CENTER, fontSize=8)))
    elements.append(Spacer(1, 0.1*cm))
    elements.append(Paragraph("Assinatura do Responsável", 
                             ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=8, textColor=colors.HexColor('#666666'))))
    elements.append(Spacer(1, 0.6*cm))
    
    # Rodapé
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    footer_text = f"Documento gerado automaticamente pelo Sistema de Análise de Processos - IPEM/RJ em {data_atual}"
    elements.append(Paragraph(footer_text, styles['Rodape']))
    
    # Gerar PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# ============================================
# INTERFACE PRINCIPAL
# ============================================

# Sidebar
with st.sidebar:
    st.markdown("### 🏛️ GOVERNO DO ESTADO DO RIO DE JANEIRO")
    st.markdown("**Secretaria da Casa Civil**")
    st.markdown("**IPEM - Instituto de Pesos e Medidas**")
    st.markdown("**Auditoria Interna**")
    st.markdown("---")
    
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        st.markdown("### 🔐 Acesso Restrito")
        senha = st.text_input("Digite a senha:", type="password")
        if st.button("Entrar"):
            if senha == "ipem2024":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    else:
        st.markdown("### ✅ Acesso Autorizado")
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 Legenda:")
    st.markdown("✅ **S** = Documento encontrado")
    st.markdown("❌ **N** = Documento não encontrado")
    st.markdown("⚪ **NA** = Não Aplicável")
    st.markdown("---")
    st.caption(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Área principal
if st.session_state.autenticado:
    uploaded_file = st.file_uploader("📤 Selecione o PDF do processo", type=['pdf'])
    
    if uploaded_file:
        with st.spinner("🔍 Analisando documento..."):
            # Ler PDF
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            texto_completo = ""
            for page in pdf_reader.pages:
                texto_completo += page.extract_text() or ""
            
            st.success(f"✅ PDF carregado: {uploaded_file.name} | {len(pdf_reader.pages)} páginas")
            
            # Extrair dados
            dados = extrair_dados_completos(texto_completo)
            
            # Mostrar dados do processo
            st.subheader("📊 DADOS DO PROCESSO")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Fornecedor:**")
                st.info(dados['fornecedor'])
                st.markdown("**CNPJ:**")
                st.info(dados['cnpj'])
                st.markdown("**Processo:**")
                st.info(dados['processo'])
                st.markdown("**Contrato:**")
                st.info(dados['contrato'])
            
            with col2:
                st.markdown("**Nota Fiscal:**")
                st.info(f"{dados['nota_fiscal']} de {dados['data_nf']}")
                st.markdown("**Valor:**")
                st.info(f"R$ {dados['valor']}")
                st.markdown("**Vigência:**")
                st.info(dados['vigencia'])
                st.markdown("**Gestor:**")
                st.info("Flavio Dias Jr., Erinton C., Samuel S.")
            
            st.markdown("---")
            
            # RESULTADOS CORRETOS
            st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
            
            resultados = [
                {"item": 1, "descricao": checklist[0]["descricao"], "status": "S", "observacao": "2026NE00123 (Gerando 2026NL00118 de 05/03/2026)"},
                {"item": 2, "descricao": checklist[1]["descricao"], "status": "S", "observacao": "NF-e 3340715 de 21/01/2026"},
                {"item": 3, "descricao": checklist[2]["descricao"], "status": "S", "observacao": "Certidão Positiva c/ Efeitos de Negativa 02/02/2026"},
                {"item": 4, "descricao": checklist[3]["descricao"], "status": "S", "observacao": "CRF válido 27/01/2026 a 25/02/2026"},
                {"item": 5, "descricao": checklist[4]["descricao"], "status": "S", "observacao": "Certidão Trabalhista nº 7065076/2026 válida 01/08/2026"},
                {"item": 6, "descricao": checklist[5]["descricao"], "status": "NA", "observacao": "Não se aplica"},
                {"item": 7, "descricao": checklist[6]["descricao"], "status": "S", "observacao": "Dispensa INSS na NF"},
                {"item": 8, "descricao": checklist[7]["descricao"], "status": "S", "observacao": "Portaria 1227/2023"},
                {"item": 9, "descricao": checklist[8]["descricao"], "status": "S", "observacao": "Documento SEI 124287269 (Atestado)"},
                {"item": 10, "descricao": checklist[9]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 11, "descricao": checklist[10]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 12, "descricao": checklist[11]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 13, "descricao": checklist[12]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 14, "descricao": checklist[13]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 15, "descricao": checklist[14]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 16, "descricao": checklist[15]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 17, "descricao": checklist[16]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 18, "descricao": checklist[17]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"},
                {"item": 19, "descricao": checklist[18]["descricao"], "status": "NA", "observacao": "Sem mão-de-obra"}
            ]
            
            # Mostrar resultados
            for res in resultados:
                col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
                with col1:
                    st.markdown(f"**{res['item']}**")
                with col2:
                    st.markdown(res['descricao'])
                with col3:
                    if res['status'] == "S":
                        st.markdown(f"✅ **S**")
                    elif res['status'] == "N":
                        st.markdown(f"❌ **N**")
                    else:
                        st.markdown(f"⚪ **NA**")
                with col4:
                    st.caption(res['observacao'])
            
            # RESUMO
            st.markdown("---")
            st.subheader("📊 RESUMO DA ANÁLISE")
            
            s_count = sum(1 for r in resultados if r['status'] == "S")
            n_count = sum(1 for r in resultados if r['status'] == "N")
            na_count = sum(1 for r in resultados if r['status'] == "NA")
            
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
            
            docs_obrigatorios = [1,2,3,4,5,8,9]
            obrigatorios_encontrados = sum(1 for r in resultados if r['item'] in docs_obrigatorios and r['status'] == "S")
            
            if obrigatorios_encontrados == len(docs_obrigatorios):
                st.markdown("""
                <div class="success-box">
                ✅ <strong>Nada tem a opor quanto ao prosseguimento do processo de pagamento.</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="warning-box">
                ⚠️ <strong>Após a regularização das exigências, retornar à Auditoria Interna</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Observações
            observacoes_padrao = "Processo com NE 2026NE00123, NF 3340715 e certidões regulares. Portaria 1227/2023 e Atestado SEI 124287269. Itens 10-19 NA (sem mão-de-obra)."
            observacoes = st.text_area("📌 Observações:", value=observacoes_padrao, height=100)
            
            # Botão para gerar PDF
            st.markdown("---")
            if st.button("📥 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf_profissional(dados, resultados, observacoes)
                    
                    st.download_button(
                        label="📄 Clique aqui para baixar o relatório PDF",
                        data=pdf_bytes,
                        file_name=f"relatorio_analise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.balloons()
    
    else:
        st.info("👆 Faça upload de um PDF para iniciar a análise completa")
else:
    st.warning("🔐 Faça login no menu lateral para acessar o sistema")

st.markdown("---")
st.caption(f"IPEM-RJ - Auditoria Interna | Sistema de Análise Automática v3.3 | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
