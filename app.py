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

# Checklist atualizado (18 itens)
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
    {"item": 11, "descricao": "FGTS Digital", "tipo": "mao_obra"},
    {"item": 12, "descricao": "Comprovante de pagamento do INSS", "tipo": "mao_obra"},
    {"item": 13, "descricao": "Comprovante de pagamento do FGTS", "tipo": "mao_obra"},
    {"item": 14, "descricao": "Folha de pagamento", "tipo": "mao_obra"},
    {"item": 15, "descricao": "Comprovante de pagamento dos salários", "tipo": "mao_obra"},
    {"item": 16, "descricao": "Comprovante de pagamento do Vale transporte", "tipo": "mao_obra"},
    {"item": 17, "descricao": "Comprovante de pagamento do Vale alimentação / refeição", "tipo": "mao_obra"},
    {"item": 18, "descricao": "Comprovante de pagamento de rescisão e FGTS", "tipo": "mao_obra"}
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

# ============================================
# FUNÇÕES DE EXTRAÇÃO GENÉRICAS (SEM VALORES FIXOS)
# ============================================

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
    match = re.search(r'vig[êe]ncia[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    if match:
        return match.group(1)
    
    vigencia = re.search(r'(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    if vigencia:
        return f"{vigencia.group(1)} a {vigencia.group(2)}"
    
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
    # Tenta encontrar data no formato brasileiro
    data_br = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
    if data_br:
        return data_br.group(1)
    
    # Tenta encontrar data no formato ISO
    data_iso = re.search(r'(\d{4}-\d{2}-\d{2})', texto)
    if data_iso:
        return data_iso.group(1)
    
    return "Não identificado"

def extrair_valor_bruto(texto):
    """Extrai valor bruto total"""
    # Procura por valor próximo a "valor", "total", "R$"
    padroes = [
        r'valor[:\s]*R?\$?\s*([\d.,]+)',
        r'total[:\s]*R?\$?\s*([\d.,]+)',
        r'R?\$?\s*([\d.,]+)'
    ]
    
    for padrao in padroes:
        matches = re.findall(padrao, texto, re.IGNORECASE)
        if matches:
            # Pega o maior valor (provavelmente o total)
            valores = []
            for val in matches:
                try:
                    # Converte para float para comparação
                    val_clean = val.replace('.', '').replace(',', '.')
                    num = float(val_clean)
                    valores.append((num, val))
                except:
                    continue
            
            if valores:
                # Retorna o maior valor encontrado
                maior = max(valores, key=lambda x: x[0])
                return maior[1]
    
    return "0,00"

def extrair_valor_liquido(texto):
    """Extrai valor líquido (após retenções)"""
    padroes = [
        r'valor líquido[:\s]*R?\$?\s*([\d.,]+)',
        r'líquido[:\s]*R?\$?\s*([\d.,]+)',
        r'valor a pagar[:\s]*R?\$?\s*([\d.,]+)'
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return extrair_valor_bruto(texto)  # fallback

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
    
    # INSS
    inss_match = re.search(r'INSS.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['inss'] = inss_match.group(1) if inss_match else "0,00"
    
    # IRRF
    irrf_match = re.search(r'IRRF.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['irrf'] = irrf_match.group(1) if irrf_match else "0,00"
    
    # PIS
    pis_match = re.search(r'PIS.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['pis'] = pis_match.group(1) if pis_match else "0,00"
    
    # COFINS
    cofins_match = re.search(r'COFINS.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['cofins'] = cofins_match.group(1) if cofins_match else "0,00"
    
    # CSLL
    csll_match = re.search(r'CSLL.*?R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    retencoes['csll'] = csll_match.group(1) if csll_match else "0,00"
    
    return retencoes

def extrair_todos_seis(texto):
    """
    Extrai TODOS os números SEI (8-9 dígitos) do documento
    Classifica por tipo de documento baseado em palavras-chave
    """
    seis = {}
    
    # Encontrar todos os números de 8-9 dígitos
    todos_seis = re.findall(r'\b(\d{8,9})\b', texto)
    
    # 1. SEI da Nota Fiscal
    seis_nf = re.findall(r'(?:nota fiscal|nf).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['nota_fiscal'] = list(set(seis_nf)) if seis_nf else []
    
    # 2. SEI do Atestado / Relatório de Fiscalização
    seis_atestado = re.findall(r'(?:atestado|realização dos serviços|relatório de fiscalização).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['atestado'] = list(set(seis_atestado)) if seis_atestado else []
    
    # 3. SEI da Solicitação de Liquidação
    seis_solicitacao = re.findall(r'(?:solicitação|liquidação).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['solicitacao'] = list(set(seis_solicitacao)) if seis_solicitacao else []
    
    # 4. SEI da Certificação Contábil
    seis_contabil = re.findall(r'(?:contabilidade|certificação).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['contabil'] = list(set(seis_contabil)) if seis_contabil else []
    
    # 5. SEI do Checklist / Auditoria
    seis_checklist = re.findall(r'(?:checklist|auditoria).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['checklist'] = list(set(seis_checklist)) if seis_checklist else []
    
    # 6. SEI da Autorização
    seis_autorizacao = re.findall(r'(?:autoriza[çc][ãa]o|presid[eê]ncia).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['autorizacao'] = list(set(seis_autorizacao)) if seis_autorizacao else []
    
    # 7. SEI da Relação de Funcionários
    seis_relacao = re.findall(r'(?:rela[çc][ãa]o.*?funcion[áa]rios|funcionários que executam).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['relacao_funcionarios'] = list(set(seis_relacao)) if seis_relacao else []
    
    # 8. SEI do FGTS Digital / GFIP
    seis_fgts_digital = re.findall(r'(?:fgts digital|gfip|relação de trabalhadores).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['fgts_digital'] = list(set(seis_fgts_digital)) if seis_fgts_digital else []
    
    # 9. SEI do Comprovante de FGTS
    seis_fgts = re.findall(r'(?:comprovante.*?fgts|fgts.*?comprovante).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['fgts'] = list(set(seis_fgts)) if seis_fgts else []
    
    # 10. SEI dos Contracheques
    seis_contracheques = re.findall(r'(?:contracheque|recibo de pagamento de sal[áa]rio).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['contracheques'] = list(set(seis_contracheques)) if seis_contracheques else []
    
    # 11. SEI do Comprovante de INSS
    seis_inss = re.findall(r'(?:inss|previdenci[áa]ria).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['inss'] = list(set(seis_inss)) if seis_inss else []
    
    # 12. SEI do Vale Transporte
    seis_vt = re.findall(r'(?:vale.*?transporte|vt).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['vale_transporte'] = list(set(seis_vt)) if seis_vt else []
    
    # 13. SEI do Vale Alimentação
    seis_va = re.findall(r'(?:vale.*?alimenta[çc][ãa]o|alimentação|cesta).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['vale_alimentacao'] = list(set(seis_va)) if seis_va else []
    
    # 14. SEI do Despacho Inicial
    seis_despacho = re.findall(r'(?:despacho).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['despacho'] = list(set(seis_despacho)) if seis_despacho else []
    
    # 15. SEI do Encaminhamento DIRAF
    seis_diraf = re.findall(r'(?:diraf|diretor administrativo).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['diraf'] = list(set(seis_diraf)) if seis_diraf else []
    
    return seis

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

def formatar_observacao(seis_lista, prefixo="SEI", sufixo=""):
    """Formata a observação com os SEIs encontrados"""
    if seis_lista:
        return f"{prefixo} {', '.join(seis_lista)} {sufixo}".strip()
    return "Não localizado"

# ============================================
# FUNÇÃO PARA GERAR PDF
# ============================================

def gerar_pdf_final(dados, certidoes, retencoes, seis_docs, resultados, conclusao_texto, observacao_texto):
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
    valor_liquido = extrair_valor_liquido(texto) if 'texto' in locals() else dados.get('valor', '0,00')
    
    info_processo = [
        [Paragraph(f"<b>Fornecedor:</b> {dados['fornecedor'][:60]}", styles['InfoValue']),
         Paragraph(f"<b>CNPJ:</b> {dados['cnpj']}", styles['InfoValue'])],
        [Paragraph(f"<b>Contrato:</b> {dados['contrato']} | <b>Vigência:</b> {dados['vigencia']}", styles['InfoValue']),
         Paragraph(f"<b>NF:</b> {dados['nota_fiscal']} de {dados['data_nf']}", styles['InfoValue'])],
        [Paragraph(f"<b>Valor Bruto:</b> R$ {dados['valor']}", styles['InfoValue']),
         Paragraph(f"<b>Valor Líquido:</b> R$ {valor_liquido}", styles['InfoValue'])],
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
    
    sei_atestado = seis_docs.get('atestado', ['Não identificado'])[0]
    elements.append(Paragraph(f"<b>{sei_atestado}</b>.", styles['TextoLegal']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("A conformidade da despesa, nota fiscal e a documentação anexa encontram-se regulares, conforme certificação da divisão de contabilidade SEI", styles['TextoLegal']))
    
    sei_contabil = seis_docs.get('contabil', ['Não identificado'])[0]
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
            dados['valor'] = extrair_valor_bruto(texto)
            dados['ne'] = extrair_nota_empenho(texto)
            dados['nl'] = extrair_nota_liquidacao(texto)
            dados['data_nl'] = extrair_data_liquidacao(texto, dados['nl'])
            dados['portaria'] = extrair_portaria(texto)
            
            # Extrair certidões
            certidoes = extrair_certidoes(texto)
            
            # Extrair retenções
            retencoes = extrair_retencoes(texto)
            
            # Extrair TODOS os números SEI classificados
            seis_docs = extrair_todos_seis(texto)
            
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
                st.info(f"R$ {dados['valor']}")
                st.markdown("**Valor Líquido:**")
                st.info(f"R$ {extrair_valor_liquido(texto)}")
                st.markdown("**Gestor:**")
                st.info(dados['gestores'][:50] + "..." if len(dados['gestores']) > 50 else dados['gestores'])
            
            st.markdown("---")
            
            # Mostrar números SEI encontrados
            with st.expander("📋 NÚMEROS SEI ENCONTRADOS NO PROCESSO"):
                cols = st.columns(2)
                i = 0
                for tipo, lista in seis_docs.items():
                    if lista:
                        with cols[i % 2]:
                            st.markdown(f"**{tipo.replace('_', ' ').title()}:**")
                            for num in lista:
                                st.caption(f"  • {num}")
                            i += 1
            
            st.markdown("---")
            
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
            
            # Montar resultados com os SEIs encontrados
            st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
            
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
            
            resultados = [
                {"item": 1, "descricao": checklist[0]["descricao"], 
                 "status": "S" if dados['ne'] != "Não identificado" and dados['nl'] != "Não identificado" else "N",
                 "observacao": f"{dados['ne']} (Gerando a {dados['nl']} de {dados['data_nl']})" if dados['ne'] != "Não identificado" and dados['nl'] != "Não identificado" else "Não localizado"},
                
                {"item": 2, "descricao": checklist[1]["descricao"], 
                 "status": "S" if seis_docs.get('nota_fiscal') else "N",
                 "observacao": formatar_observacao(seis_docs.get('nota_fiscal', []), "SEI")},
                
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
                 "status": "S" if seis_docs.get('atestado') else "N",
                 "observacao": formatar_observacao(seis_docs.get('atestado', []), "SEI")},
                
                {"item": 10, "descricao": checklist[9]["descricao"], 
                 "status": "S" if seis_docs.get('relacao_funcionarios') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('relacao_funcionarios', []), "SEI") if seis_docs.get('relacao_funcionarios') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 11, "descricao": checklist[10]["descricao"], 
                 "status": "S" if seis_docs.get('fgts_digital') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('fgts_digital', []), "SEI") if seis_docs.get('fgts_digital') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 12, "descricao": checklist[11]["descricao"], 
                 "status": "S" if seis_docs.get('inss') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('inss', []), "SEI") if seis_docs.get('inss') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 13, "descricao": checklist[12]["descricao"], 
                 "status": "S" if seis_docs.get('fgts') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('fgts', []), "SEI") if seis_docs.get('fgts') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 14, "descricao": checklist[13]["descricao"], 
                 "status": "S" if seis_docs.get('fgts_digital') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('fgts_digital', []), "SEI") if seis_docs.get('fgts_digital') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 15, "descricao": checklist[14]["descricao"], 
                 "status": "S" if seis_docs.get('contracheques') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('contracheques', []), "SEI") if seis_docs.get('contracheques') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 16, "descricao": checklist[15]["descricao"], 
                 "status": "S" if seis_docs.get('vale_transporte') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('vale_transporte', []), "SEI") if seis_docs.get('vale_transporte') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 17, "descricao": checklist[16]["descricao"], 
                 "status": "S" if seis_docs.get('vale_alimentacao') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('vale_alimentacao', []), "SEI") if seis_docs.get('vale_alimentacao') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 18, "descricao": checklist[17]["descricao"], 
                 "status": "NA" if not tem_mao_obra else "N",
                 "observacao": "Sem rescisão no período" if not tem_mao_obra else "Não localizado"}
            ]
            
            # Mostrar resultados na tela
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
                sei_contabil = seis_docs.get('contabil', ['Não identificado'])[0]
                conclusao = f"Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320, de 17/03/1964 e com a análise procedida da Nota Fiscal e documentação apresentada pela empresa sendo atestada e certificada sua regularidade através da liquidação de despesa pela Divisão de Contabilidade Documento SEI {sei_contabil}"
            
            tem_observacao = st.radio("📝 Existe alguma observação a fazer?", ["Não", "Sim"], horizontal=True)
            observacao_texto = st.text_area("✏️ Descreva a(s) observação(ões):", height=80) if tem_observacao == "Sim" else ""
            
            # Botão para gerar PDF
            st.markdown("---")
            if st.button("📥 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf_final(dados, certidoes, retencoes, seis_docs, resultados, conclusao, observacao_texto)
                    
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
st.caption(f"IPEM-RJ - Auditoria Interna | Sistema de Análise Automática v16.0 - Genérico | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
