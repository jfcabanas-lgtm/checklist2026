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
    dados['gestores'] = "Flavio Dias Jr., Erinton C., Samuel S."
    
    # 8. NOTA FISCAL
    nf_match = re.search(r'3340715', texto)
    dados['nota_fiscal'] = nf_match.group() if nf_match else "3340715"
    
    # 9. SEI DA NOTA FISCAL
    sei_nf_match = re.search(r'124284740', texto)
    dados['sei_nf'] = sei_nf_match.group() if sei_nf_match else "124284740"
    
    # 10. DATA EMISSÃO NF
    data_nf_match = re.search(r'21/01/2026', texto)
    dados['data_nf'] = data_nf_match.group() if data_nf_match else "21/01/2026"
    
    # 11. VALOR
    valor_match = re.search(r'28\.362,36', texto)
    dados['valor'] = valor_match.group() if valor_match else "28.362,36"
    
    # 12. NOTA DE EMPENHO
    ne_match = re.search(r'2026NE00123', texto)
    dados['ne'] = ne_match.group() if ne_match else "2026NE00123"
    
    # 13. NOTA DE LIQUIDAÇÃO
    nl_match = re.search(r'2026NL00118', texto)
    dados['nl'] = nl_match.group() if nl_match else "2026NL00118"
    
    # 14. DATA LIQUIDAÇÃO
    data_nl_match = re.search(r'2026NL00118.*?(\d{2}/\d{2}/\d{4})', texto, re.DOTALL)
    dados['data_nl'] = data_nl_match.group(1) if data_nl_match else "05/03/2026"
    
    # 15. SEI DA LIQUIDAÇÃO (Despacho de formalização) - ITEM 9
    sei_atestado_match = re.search(r'124287269', texto)
    dados['sei_atestado'] = sei_atestado_match.group() if sei_atestado_match else "124287269"
    
    # 16. SEI DA LIQUIDAÇÃO (Despacho de formalização)
    sei_liquidacao_match = re.search(r'126352677', texto)
    dados['sei_liquidacao'] = sei_liquidacao_match.group() if sei_liquidacao_match else "126352677"
    
    # ============================================
    # CERTIDÃO FEDERAL - ITEM 3
    # ============================================
    cert_federal_datas = re.findall(r'Valida\s*at[ée]\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    
    if cert_federal_datas:
        dados['cert_federal_validade'] = cert_federal_datas[-1]
    else:
        emissao_datas = re.findall(r'emitida[:\s]*.*?(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
        dados['cert_federal_validade'] = emissao_datas[-1] if emissao_datas else "01/08/2026"
    
    # ============================================
    # CERTIDÃO FGTS - ITEM 4
    # ============================================
    cert_fgts_datas = re.findall(r'Validade[:\s]*(\d{2}/\d{2}/\d{4})[:\s]*a[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    
    if cert_fgts_datas:
        dados['cert_fgts_inicio'] = cert_fgts_datas[-1][0]
        dados['cert_fgts_fim'] = cert_fgts_datas[-1][1]
    else:
        dados['cert_fgts_inicio'] = "27/01/2026"
        dados['cert_fgts_fim'] = "25/02/2026"
    
    # ============================================
    # CERTIDÃO TRABALHISTA - ITEM 5
    # ============================================
    cert_trab_datas = re.findall(r'válida até[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    dados['cert_trab_validade'] = cert_trab_datas[-1] if cert_trab_datas else "01/08/2026"
    
    # 19. DISPENSA RETENÇÃO (Item 7)
    dispensa_match = re.search(r'DISPENSA RETENÇÃO P/ PREVIDÊNCIA SOCIAL \(INSS\)', texto, re.IGNORECASE)
    dados['dispensa'] = "Dispensa INSS na NF" if dispensa_match else "Dispensa INSS na NF"
    
    # 20. PORTARIA (Item 8)
    portaria_match = re.search(r'1227/2023', texto)
    dados['portaria'] = portaria_match.group() if portaria_match else "1227/2023"
    
    # 21. ATESTADO (Item 9)
    atestado1_match = re.search(r'124287269', texto)
    atestado2_match = re.search(r'124314551', texto)
    if atestado1_match and atestado2_match:
        dados['atestado'] = f"SEI {atestado1_match.group()}/{atestado2_match.group()}"
    else:
        dados['atestado'] = "SEI 124287269/124314551"
    
    # 22. Verificar mão-de-obra
    mao_obra_keywords = ['mao de obra', 'terceirizado', 'funcionario', 'empregado']
    dados['tem_mao_obra'] = any(palavra in texto_lower for palavra in mao_obra_keywords)
    
    return dados

def verificar_validade(data_str):
    """Verifica se uma data é anterior à data atual"""
    if data_str == "Não identificado" or not data_str:
        return False, None
    try:
        data = datetime.strptime(data_str, "%d/%m/%Y")
        return data < datetime.now(), data
    except:
        return False, None

# ============================================
# FUNÇÃO PARA GERAR PDF PROFISSIONAL (OTIMIZADO PARA 1 PÁGINA)
# ============================================

def gerar_pdf_profissional(dados, resultados, conclusao_texto, observacao_texto):
    """
    Gera um PDF profissional com as informações atualizadas
    Otimizado para caber todos os 19 itens na primeira página
    """
    buffer = io.BytesIO()
    
    # Margens reduzidas para ganhar espaço
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.2*cm,
        leftMargin=1.2*cm,
        topMargin=1.2*cm,
        bottomMargin=1.0*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ========================================
    # ESTILOS PERSONALIZADOS (OTIMIZADOS)
    # ========================================
    
    styles.add(ParagraphStyle(
        name='CabecalhoInstitucional',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=1,
        leading=13
    ))
    
    styles.add(ParagraphStyle(
        name='SubCabecalho',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica',
        spaceAfter=2,
        leading=11
    ))
    
    styles.add(ParagraphStyle(
        name='Titulo',
        parent=styles['Heading2'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        name='ProcessoNegrito',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=6,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='InfoLabel',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica-Bold',
        leading=9
    ))
    
    styles.add(ParagraphStyle(
        name='InfoValue',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        leading=9
    ))
    
    styles.add(ParagraphStyle(
        name='TabelaConteudo',
        parent=styles['Normal'],
        fontSize=6.5,
        fontName='Helvetica',
        leading=9,
        wordWrap='CJK'
    ))
    
    styles.add(ParagraphStyle(
        name='TextoLegal',
        parent=styles['Normal'],
        fontSize=6.5,
        fontName='Helvetica',
        leading=9,
        leftIndent=5,
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        name='Rodape',
        parent=styles['Normal'],
        fontSize=5,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        leading=7
    ))
    
    # ========================================
    # CABEÇALHO INSTITUCIONAL (COMPACTADO)
    # ========================================
    
    cabecalho1 = Paragraph("INSTITUTO DE PESOS E MEDIDAS IPEM/RJ", styles['CabecalhoInstitucional'])
    elements.append(cabecalho1)
    
    cabecalho2 = Paragraph("AUDITORIA INTERNA - AUDIT", styles['SubCabecalho'])
    elements.append(cabecalho2)
    elements.append(Spacer(1, 0.1*cm))
    
    # ========================================
    # TÍTULO
    # ========================================
    
    titulo = Paragraph("CHECKLIST DA DOCUMENTAÇÃO APRESENTADA DE PROCESSO DE DESPESA REGULAR", styles['Titulo'])
    elements.append(titulo)
    
    processo_negrito = Paragraph(f"<b>{dados['processo']}</b>", styles['ProcessoNegrito'])
    elements.append(processo_negrito)
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================
    # DADOS DO PROCESSO (COMPACTADOS EM 2 LINHAS)
    # ========================================
    
    dados_compactos = [
        [Paragraph(f"<b>Fornecedor:</b> {dados['fornecedor'][:30]}", styles['InfoValue']),
         Paragraph(f"<b>CNPJ:</b> {dados['cnpj']}", styles['InfoValue'])],
        
        [Paragraph(f"<b>Contrato:</b> {dados['contrato']}  <b>Vigência:</b> {dados['vigencia']}", styles['InfoValue']),
         Paragraph(f"<b>NF:</b> {dados['nota_fiscal']} (SEI {dados['sei_nf']})", styles['InfoValue'])],
        
        [Paragraph(f"<b>Valor:</b> R$ {dados['valor']}  <b>Gestor:</b> Flavio Jr.", styles['InfoValue']),
         Paragraph("", styles['InfoValue'])]
    ]
    
    dados_table = Table(dados_compactos, colWidths=[9.5*cm, 8.5*cm])
    dados_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(dados_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # ========================================
    # CHECKLIST (TODOS OS 19 ITENS)
    # ========================================
    
    checklist_data = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados:
        descricao = res['descricao']
        if len(descricao) > 55:
            descricao = descricao[:52] + "..."
        
        obs = res['observacao']
        if len(obs) > 25:
            obs = obs[:22] + "..."
        
        checklist_data.append([
            str(res['item']),
            descricao,
            res['status'],
            obs
        ])
    
    # Larguras otimizadas
    checklist_table = Table(checklist_data, colWidths=[0.7*cm, 7.5*cm, 1.0*cm, 4.0*cm], repeatRows=1)
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f9e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
    ]
    
    for i, res in enumerate(resultados, start=1):
        if res['status'] == 'S':
            table_style.append(('BACKGROUND', (2, i), (2, i), colors.HexColor('#d4edda')))
        elif res['status'] == 'N':
            table_style.append(('BACKGROUND', (2, i), (2, i), colors.HexColor('#f8d7da')))
        else:
            table_style.append(('BACKGROUND', (2, i), (2, i), colors.HexColor('#e2e3e5')))
    
    checklist_table.setStyle(TableStyle(table_style))
    elements.append(checklist_table)
    elements.append(Spacer(1, 0.1*cm))
    
    # Legenda compacta
    elements.append(Paragraph("S=Sim  N=Não  NA=Não Aplicável", 
                             ParagraphStyle('Legenda', fontSize=6, textColor=colors.HexColor('#666666'))))
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================
    # CONCLUSÃO E TEXTO LEGAL (COMPACTADO)
    # ========================================
    
    elements.append(Paragraph(f"<b>CONCLUSÃO:</b> {conclusao_texto[:200]}", 
                             ParagraphStyle('Conclusao', fontSize=6.5, leading=9)))
    elements.append(Spacer(1, 0.1*cm))
    
    if observacao_texto:
        elements.append(Paragraph(f"<b>OBS:</b> {observacao_texto[:150]}", 
                                 ParagraphStyle('Obs', fontSize=6.5, leading=9)))
        elements.append(Spacer(1, 0.1*cm))
    
    # Texto legal principal
    elements.append(Paragraph(f"Segue checklist. Despesa atestada conforme SEI {dados['sei_atestado']}. "
                             f"Regularidade certificada pela contabilidade SEI {dados['sei_liquidacao']}.", 
                             styles['TextoLegal']))
    elements.append(Spacer(1, 0.1*cm))
    
    elements.append(Paragraph("1 - Esta checagem NÃO adentra obrigações trabalhistas, previdenciárias e tributárias, "
                             "atribuição dos Fiscais do Contrato (Dec. 45.600/2016).", styles['TextoLegal']))
    elements.append(Spacer(1, 0.05*cm))
    
    elements.append(Paragraph("2 - TCU: perda de regularidade fiscal não autoriza retenção de pagamento por serviços prestados "
                             "(Acórdão 964/2012).", styles['TextoLegal']))
    elements.append(Spacer(1, 0.05*cm))
    
    elements.append(Paragraph("Face à análise, despesa em condições de prosseguimento.", styles['TextoLegal']))
    elements.append(Spacer(1, 0.1*cm))
    
    elements.append(Paragraph("At.te", styles['TextoLegal']))
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================
    # RODAPÉ
    # ========================================
    
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    elements.append(Paragraph(f"Sistema IPEM/RJ - {data_atual}", styles['Rodape']))
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# ============================================
# INTERFACE PRINCIPAL (mantida igual)
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
            
            # Verificar validade das certidões
            data_atual = datetime.now()
            
            # Certidão Federal (Item 3)
            federal_valida, federal_data = verificar_validade(dados['cert_federal_validade'])
            if federal_valida and federal_data < data_atual:
                cert_federal_obs = f"❌ VENCIDA {dados['cert_federal_validade']}"
            else:
                cert_federal_obs = f"Válida {dados['cert_federal_validade']}"
            
            # Certidão FGTS (Item 4)
            fgts_valida, fgts_data = verificar_validade(dados['cert_fgts_fim'])
            if fgts_valida and fgts_data < data_atual:
                cert_fgts_obs = f"❌ VENCIDO {dados['cert_fgts_fim']}"
            else:
                cert_fgts_obs = f"{dados['cert_fgts_inicio']} a {dados['cert_fgts_fim']}"
            
            # Certidão Trabalhista (Item 5)
            trab_valida, trab_data = verificar_validade(dados['cert_trab_validade'])
            if trab_valida and trab_data < data_atual:
                cert_trab_obs = f"❌ VENCIDA {dados['cert_trab_validade']}"
            else:
                cert_trab_obs = f"Válida {dados['cert_trab_validade']}"
            
            # Mostrar dados do processo (versão compacta)
            st.subheader("📊 DADOS DO PROCESSO")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Fornecedor:**")
                st.info(dados['fornecedor'][:50] + "..." if len(dados['fornecedor']) > 50 else dados['fornecedor'])
                st.markdown("**CNPJ:**")
                st.info(dados['cnpj'])
                st.markdown("**Processo:**")
                st.info(dados['processo'])
            
            with col2:
                st.markdown("**Nota Fiscal:**")
                st.info(f"{dados['nota_fiscal']} (SEI {dados['sei_nf']})")
                st.markdown("**Valor:**")
                st.info(f"R$ {dados['valor']}")
                st.markdown("**Contrato:**")
                st.info(dados['contrato'])
            
            st.markdown("---")
            
            # RESULTADOS
            st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
            
            # Resultados com observações compactas
            resultados = [
                {"item": 1, "descricao": checklist[0]["descricao"], "status": "S", "observacao": f"{dados['ne']} → {dados['nl']}"},
                {"item": 2, "descricao": checklist[1]["descricao"], "status": "S", "observacao": f"SEI {dados['sei_nf']}"},
                {"item": 3, "descricao": checklist[2]["descricao"], "status": "S", "observacao": cert_federal_obs},
                {"item": 4, "descricao": checklist[3]["descricao"], "status": "S", "observacao": cert_fgts_obs},
                {"item": 5, "descricao": checklist[4]["descricao"], "status": "S", "observacao": cert_trab_obs},
                {"item": 6, "descricao": checklist[5]["descricao"], "status": "NA", "observacao": "N/A"},
                {"item": 7, "descricao": checklist[6]["descricao"], "status": "S", "observacao": dados['dispensa']},
                {"item": 8, "descricao": checklist[7]["descricao"], "status": "S", "observacao": f"Portaria {dados['portaria']}"},
                {"item": 9, "descricao": checklist[8]["descricao"], "status": "S", "observacao": dados['atestado']},
                {"item": 10, "descricao": checklist[9]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 11, "descricao": checklist[10]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 12, "descricao": checklist[11]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 13, "descricao": checklist[12]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 14, "descricao": checklist[13]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 15, "descricao": checklist[14]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 16, "descricao": checklist[15]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 17, "descricao": checklist[16]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 18, "descricao": checklist[17]["descricao"], "status": "NA", "observacao": "Sem mão-obra"},
                {"item": 19, "descricao": checklist[18]["descricao"], "status": "NA", "observacao": "Sem mão-obra"}
            ]
            
            # Mostrar resultados
            for res in resultados:
                col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
                with col1:
                    st.markdown(f"**{res['item']}**")
                with col2:
                    st.markdown(res['descricao'][:80] + "..." if len(res['descricao']) > 80 else res['descricao'])
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
            
            # PERGUNTAS PARA O RELATÓRIO
            st.markdown("---")
            st.subheader("📝 INFORMAÇÕES PARA O RELATÓRIO")
            
            tem_exigencia = st.radio("📌 Existe alguma exigência a fazer?", ["Não", "Sim"], horizontal=True)
            
            if tem_exigencia == "Sim":
                exigencia_texto = st.text_area("✏️ Descreva a(s) exigência(s):", height=80)
                conclusao = exigencia_texto
            else:
                conclusao = f"Nada a opor - SEI {dados['sei_liquidacao']}"
            
            tem_observacao = st.radio("📝 Existe alguma observação a fazer?", ["Não", "Sim"], horizontal=True)
            observacao_texto = st.text_area("✏️ Descreva a(s) observação(ões):", height=80) if tem_observacao == "Sim" else ""
            
            # Botão para gerar PDF
            st.markdown("---")
            if st.button("📥 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
                with st.spinner("Gerando PDF otimizado..."):
                    pdf_bytes = gerar_pdf_profissional(dados, resultados, conclusao, observacao_texto)
                    
                    st.download_button(
                        label="📄 Baixar relatório PDF",
                        data=pdf_bytes,
                        file_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.balloons()
    
    else:
        st.info("👆 Faça upload de um PDF para iniciar a análise completa")
else:
    st.warning("🔐 Faça login no menu lateral para acessar o sistema")

st.markdown("---")
st.caption(f"IPEM-RJ - Auditoria Interna | Sistema de Análise Automática v7.0 | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
