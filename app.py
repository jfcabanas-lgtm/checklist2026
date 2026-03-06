import streamlit as st
import PyPDF2
import re
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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
# FUNÇÕES DE EXTRAÇÃO GENÉRICAS
# ============================================

def extrair_dados_completos(texto):
    """Extrai informações de QUALQUER processo de pagamento"""
    dados = {}
    texto_lower = texto.lower()
    
    # 1. FORNECEDOR (busca genérica por padrões de nome de empresa)
    fornecedor_patterns = [
        r'(?:fornecedor|empresa|contratada|razao social)[:\s]*([A-Z][A-Z\s.,&]+(?:LTDA|Ltda|ME|EIRELI|SA|S/A))',
        r'(?:fornecedor|empresa|contratada)[:\s]*([A-Z][A-Z\s.,&]+)',
        r'([A-Z][A-Z\s.,&]+(?:LTDA|Ltda|ME|EIRELI|SA|S/A))'
    ]
    
    dados['fornecedor'] = "Não identificado"
    for pattern in fornecedor_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            dados['fornecedor'] = match.group(1).strip()
            break
    
    # 2. CNPJ (padrão universal)
    cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
    dados['cnpj'] = cnpj_match.group() if cnpj_match else "Não identificado"
    
    # 3. PROCESSO (padrão SEI)
    processo_match = re.search(r'SEI[-/\s]*(\d+[-/\s]*\d+[-/\s]*\d+)', texto, re.IGNORECASE)
    dados['processo'] = processo_match.group(1) if processo_match else "Não identificado"
    
    # 4. CONTRATO
    contrato_match = re.search(r'(?:contrato|processo)[:\s]*(\d+/\d{4})', texto, re.IGNORECASE)
    dados['contrato'] = contrato_match.group(1) if contrato_match else "Não identificado"
    
    # 5. VIGÊNCIA
    vigencia_match = re.search(r'vig[êe]ncia[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    dados['vigencia'] = vigencia_match.group(1) if vigencia_match else "Não identificado"
    
    # 6. OBJETO
    objeto_match = re.search(r'(?:objeto|descrição do serviço)[:\s]*([^\n]+)', texto, re.IGNORECASE)
    dados['objeto'] = objeto_match.group(1).strip() if objeto_match else "Não identificado"
    
    # 7. GESTORES (busca por nomes após "Gestor" e "Fiscal")
    gestores = []
    gestor_match = re.search(r'(?:gestor|fiscal)[:\s]*([A-Z][A-Z\s]+)', texto, re.IGNORECASE)
    if gestor_match:
        gestores.append(gestor_match.group(1).strip())
    
    fiscal_match = re.findall(r'(?:fiscal)[:\s]*([A-Z][A-Z\s]+)', texto, re.IGNORECASE)
    for fiscal in fiscal_match:
        if fiscal.strip() not in gestores:
            gestores.append(fiscal.strip())
    
    dados['gestores'] = ", ".join(gestores) if gestores else "Não identificado"
    
    # 8. NOTA FISCAL
    nf_match = re.search(r'(?:nota fiscal|nf)[:\s]*n[º°]?\s*(\d+)', texto, re.IGNORECASE)
    dados['nota_fiscal'] = nf_match.group(1) if nf_match else "Não identificado"
    
    # 9. SEI DA NOTA FISCAL (busca por números de 9 dígitos próximos à NF)
    if nf_match:
        contexto_nf = texto[max(0, nf_match.start()-200):nf_match.end()+200]
        sei_match = re.search(r'(\d{9})', contexto_nf)
        dados['sei_nf'] = sei_match.group(1) if sei_match else "Não identificado"
    else:
        dados['sei_nf'] = "Não identificado"
    
    # 10. DATA EMISSÃO NF
    data_nf_match = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
    dados['data_nf'] = data_nf_match.group(1) if data_nf_match else "Não identificado"
    
    # 11. VALOR
    valor_match = re.search(r'valor[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    dados['valor'] = valor_match.group(1) if valor_match else "0,00"
    
    # 12. NOTA DE EMPENHO
    ne_match = re.search(r'\d{4}NE\d{5}', texto)
    dados['ne'] = ne_match.group() if ne_match else "Não identificado"
    
    # 13. NOTA DE LIQUIDAÇÃO
    nl_match = re.search(r'\d{4}NL\d{5}', texto)
    dados['nl'] = nl_match.group() if nl_match else "Não identificado"
    
    # 14. DATA LIQUIDAÇÃO
    if nl_match:
        contexto_nl = texto[max(0, nl_match.start()-200):nl_match.end()+200]
        data_nl_match = re.search(r'(\d{2}/\d{2}/\d{4})', contexto_nl)
        dados['data_nl'] = data_nl_match.group(1) if data_nl_match else "Não identificado"
    else:
        dados['data_nl'] = "Não identificado"
    
    # 15. SEI DO ATESTADO (busca por números de 9 dígitos perto de "atestado")
    atestado_contexto = re.search(r'atestado.*?(\d{9})', texto, re.IGNORECASE | re.DOTALL)
    dados['sei_atestado'] = atestado_contexto.group(1) if atestado_contexto else "Não identificado"
    
    # 16. SEI DA LIQUIDAÇÃO (busca por números de 9 dígitos perto de "liquidação")
    liquidacao_contexto = re.search(r'liquidação.*?(\d{9})', texto, re.IGNORECASE | re.DOTALL)
    dados['sei_liquidacao'] = liquidacao_contexto.group(1) if liquidacao_contexto else "Não identificado"
    
    # ============================================
    # CERTIDÃO FEDERAL - ITEM 3
    # ============================================
    cert_federal_datas = re.findall(r'Valida\s*at[ée]\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    
    if cert_federal_datas:
        dados['cert_federal_validade'] = cert_federal_datas[-1]
    else:
        emissao_datas = re.findall(r'emitida[:\s]*.*?(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
        dados['cert_federal_validade'] = emissao_datas[-1] if emissao_datas else "Não identificado"
    
    # ============================================
    # CERTIDÃO FGTS - ITEM 4
    # ============================================
    cert_fgts_datas = re.findall(r'Validade[:\s]*(\d{2}/\d{2}/\d{4})[:\s]*a[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    
    if cert_fgts_datas:
        dados['cert_fgts_inicio'] = cert_fgts_datas[-1][0]
        dados['cert_fgts_fim'] = cert_fgts_datas[-1][1]
    else:
        dados['cert_fgts_inicio'] = "Não identificado"
        dados['cert_fgts_fim'] = "Não identificado"
    
    # ============================================
    # CERTIDÃO TRABALHISTA - ITEM 5
    # ============================================
    cert_trab_datas = re.findall(r'válida até[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    dados['cert_trab_validade'] = cert_trab_datas[-1] if cert_trab_datas else "Não identificado"
    
    # 19. DISPENSA RETENÇÃO (Item 7)
    dispensa_match = re.search(r'DISPENSA.*?RETENÇÃO.*?INSS', texto, re.IGNORECASE)
    dados['dispensa'] = "Dispensa INSS na NF" if dispensa_match else "Não identificado"
    
    # 20. PORTARIA (Item 8)
    portaria_match = re.search(r'(\d+/\d{4})', texto)
    dados['portaria'] = portaria_match.group(1) if portaria_match else "Não identificado"
    
    # 21. ATESTADO (Item 9) - já temos sei_atestado
    dados['atestado'] = f"SEI {dados['sei_atestado']}" if dados['sei_atestado'] != "Não identificado" else "Não identificado"
    
    # 22. Verificar mão-de-obra
    mao_obra_keywords = ['mao de obra', 'terceirizado', 'funcionario', 'empregado', 'posto de trabalho']
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
# FUNÇÃO PARA GERAR PDF EM DUAS PÁGINAS
# ============================================

def gerar_pdf_duas_paginas(dados, resultados, conclusao_texto, observacao_texto):
    """
    Gera um PDF com:
    - Página 1: Checklist completo (19 itens)
    - Página 2: Texto legal e conclusão (fonte aumentada)
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
        name='CabecalhoInstitucional',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=2,
        leading=14
    ))
    
    styles.add(ParagraphStyle(
        name='SubCabecalho',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica',
        spaceAfter=4,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='Titulo',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=4
    ))
    
    styles.add(ParagraphStyle(
        name='ProcessoNegrito',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=8,
        leading=13
    ))
    
    styles.add(ParagraphStyle(
        name='InfoLabel',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        leading=11
    ))
    
    styles.add(ParagraphStyle(
        name='InfoValue',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        leading=11
    ))
    
    styles.add(ParagraphStyle(
        name='TabelaConteudo',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        leading=10,
        wordWrap='CJK'
    ))
    
    # ========================================
    # ESTILOS DA PÁGINA 2 (FONTE AUMENTADA)
    # ========================================
    
    styles.add(ParagraphStyle(
        name='TextoLegalPagina2',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        leading=13,
        leftIndent=10,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='TextoSemiNegritoPagina2',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        leading=13,
        leftIndent=10,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='TituloSecaoPagina2',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        leading=14,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='Rodape',
        parent=styles['Normal'],
        fontSize=6,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        leading=8
    ))
    
    # ========================================
    # PÁGINA 1 - CABEÇALHO E CHECKLIST
    # ========================================
    
    # Cabeçalho institucional
    cabecalho1 = Paragraph("INSTITUTO DE PESOS E MEDIDAS IPEM/RJ", styles['CabecalhoInstitucional'])
    elements.append(cabecalho1)
    
    cabecalho2 = Paragraph("AUDITORIA INTERNA - AUDIT", styles['SubCabecalho'])
    elements.append(cabecalho2)
    elements.append(Spacer(1, 0.1*cm))
    
    # Título
    titulo = Paragraph("CHECKLIST DA DOCUMENTAÇÃO APRESENTADA DE PROCESSO DE DESPESA REGULAR", styles['Titulo'])
    elements.append(titulo)
    
    # Número do processo
    processo_negrito = Paragraph(f"<b>{dados['processo']}</b>", styles['ProcessoNegrito'])
    elements.append(processo_negrito)
    elements.append(Spacer(1, 0.3*cm))
    
    # Dados do processo em formato mais compacto
    dados_compactos = [
        [Paragraph(f"<b>Fornecedor:</b> {dados['fornecedor'][:50]}", styles['InfoValue']),
         Paragraph(f"<b>CNPJ:</b> {dados['cnpj']}", styles['InfoValue'])],
        
        [Paragraph(f"<b>Contrato:</b> {dados['contrato']} | <b>Vigência:</b> {dados['vigencia']}", styles['InfoValue']),
         Paragraph(f"<b>NF:</b> {dados['nota_fiscal']} (SEI {dados['sei_nf']})", styles['InfoValue'])],
        
        [Paragraph(f"<b>Valor:</b> R$ {dados['valor']} | <b>Gestor:</b> {dados['gestores'][:30]}", styles['InfoValue']),
         Paragraph("", styles['InfoValue'])]
    ]
    
    dados_table = Table(dados_compactos, colWidths=[10*cm, 8*cm])
    dados_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(dados_table)
    elements.append(Spacer(1, 0.4*cm))
    
    # CHECKLIST COMPLETO (19 itens)
    checklist_data = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados:
        descricao = res['descricao']
        if len(descricao) > 65:
            descricao = descricao[:62] + "..."
        
        checklist_data.append([
            str(res['item']),
            descricao,
            res['status'],
            res['observacao']
        ])
    
    checklist_table = Table(checklist_data, colWidths=[0.8*cm, 8.5*cm, 1.2*cm, 4.0*cm], repeatRows=1)
    
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f9e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
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
    elements.append(Spacer(1, 0.2*cm))
    
    # Legenda
    elements.append(Paragraph("S = Sim • N = Não • NA = Não Aplicável", 
                             ParagraphStyle('Legenda', fontSize=7, textColor=colors.HexColor('#666666'))))
    
    # ========================================
    # QUEBRA DE PÁGINA
    # ========================================
    elements.append(PageBreak())
    
    # ========================================
    # PÁGINA 2 - TEXTO LEGAL E CONCLUSÃO
    # ========================================
    
    # Texto legal completo
    elements.append(Paragraph("Segue checklist, com o objetivo de conferência da documentação apresentada e continuidade do processo. A despesa está devidamente atestada pelo gestor e fiscais da área solicitante, conforme o SEI", styles['TextoLegalPagina2']))
    elements.append(Paragraph(f"<b>{dados['sei_atestado']}</b>.", styles['TextoSemiNegritoPagina2']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("A conformidade da despesa, nota fiscal e a documentação anexa encontram-se regulares, conforme certificação da divisão de contabilidade SEI", styles['TextoLegalPagina2']))
    elements.append(Paragraph(f"<b>{dados['sei_liquidacao']}</b>.", styles['TextoSemiNegritoPagina2']))
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph("1 - Cumpre destacar que esta checagem NÃO tem o papel de adentrar a seara do cumprimento das obrigações da contratada, no que tange às obrigações trabalhistas, previdenciárias e tributárias, inclusive pagamento das verbas salariais, vale transporte e auxílio alimentação, assim como a averiguação das Certidões de Regularidade (CRF, CND e CNDT), visto que são atribuições relacionadas aos Fiscais do Contrato conforme Decreto nº 45.600, de 16 de março de 2016.", styles['TextoLegalPagina2']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("2 – Conforme manifestação do Tribunal de Contas da União em seu Informativo 103/2012, “A perda da regularidade fiscal no curso de contratos de execução continuada ou parcela justifica a imposição de sanções à contratada, mas não autoriza a retenção de pagamento por serviços prestados”. (Acórdão nº 964/2012-Plenário, TC 017.371/2011-2, rel. Min Walton Alencar Rodrigues, 25.4.2012).", styles['TextoLegalPagina2']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("Face à análise, a despesa encontra-se em condições de prosseguimento, estando em conformidade quanto à correta classificação orçamentária, ao enquadramento legal e à formalização processual.", styles['TextoLegalPagina2']))
    elements.append(Spacer(1, 0.3*cm))
    
    # CONCLUSÃO
    elements.append(Paragraph("CONCLUSÃO:", styles['TituloSecaoPagina2']))
    elements.append(Paragraph(conclusao_texto, styles['TextoLegalPagina2']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Observações adicionais
    if observacao_texto:
        elements.append(Paragraph("OBSERVAÇÕES:", styles['TituloSecaoPagina2']))
        elements.append(Paragraph(observacao_texto, styles['TextoLegalPagina2']))
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph("At.te", styles['TextoLegalPagina2']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Espaço para assinatura
    elements.append(Spacer(1, 1*cm))
    
    # Rodapé
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    elements.append(Paragraph(f"Documento gerado automaticamente pelo Sistema de Análise de Processos - IPEM/RJ em {data_atual}", 
                             styles['Rodape']))
    
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
            if dados['cert_federal_validade'] != "Não identificado":
                federal_valida, federal_data = verificar_validade(dados['cert_federal_validade'])
                if federal_valida and federal_data < data_atual:
                    cert_federal_obs = f"❌ VENCIDA {dados['cert_federal_validade']}"
                else:
                    cert_federal_obs = f"Válida {dados['cert_federal_validade']}"
            else:
                cert_federal_obs = "Não identificado"
            
            # Certidão FGTS (Item 4)
            if dados['cert_fgts_fim'] != "Não identificado":
                fgts_valida, fgts_data = verificar_validade(dados['cert_fgts_fim'])
                if fgts_valida and fgts_data < data_atual:
                    cert_fgts_obs = f"❌ VENCIDO {dados['cert_fgts_fim']}"
                else:
                    cert_fgts_obs = f"{dados['cert_fgts_inicio']} a {dados['cert_fgts_fim']}"
            else:
                cert_fgts_obs = "Não identificado"
            
            # Certidão Trabalhista (Item 5)
            if dados['cert_trab_validade'] != "Não identificado":
                trab_valida, trab_data = verificar_validade(dados['cert_trab_validade'])
                if trab_valida and trab_data < data_atual:
                    cert_trab_obs = f"❌ VENCIDA {dados['cert_trab_validade']}"
                else:
                    cert_trab_obs = f"Válida {dados['cert_trab_validade']}"
            else:
                cert_trab_obs = "Não identificado"
            
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
            
            # Resultados com observações
            resultados = [
                {"item": 1, "descricao": checklist[0]["descricao"], "status": "S" if dados['ne'] != "Não identificado" else "N", "observacao": f"{dados['ne']} → {dados['nl']}" if dados['ne'] != "Não identificado" else "Não localizado"},
                {"item": 2, "descricao": checklist[1]["descricao"], "status": "S" if dados['sei_nf'] != "Não identificado" else "N", "observacao": f"SEI {dados['sei_nf']}" if dados['sei_nf'] != "Não identificado" else "Não localizado"},
                {"item": 3, "descricao": checklist[2]["descricao"], "status": "S" if dados['cert_federal_validade'] != "Não identificado" else "N", "observacao": cert_federal_obs},
                {"item": 4, "descricao": checklist[3]["descricao"], "status": "S" if dados['cert_fgts_fim'] != "Não identificado" else "N", "observacao": cert_fgts_obs},
                {"item": 5, "descricao": checklist[4]["descricao"], "status": "S" if dados['cert_trab_validade'] != "Não identificado" else "N", "observacao": cert_trab_obs},
                {"item": 6, "descricao": checklist[5]["descricao"], "status": "NA", "observacao": "N/A"},
                {"item": 7, "descricao": checklist[6]["descricao"], "status": "S" if dados['dispensa'] != "Não identificado" else "NA", "observacao": dados['dispensa']},
                {"item": 8, "descricao": checklist[7]["descricao"], "status": "S" if dados['portaria'] != "Não identificado" else "N", "observacao": f"Portaria {dados['portaria']}" if dados['portaria'] != "Não identificado" else "Não localizado"},
                {"item": 9, "descricao": checklist[8]["descricao"], "status": "S" if dados['sei_atestado'] != "Não identificado" else "N", "observacao": dados['atestado']},
                {"item": 10, "descricao": checklist[9]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 11, "descricao": checklist[10]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 12, "descricao": checklist[11]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 13, "descricao": checklist[12]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 14, "descricao": checklist[13]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 15, "descricao": checklist[14]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 16, "descricao": checklist[15]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 17, "descricao": checklist[16]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 18, "descricao": checklist[17]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"},
                {"item": 19, "descricao": checklist[18]["descricao"], "status": "NA" if not dados['tem_mao_obra'] else "N", "observacao": "Sem mão-obra" if not dados['tem_mao_obra'] else "Não localizado"}
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
            
            # PERGUNTAS PARA O RELATÓRIO
            st.markdown("---")
            st.subheader("📝 INFORMAÇÕES PARA O RELATÓRIO")
            
            tem_exigencia = st.radio("📌 Existe alguma exigência a fazer?", ["Não", "Sim"], horizontal=True)
            
            if tem_exigencia == "Sim":
                exigencia_texto = st.text_area("✏️ Descreva a(s) exigência(s):", height=100)
                conclusao = exigencia_texto
            else:
                conclusao = f"Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320, de 17/03/1964 e com a análise procedida da Nota Fiscal e documentação apresentada pela empresa sendo atestada e certificada sua regularidade através da liquidação de despesa pela Divisão de Contabilidade Documento SEI {dados['sei_liquidacao'] if dados['sei_liquidacao'] != 'Não identificado' else '________'}"
            
            tem_observacao = st.radio("📝 Existe alguma observação a fazer?", ["Não", "Sim"], horizontal=True)
            observacao_texto = st.text_area("✏️ Descreva a(s) observação(ões):", height=100) if tem_observacao == "Sim" else ""
            
            # Botão para gerar PDF
            st.markdown("---")
            if st.button("📥 GERAR RELATÓRIO PDF (2 PÁGINAS)", type="primary", use_container_width=True):
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf_duas_paginas(dados, resultados, conclusao, observacao_texto)
                    
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
st.caption(f"IPEM-RJ - Auditoria Interna | Sistema de Análise Automática v9.0 - Genérico | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
