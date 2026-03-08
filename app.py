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
    .sei-mapper {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin-bottom: 1.5rem;
    }
    .sei-item {
        background-color: white;
        padding: 0.8rem;
        border-radius: 5px;
        border-left: 4px solid #1a5f9e;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>📋 ANÁLISE DE PROCESSO DE PAGAMENTO - IPEM/RJ</h1></div>', unsafe_allow_html=True)

# Checklist atualizado (18 itens)
checklist = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo (art. 63, §1°, II, da Lei 4320/64)", "tipo": "obrigatorio", "sei_key": "ne_nl"},
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM, de acordo com o empenho e com o objeto", "tipo": "obrigatorio", "sei_key": "nota_fiscal"},
    {"item": 3, "descricao": "Certidão de regularidade relativo aos tributos federais e dívida ativa da União", "tipo": "obrigatorio", "sei_key": None},
    {"item": 4, "descricao": "Certidão de regularidade junto ao FGTS", "tipo": "obrigatorio", "sei_key": None},
    {"item": 5, "descricao": "Certidão de regularidade junto a Justiça do Trabalho", "tipo": "obrigatorio", "sei_key": None},
    {"item": 6, "descricao": "No caso de incidir tributos a serem retidos da fonte, consta indicação?", "tipo": "condicional", "sei_key": None},
    {"item": 7, "descricao": "Quando não incidir tributos, há documento de comprovação da não incidência?", "tipo": "condicional", "sei_key": None},
    {"item": 8, "descricao": "Portaria de Nomeação de Fiscalização", "tipo": "obrigatorio", "sei_key": "portaria"},
    {"item": 9, "descricao": "Atestado do Gestor do contrato de que os serviços ou aquisições contratados foram prestados a contento", "tipo": "obrigatorio", "sei_key": "atestado"},
    {"item": 10, "descricao": "Relação dos funcionários que executaram o serviço", "tipo": "mao_obra", "sei_key": "relacao_funcionarios"},
    {"item": 11, "descricao": "FGTS Digital", "tipo": "mao_obra", "sei_key": "fgts_digital"},
    {"item": 12, "descricao": "Comprovante de pagamento do INSS", "tipo": "mao_obra", "sei_key": "inss"},
    {"item": 13, "descricao": "Comprovante de pagamento do FGTS", "tipo": "mao_obra", "sei_key": "fgts"},
    {"item": 14, "descricao": "Folha de pagamento", "tipo": "mao_obra", "sei_key": "folha_pagamento"},
    {"item": 15, "descricao": "Comprovante de pagamento dos salários", "tipo": "mao_obra", "sei_key": "comprovante_salarios"},
    {"item": 16, "descricao": "Comprovante de pagamento do Vale transporte", "tipo": "mao_obra", "sei_key": "vale_transporte"},
    {"item": 17, "descricao": "Comprovante de pagamento do Vale alimentação / refeição", "tipo": "mao_obra", "sei_key": "vale_alimentacao"},
    {"item": 18, "descricao": "Comprovante de pagamento de rescisão e FGTS", "tipo": "mao_obra", "sei_key": "rescisao"}
]

# ============================================
# FUNÇÕES DE EXTRAÇÃO DE TEXTO
# ============================================

def extrair_texto_pdf(pdf_file):
    """Extrai texto de qualquer PDF"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    texto = ""
    for page in pdf_reader.pages:
        texto += page.extract_text() or ""
    return texto

def extrair_fornecedor(texto):
    """Extrai nome do fornecedor de forma genérica"""
    padroes = [
        r'(?:fornecedor|empresa|contratada|razao social)[:\s]*([A-Z][A-Z\s.,&]+(?:LTDA|Ltda|ME|EIRELI|SA|S/A))',
        r'(?:fornecedor|empresa|contratada)[:\s]*([A-Z][A-Z\s.,&]+)',
        r'([A-Z][A-Z\s.,&]+(?:LTDA|Ltda|ME|EIRELI|SA|S/A))'
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Não identificado"

def extrair_cnpj(texto):
    """Extrai CNPJ no formato XX.XXX.XXX/XXXX-XX"""
    match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
    return match.group() if match else "Não identificado"

def extrair_processo(texto):
    """Extrai número do processo SEI"""
    match = re.search(r'SEI[-/\s]*(\d+[-/\s]*\d+[-/\s]*\d+)', texto, re.IGNORECASE)
    return match.group(1) if match else "Não identificado"

def extrair_contrato(texto):
    """Extrai número do contrato"""
    match = re.search(r'(?:contrato|processo)[:\s]*(\d+/\d{4})', texto, re.IGNORECASE)
    return match.group(1) if match else "Não identificado"

def extrair_vigencia(texto):
    """Extrai data de vigência"""
    vigencia = re.search(r'(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    if vigencia:
        return f"{vigencia.group(1)} a {vigencia.group(2)}"
    
    match = re.search(r'vig[êe]ncia[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return "Não identificado"

def extrair_objeto(texto):
    """Extrai objeto do contrato"""
    match = re.search(r'(?:objeto|descrição do serviço)[:\s]*([^\n]+)', texto, re.IGNORECASE)
    return match.group(1).strip() if match else "Não identificado"

def extrair_gestores(texto):
    """Extrai nomes dos gestores e fiscais"""
    gestores = []
    
    gestor = re.search(r'(?:gestor)[:\s]*([A-Z][A-Z\s]+)', texto, re.IGNORECASE)
    if gestor:
        gestores.append(f"Gestor: {gestor.group(1).strip()}")
    
    fiscais = re.findall(r'(?:fiscal)[:\s]*([A-Z][A-Z\s]+)', texto, re.IGNORECASE)
    for fiscal in fiscais:
        if fiscal.strip() not in str(gestores):
            gestores.append(f"Fiscal: {fiscal.strip()}")
    
    return ", ".join(gestores) if gestores else "Não identificado"

def extrair_nota_fiscal(texto):
    """Extrai número da nota fiscal"""
    match = re.search(r'(?:nota fiscal|nf|nfs[ -]e)[:\s]*n[º°]?\s*(\d+)', texto, re.IGNORECASE)
    return match.group(1) if match else "Não identificado"

def extrair_data_emissao_nf(texto):
    """Extrai data de emissão da nota fiscal"""
    match = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
    return match.group(1) if match else "Não identificado"

def extrair_valor_bruto(texto):
    """Extrai valor bruto total"""
    padroes = [
        r'valor[:\s]*R?\$?\s*([\d.,]+)',
        r'total[:\s]*R?\$?\s*([\d.,]+)',
        r'R?\$?\s*([\d.,]+)'
    ]
    
    for padrao in padroes:
        matches = re.findall(padrao, texto, re.IGNORECASE)
        if matches:
            valores = []
            for val in matches:
                try:
                    val_clean = val.replace('.', '').replace(',', '.')
                    num = float(val_clean)
                    if num > 1000:
                        valores.append((num, val))
                except:
                    continue
            
            if valores:
                maior = max(valores, key=lambda x: x[0])
                return maior[1]
    
    return "0,00"

def extrair_valor_liquido(texto):
    """Extrai valor líquido"""
    padroes = [
        r'valor líquido[:\s]*R?\$?\s*([\d.,]+)',
        r'líquido[:\s]*R?\$?\s*([\d.,]+)',
        r'valor a pagar[:\s]*R?\$?\s*([\d.,]+)'
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return extrair_valor_bruto(texto)

def extrair_nota_empenho(texto):
    """Extrai número da nota de empenho"""
    match = re.search(r'\d{4}NE\d{5}', texto)
    return match.group() if match else "Não identificado"

def extrair_nota_liquidacao(texto):
    """Extrai número da nota de liquidação"""
    match = re.search(r'\d{4}NL\d{5}', texto)
    return match.group() if match else "Não identificado"

def extrair_data_liquidacao(texto, nl_numero):
    """Extrai data da liquidação"""
    if nl_numero != "Não identificado":
        contexto = re.search(f'{nl_numero}.*?(\\d{{2}}/\\d{{2}}/\\d{{4}})', texto, re.DOTALL)
        if contexto:
            return contexto.group(1)
    return "Não identificado"

def extrair_portaria(texto):
    """Extrai número da portaria"""
    match = re.search(r'(\d+/\d{4})', texto)
    return match.group(1) if match else "Não identificado"

def extrair_certidoes(texto):
    """Extrai informações das certidões"""
    certidoes = {}
    
    # Certidão Federal
    federal_datas = re.findall(r'Valida\s*at[ée]\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    certidoes['federal'] = federal_datas[-1] if federal_datas else "Não identificado"
    
    # Certidão FGTS
    fgts_datas = re.findall(r'Validade[:\s]*(\d{2}/\d{2}/\d{4})[:\s]*a[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    if fgts_datas:
        certidoes['fgts_inicio'] = fgts_datas[-1][0]
        certidoes['fgts_fim'] = fgts_datas[-1][1]
    else:
        certidoes['fgts_inicio'] = "Não identificado"
        certidoes['fgts_fim'] = "Não identificado"
    
    # Certidão Trabalhista
    trab_datas = re.findall(r'válida até[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    certidoes['trabalhista'] = trab_datas[-1] if trab_datas else "Não identificado"
    
    return certidoes

def extrair_retencoes(texto):
    """Extrai informações sobre retenções"""
    retencoes = {}
    
    inss_match = re.search(r'INSS.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['inss'] = inss_match.group(1) if inss_match else "0,00"
    
    irrf_match = re.search(r'IRRF.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['irrf'] = irrf_match.group(1) if irrf_match else "0,00"
    
    pis_match = re.search(r'PIS.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['pis'] = pis_match.group(1) if pis_match else "0,00"
    
    cofins_match = re.search(r'COFINS.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['cofins'] = cofins_match.group(1) if cofins_match else "0,00"
    
    csll_match = re.search(r'CSLL.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['csll'] = csll_match.group(1) if csll_match else "0,00"
    
    return retencoes

def extrair_todos_seis(texto):
    """
    Extrai TODOS os números SEI (8-9 dígitos) do documento
    Retorna uma lista simples, sem classificação
    """
    todos_seis = re.findall(r'\b(\d{8,9})\b', texto)
    return sorted(list(set(todos_seis)))  # Remove duplicatas e ordena

def verificar_mao_obra(texto):
    """Verifica se há indícios de mão-de-obra"""
    palavras = ['mao de obra', 'terceirizado', 'funcionario', 'empregado', 'posto de trabalho',
                'folha de pagamento', 'salário', 'vale transporte', 'cesta básica', 'recibo de pagamento',
                'vigilante', 'auxiliar', 'copeiro', 'recepcionista']
    return any(palavra in texto.lower() for palavra in palavras)

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
# FUNÇÃO PARA GERAR PDF
# ============================================

def gerar_pdf_final(dados, certidoes, retencoes, mapeamento_seis, resultados, conclusao_texto, observacao_texto):
    """
    Gera um PDF profissional com as informações do processo
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
        name='Cabecalho',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='SubCabecalho',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica',
        spaceAfter=4
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
        name='Processo',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=8
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
        leading=11,
        wordWrap='CJK'
    ))
    
    styles.add(ParagraphStyle(
        name='TabelaItem',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        leading=10,
        wordWrap='CJK'
    ))
    
    styles.add(ParagraphStyle(
        name='TabelaObs',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        leading=10,
        wordWrap='CJK'
    ))
    
    styles.add(ParagraphStyle(
        name='TextoLegal',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        leading=12,
        leftIndent=10,
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
    # PÁGINA 1
    # ========================================
    
    # Cabeçalho
    elements.append(Paragraph("INSTITUTO DE PESOS E MEDIDAS IPEM/RJ", styles['Cabecalho']))
    elements.append(Paragraph("AUDITORIA INTERNA - AUDIT", styles['SubCabecalho']))
    elements.append(Spacer(1, 0.1*cm))
    
    # Título
    elements.append(Paragraph("CHECKLIST DA DOCUMENTAÇÃO APRESENTADA DE PROCESSO DE DESPESA REGULAR", styles['Titulo']))
    elements.append(Paragraph(f"<b>{dados['processo']}</b>", styles['Processo']))
    elements.append(Spacer(1, 0.2*cm))
    
    # Dados do processo
    info_processo = [
        [Paragraph(f"<b>Fornecedor:</b> {dados['fornecedor'][:60]}", styles['InfoValue']),
         Paragraph(f"<b>CNPJ:</b> {dados['cnpj']}", styles['InfoValue'])],
        [Paragraph(f"<b>Contrato:</b> {dados['contrato']} | <b>Vigência:</b> {dados['vigencia']}", styles['InfoValue']),
         Paragraph(f"<b>NF:</b> {dados['nota_fiscal']} de {dados['data_nf']}", styles['InfoValue'])],
        [Paragraph(f"<b>Valor Bruto:</b> R$ {dados['valor_bruto']}", styles['InfoValue']),
         Paragraph(f"<b>Valor Líquido:</b> R$ {dados['valor_liquido']}", styles['InfoValue'])],
        [Paragraph(f"<b>Gestor:</b> {dados['gestores'][:40]}", styles['InfoValue']),
         Paragraph("", styles['InfoValue'])]
    ]
    
    tabela_info = Table(info_processo, colWidths=[10*cm, 7.5*cm])
    tabela_info.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(tabela_info)
    elements.append(Spacer(1, 0.3*cm))
    
    # Checklist
    cabecalho_checklist = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados:
        cabecalho_checklist.append([
            Paragraph(str(res['item']), ParagraphStyle('Item', fontSize=7, alignment=TA_CENTER)),
            Paragraph(res['descricao'], styles['TabelaItem']),
            Paragraph(res['status'], ParagraphStyle('Status', fontSize=7, alignment=TA_CENTER)),
            Paragraph(res['observacao'], styles['TabelaObs'])
        ])
    
    tabela_checklist = Table(cabecalho_checklist, colWidths=[0.7*cm, 8.0*cm, 1.0*cm, 4.0*cm], repeatRows=1)
    
    estilo = [
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
    
    # Cores baseadas no status
    for i, res in enumerate(resultados, start=1):
        if res['status'] == 'S':
            estilo.append(('BACKGROUND', (2, i), (2, i), colors.HexColor('#d4edda')))
        elif res['status'] == 'N':
            estilo.append(('BACKGROUND', (2, i), (2, i), colors.HexColor('#f8d7da')))
        else:
            estilo.append(('BACKGROUND', (2, i), (2, i), colors.HexColor('#e2e3e5')))
    
    tabela_checklist.setStyle(TableStyle(estilo))
    elements.append(tabela_checklist)
    elements.append(Spacer(1, 0.2*cm))
    
    # Legenda
    elements.append(Paragraph("S = Sim • N = Não • NA = Não Aplicável", 
                             ParagraphStyle('Legenda', fontSize=6, textColor=colors.HexColor('#666666'))))
    
    # ========================================
    # QUEBRA DE PÁGINA
    # ========================================
    elements.append(PageBreak())
    
    # ========================================
    # PÁGINA 2 - TEXTO LEGAL
    # ========================================
    
    # Texto legal
    elements.append(Paragraph("Segue checklist, com o objetivo de conferência da documentação apresentada e continuidade do processo. A despesa está devidamente atestada pelo gestor e fiscais da área solicitante, conforme o SEI", styles['TextoLegal']))
    
    sei_atestado = mapeamento_seis.get('atestado', 'Não identificado')
    elements.append(Paragraph(f"<b>{sei_atestado}</b>.", styles['TextoLegal']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("A conformidade da despesa, nota fiscal e a documentação anexa encontram-se regulares, conforme certificação da divisão de contabilidade SEI", styles['TextoLegal']))
    
    sei_contabil = mapeamento_seis.get('contabil', 'Não identificado')
    elements.append(Paragraph(f"<b>{sei_contabil}</b>.", styles['TextoLegal']))
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph("1 - Cumpre destacar que esta checagem NÃO tem o papel de adentrar a seara do cumprimento das obrigações da contratada, no que tange às obrigações trabalhistas, previdenciárias e tributárias, inclusive pagamento das verbas salariais, vale transporte e auxílio alimentação, assim como a averiguação das Certidões de Regularidade (CRF, CND e CNDT), visto que são atribuições relacionadas aos Fiscais do Contrato conforme Decreto nº 45.600, de 16 de março de 2016.", styles['TextoLegal']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("2 – Conforme manifestação do Tribunal de Contas da União em seu Informativo 103/2012, “A perda da regularidade fiscal no curso de contratos de execução continuada ou parcela justifica a imposição de sanções à contratada, mas não autoriza a retenção de pagamento por serviços prestados”. (Acórdão nº 964/2012-Plenário, TC 017.371/2011-2, rel. Min Walton Alencar Rodrigues, 25.4.2012).", styles['TextoLegal']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("Face à análise, a despesa encontra-se em condições de prosseguimento, estando em conformidade quanto à correta classificação orçamentária, ao enquadramento legal e à formalização processual.", styles['TextoLegal']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Conclusão
    elements.append(Paragraph("<b>CONCLUSÃO:</b>", styles['InfoLabel']))
    elements.append(Paragraph(conclusao_texto, styles['InfoValue']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Observações
    if observacao_texto:
        elements.append(Paragraph("<b>OBSERVAÇÕES:</b>", styles['InfoLabel']))
        elements.append(Paragraph(observacao_texto, styles['InfoValue']))
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph("At.te", styles['InfoValue']))
    elements.append(Spacer(1, 0.5*cm))
    
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

if st.session_state.autenticado:
    uploaded_file = st.file_uploader("📤 Selecione o PDF do processo", type=['pdf'])
    
    if uploaded_file:
        with st.spinner("🔍 Analisando documento..."):
            texto = extrair_texto_pdf(uploaded_file)
            
            # Extrair dados básicos
            dados = {}
            dados['fornecedor'] = extrair_fornecedor(texto)
            dados['cnpj'] = extrair_cnpj(texto)
            dados['processo'] = extrair_processo(texto)
            dados['contrato'] = extrair_contrato(texto)
            dados['vigencia'] = extrair_vigencia(texto)
            dados['objeto'] = extrair_objeto(texto)
            dados['gestores'] = extrair_gestores(texto)
            dados['nota_fiscal'] = extrair_nota_fiscal(texto)
            dados['data_nf'] = extrair_data_emissao_nf(texto)
            dados['valor_bruto'] = extrair_valor_bruto(texto)
            dados['valor_liquido'] = extrair_valor_liquido(texto)
            dados['ne'] = extrair_nota_empenho(texto)
            dados['nl'] = extrair_nota_liquidacao(texto)
            dados['data_nl'] = extrair_data_liquidacao(texto, dados['nl'])
            dados['portaria'] = extrair_portaria(texto)
            
            # Extrair certidões
            certidoes = extrair_certidoes(texto)
            
            # Extrair retenções
            retencoes = extrair_retencoes(texto)
            
            # Extrair TODOS os números SEI (lista simples)
            todos_seis = extrair_todos_seis(texto)
            
            # Verificar mão-de-obra
            tem_mao_obra = verificar_mao_obra(texto)
            
            # Mostrar dados extraídos
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
                st.markdown("**Valor Bruto:**")
                st.info(f"R$ {dados['valor_bruto']}")
                st.markdown("**Valor Líquido:**")
                st.info(f"R$ {dados['valor_liquido']}")
                st.markdown("**Gestor:**")
                st.info(dados['gestores'][:50] + "..." if len(dados['gestores']) > 50 else dados['gestores'])
            
            st.markdown("---")
            
            # ============================================
            # MAPEAMENTO MANUAL DE SEIS (OPÇÃO 1)
            # ============================================
            
            st.subheader("🔗 MAPEAMENTO MANUAL DE NÚMEROS SEI")
            st.markdown('<div class="sei-mapper">', unsafe_allow_html=True)
            st.markdown("**Selecione os números SEI correspondentes a cada documento:**")
            
            # Inicializar mapeamento na sessão
            if 'mapeamento_seis' not in st.session_state:
                st.session_state.mapeamento_seis = {}
            
            # Adicionar opção "Não localizado" e "Não Aplicável"
            opcoes = ["Não localizado"] + todos_seis
            opcoes_com_na = ["Não localizado", "Não Aplicável"] + todos_seis
            
            # Criar layout em colunas para o mapeamento
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 1 - Nota de Empenho/Liquidação**")
                st.markdown(f"NE: {dados['ne']} | NL: {dados['nl']} | Data: {dados['data_nl']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 2 - Nota Fiscal**")
                st.session_state.mapeamento_seis['nota_fiscal'] = st.selectbox(
                    "Selecione o SEI da Nota Fiscal:", opcoes, key="sel_nf", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 8 - Portaria**")
                st.markdown(f"Número da Portaria: {dados['portaria']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 9 - Atestado do Gestor**")
                st.session_state.mapeamento_seis['atestado'] = st.selectbox(
                    "Selecione o SEI do Atestado:", opcoes, key="sel_atestado", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 10 - Relação de funcionários**")
                st.session_state.mapeamento_seis['relacao_funcionarios'] = st.selectbox(
                    "Selecione o SEI da Relação de funcionários:", opcoes, key="sel_relacao", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 11 - FGTS Digital**")
                st.session_state.mapeamento_seis['fgts_digital'] = st.selectbox(
                    "Selecione o SEI do FGTS Digital:", opcoes, key="sel_fgts_digital", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 12 - INSS**")
                st.session_state.mapeamento_seis['inss'] = st.selectbox(
                    "Selecione o SEI do INSS:", opcoes, key="sel_inss", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_right:
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 13 - FGTS**")
                st.session_state.mapeamento_seis['fgts'] = st.selectbox(
                    "Selecione o SEI do FGTS:", opcoes, key="sel_fgts", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 14 - Folha de pagamento**")
                st.session_state.mapeamento_seis['folha_pagamento'] = st.selectbox(
                    "Selecione o SEI da Folha de pagamento:", opcoes, key="sel_folha", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 15 - Comprovante de salários**")
                st.session_state.mapeamento_seis['comprovante_salarios'] = st.selectbox(
                    "Selecione o SEI do Comprovante de salários:", opcoes, key="sel_salarios", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 16 - Vale transporte**")
                st.session_state.mapeamento_seis['vale_transporte'] = st.selectbox(
                    "Selecione o SEI do Vale transporte:", opcoes, key="sel_vt", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 17 - Vale alimentação**")
                st.session_state.mapeamento_seis['vale_alimentacao'] = st.selectbox(
                    "Selecione o SEI do Vale alimentação:", opcoes, key="sel_va", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Item 18 - Rescisão**")
                st.session_state.mapeamento_seis['rescisao'] = st.selectbox(
                    "Selecione o SEI da Rescisão (ou 'Não Aplicável'):", opcoes_com_na, key="sel_rescisao", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="sei-item">', unsafe_allow_html=True)
                st.markdown("**Certificação Contábil (para o texto legal)**")
                st.session_state.mapeamento_seis['contabil'] = st.selectbox(
                    "Selecione o SEI da Certificação Contábil:", opcoes, key="sel_contabil", index=0
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar certidões (automático)
            st.markdown("---")
            st.markdown("### 📅 CERTIDÕES (DETECTADAS AUTOMATICAMENTE)")
            col_cert1, col_cert2, col_cert3 = st.columns(3)
            with col_cert1:
                st.markdown(f"**Federal:** {certidoes['federal']}")
            with col_cert2:
                st.markdown(f"**FGTS:** {certidoes['fgts_inicio']} a {certidoes['fgts_fim']}")
            with col_cert3:
                st.markdown(f"**Trabalhista:** {certidoes['trabalhista']}")
            
            st.markdown("---")
            
            # Botão para confirmar mapeamento
            if st.button("✅ CONFIRMAR MAPEAMENTO", type="primary", use_container_width=True):
                st.session_state.mapeamento_concluido = True
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ============================================
            # MONTAR RESULTADOS COM BASE NO MAPEAMENTO
            # ============================================
            
            if 'mapeamento_concluido' in st.session_state and st.session_state.mapeamento_concluido:
                
                # Construir string de retenções
                retencoes_str = []
                if retencoes.get('inss') and retencoes['inss'] != "0,00":
                    retencoes_str.append(f"INSS R$ {retencoes['inss']}")
                if retencoes.get('irrf') and retencoes['irrf'] != "0,00":
                    retencoes_str.append(f"IRRF R$ {retencoes['irrf']}")
                if retencoes.get('pis') and retencoes['pis'] != "0,00":
                    retencoes_str.append(f"PIS R$ {retencoes['pis']}")
                if retencoes.get('cofins') and retencoes['cofins'] != "0,00":
                    retencoes_str.append(f"COFINS R$ {retencoes['cofins']}")
                if retencoes.get('csll') and retencoes['csll'] != "0,00":
                    retencoes_str.append(f"CSLL R$ {retencoes['csll']}")
                
                retencoes_texto = "Há retenções (" + ", ".join(retencoes_str) + ")" if retencoes_str else "Não identificado"
                
                # Verificar validade das certidões
                data_atual = datetime.now()
                
                # Certidão Federal
                if certidoes['federal'] != "Não identificado":
                    federal_valida, _ = verificar_validade(certidoes['federal'])
                    cert_federal_obs = f"Certidão Federal válida até {certidoes['federal']}"
                else:
                    cert_federal_obs = "Não identificado"
                
                # Certidão FGTS
                if certidoes['fgts_fim'] != "Não identificado":
                    fgts_valida, _ = verificar_validade(certidoes['fgts_fim'])
                    cert_fgts_obs = f"CRF válido de {certidoes['fgts_inicio']} a {certidoes['fgts_fim']}"
                else:
                    cert_fgts_obs = "Não identificado"
                
                # Certidão Trabalhista
                if certidoes['trabalhista'] != "Não identificado":
                    trab_valida, _ = verificar_validade(certidoes['trabalhista'])
                    cert_trab_obs = f"Certidão Trabalhista válida até {certidoes['trabalhista']}"
                else:
                    cert_trab_obs = "Não identificado"
                
                resultados = [
                    {"item": 1, "descricao": checklist[0]["descricao"], 
                     "status": "S" if dados['ne'] != "Não identificado" and dados['nl'] != "Não identificado" else "N",
                     "observacao": f"{dados['ne']} (Gerando a {dados['nl']} de {dados['data_nl']})" if dados['ne'] != "Não identificado" and dados['nl'] != "Não identificado" else "Não localizado"},
                    
                    {"item": 2, "descricao": checklist[1]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('nota_fiscal') != "Não localizado" else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('nota_fiscal', 'Não localizado')}"},
                    
                    {"item": 3, "descricao": checklist[2]["descricao"], 
                     "status": "S" if certidoes['federal'] != "Não identificado" else "N",
                     "observacao": cert_federal_obs},
                    
                    {"item": 4, "descricao": checklist[3]["descricao"], 
                     "status": "S" if certidoes['fgts_fim'] != "Não identificado" else "N",
                     "observacao": cert_fgts_obs},
                    
                    {"item": 5, "descricao": checklist[4]["descricao"], 
                     "status": "S" if certidoes['trabalhista'] != "Não identificado" else "N",
                     "observacao": cert_trab_obs},
                    
                    {"item": 6, "descricao": checklist[5]["descricao"], 
                     "status": "S" if retencoes_str else "N",
                     "observacao": retencoes_texto},
                    
                    {"item": 7, "descricao": checklist[6]["descricao"], 
                     "status": "NA", "observacao": "Não se aplica"},
                    
                    {"item": 8, "descricao": checklist[7]["descricao"], 
                     "status": "S" if dados['portaria'] != "Não identificado" else "N",
                     "observacao": f"Portaria IPEM/GAPRE N.º {dados['portaria']}" if dados['portaria'] != "Não identificado" else "Não localizado"},
                    
                    {"item": 9, "descricao": checklist[8]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('atestado') != "Não localizado" else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('atestado', 'Não localizado')}"},
                    
                    {"item": 10, "descricao": checklist[9]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('relacao_funcionarios') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('relacao_funcionarios', 'Não localizado')}" if st.session_state.mapeamento_seis.get('relacao_funcionarios') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 11, "descricao": checklist[10]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('fgts_digital') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('fgts_digital', 'Não localizado')}" if st.session_state.mapeamento_seis.get('fgts_digital') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 12, "descricao": checklist[11]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('inss') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('inss', 'Não localizado')}" if st.session_state.mapeamento_seis.get('inss') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 13, "descricao": checklist[12]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('fgts') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('fgts', 'Não localizado')}" if st.session_state.mapeamento_seis.get('fgts') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 14, "descricao": checklist[13]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('folha_pagamento') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('folha_pagamento', 'Não localizado')}" if st.session_state.mapeamento_seis.get('folha_pagamento') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 15, "descricao": checklist[14]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('comprovante_salarios') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('comprovante_salarios', 'Não localizado')}" if st.session_state.mapeamento_seis.get('comprovante_salarios') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 16, "descricao": checklist[15]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('vale_transporte') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('vale_transporte', 'Não localizado')}" if st.session_state.mapeamento_seis.get('vale_transporte') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 17, "descricao": checklist[16]["descricao"], 
                     "status": "S" if st.session_state.mapeamento_seis.get('vale_alimentacao') != "Não localizado" else "NA" if not tem_mao_obra else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('vale_alimentacao', 'Não localizado')}" if st.session_state.mapeamento_seis.get('vale_alimentacao') != "Não localizado" else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                    
                    {"item": 18, "descricao": checklist[17]["descricao"], 
                     "status": "NA" if st.session_state.mapeamento_seis.get('rescisao') == "Não Aplicável" or not tem_mao_obra else "S" if st.session_state.mapeamento_seis.get('rescisao') != "Não localizado" else "N",
                     "observacao": f"SEI {st.session_state.mapeamento_seis.get('rescisao', 'Não localizado')}" if st.session_state.mapeamento_seis.get('rescisao') not in ["Não localizado", "Não Aplicável"] else ("Sem rescisão no período" if st.session_state.mapeamento_seis.get('rescisao') == "Não Aplicável" or not tem_mao_obra else "Não localizado")}
                ]
                
                # Mostrar resultados na tela
                st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
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
                
                # Resumo
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
                
                # Perguntas para o relatório
                st.markdown("---")
                st.subheader("📝 INFORMAÇÕES PARA O RELATÓRIO")
                
                tem_exigencia = st.radio("📌 Existe alguma exigência a fazer?", ["Não", "Sim"], horizontal=True)
                
                if tem_exigencia == "Sim":
                    exigencia_texto = st.text_area("✏️ Descreva a(s) exigência(s):", height=80)
                    conclusao = exigencia_texto
                else:
                    sei_contabil = st.session_state.mapeamento_seis.get('contabil', 'Não identificado')
                    conclusao = f"Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320, de 17/03/1964 e com a análise procedida da Nota Fiscal e documentação apresentada pela empresa sendo atestada e certificada sua regularidade através da liquidação de despesa pela Divisão de Contabilidade Documento SEI {sei_contabil}"
                
                tem_observacao = st.radio("📝 Existe alguma observação a fazer?", ["Não", "Sim"], horizontal=True)
                observacao_texto = st.text_area("✏️ Descreva a(s) observação(ões):", height=80) if tem_observacao == "Sim" else ""
                
                if not observacao_texto:
                    observacao_texto = f"Despesa referente a {dados['data_nf'] if dados['data_nf'] != 'Não identificado' else 'período não identificado'}."
                
                # Botão para gerar PDF
                st.markdown("---")
                if st.button("📥 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
                    with st.spinner("Gerando PDF..."):
                        pdf_bytes = gerar_pdf_final(dados, certidoes, retencoes, st.session_state.mapeamento_seis, resultados, conclusao, observacao_texto)
                        
                        st.download_button(
                            label="📄 Baixar relatório PDF",
                            data=pdf_bytes,
                            file_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.balloons()
    
    else:
        st.info("👆 Faça upload de um PDF para iniciar a análise")
else:
    st.warning("🔐 Faça login no menu lateral para acessar o sistema")

st.markdown("---")
st.caption(f"IPEM-RJ - Auditoria Interna | Sistema de Análise Automática v18.0 - Mapeamento Manual | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
