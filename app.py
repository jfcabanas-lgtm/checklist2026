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
# FUNÇÕES DE EXTRAÇÃO PRECISAS
# ============================================

def extrair_texto_pdf(pdf_file):
    """Extrai texto de qualquer PDF"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    texto = ""
    for page in pdf_reader.pages:
        texto += page.extract_text() or ""
    return texto

def extrair_dados_basicos(texto):
    """Extrai informações básicas do processo"""
    dados = {}
    
    # Fornecedor - busca por padrões comuns
    padroes_fornecedor = [
        r'(?:fornecedor|empresa|contratada|razao social)[:\s]*([A-Z][A-Z\s.,&]+(?:LTDA|Ltda|ME|EIRELI|SA|S/A))',
        r'(?:fornecedor|empresa|contratada)[:\s]*([A-Z][A-Z\s.,&]+)',
        r'([A-Z][A-Z\s.,&]+(?:LTDA|Ltda|ME|EIRELI|SA|S/A))'
    ]
    dados['fornecedor'] = "Não identificado"
    for padrao in padroes_fornecedor:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            dados['fornecedor'] = match.group(1).strip()
            break
    
    # CNPJ
    cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
    dados['cnpj'] = cnpj_match.group() if cnpj_match else "Não identificado"
    
    # Processo SEI
    processo_match = re.search(r'SEI[-/\s]*(\d+[-/\s]*\d+[-/\s]*\d+)', texto, re.IGNORECASE)
    dados['processo'] = processo_match.group(1) if processo_match else "Não identificado"
    
    # Contrato
    contrato_match = re.search(r'(?:contrato|processo)[:\s]*(\d+/\d{4})', texto, re.IGNORECASE)
    dados['contrato'] = contrato_match.group(1) if contrato_match else "Não identificado"
    
    # Vigência
    vigencia_match = re.search(r'vig[êe]ncia[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    dados['vigencia'] = vigencia_match.group(1) if vigencia_match else "Não identificado"
    
    # Objeto
    objeto_match = re.search(r'(?:objeto|descrição do serviço)[:\s]*([^\n]+)', texto, re.IGNORECASE)
    dados['objeto'] = objeto_match.group(1).strip() if objeto_match else "Não identificado"
    
    # Gestores
    gestores = []
    gestor_match = re.search(r'(?:gestor)[:\s]*([A-Z][A-Z\s]+)', texto, re.IGNORECASE)
    if gestor_match:
        gestores.append(gestor_match.group(1).strip())
    
    fiscais = re.findall(r'(?:fiscal)[:\s]*([A-Z][A-Z\s]+)', texto, re.IGNORECASE)
    for fiscal in fiscais:
        if fiscal.strip() not in gestores:
            gestores.append(fiscal.strip())
    
    dados['gestores'] = ", ".join(gestores) if gestores else "Não identificado"
    
    # Nota Fiscal
    nf_match = re.search(r'(?:nota fiscal|nf|nfs[ -]e)[:\s]*n[º°]?\s*(\d+)', texto, re.IGNORECASE)
    dados['nota_fiscal'] = nf_match.group(1) if nf_match else "Não identificado"
    
    # Data de emissão
    data_match = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
    dados['data_emissao'] = data_match.group(1) if data_match else "Não identificado"
    
    # Valor
    valor_match = re.search(r'valor[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    dados['valor'] = valor_match.group(1) if valor_match else "0,00"
    
    # Nota de Empenho
    ne_match = re.search(r'\d{4}NE\d{5}', texto)
    dados['ne'] = ne_match.group() if ne_match else "Não identificado"
    
    # Nota de Liquidação
    nl_match = re.search(r'\d{4}NL\d{5}', texto)
    dados['nl'] = nl_match.group() if nl_match else "Não identificado"
    
    # Data da Liquidação
    if dados['nl'] != "Não identificado":
        contexto = re.search(f"{dados['nl']}.*?(\\d{{2}}/\\d{{2}}/\\d{{4}})", texto, re.DOTALL)
        dados['data_nl'] = contexto.group(1) if contexto else "Não identificado"
    else:
        dados['data_nl'] = "Não identificado"
    
    # Portaria
    portaria_match = re.search(r'(\d+/\d{4})', texto)
    dados['portaria'] = portaria_match.group(1) if portaria_match else "Não identificado"
    
    return dados

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

def extrair_seis_especificos(texto):
    """
    Extrai números SEI específicos baseado em contexto
    Retorna um dicionário com os SEIs encontrados para cada tipo de documento
    """
    seis = {}
    
    # Encontrar TODOS os números de 8-9 dígitos
    todos_seis = re.findall(r'\b(\d{8,9})\b', texto)
    
    # 1. SEI da Nota Fiscal - próximo a "nota fiscal" ou "nf"
    seis_nf = re.findall(r'(?:nota fiscal|nf).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['nota_fiscal'] = list(set(seis_nf)) if seis_nf else []
    
    # 2. SEI do Atestado - próximo a "atestado" ou "realização dos serviços"
    seis_atestado = re.findall(r'(?:atestado|realização dos serviços).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['atestado'] = list(set(seis_atestado)) if seis_atestado else []
    
    # 3. SEI da Solicitação de Liquidação
    seis_solicitacao = re.findall(r'(?:solicitação|liquidação).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['solicitacao'] = list(set(seis_solicitacao)) if seis_solicitacao else []
    
    # 4. SEI da Certificação Contábil
    seis_contabil = re.findall(r'(?:contabilidade|certificação).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['contabil'] = list(set(seis_contabil)) if seis_contabil else []
    
    # 5. SEI da Autorização
    seis_autorizacao = re.findall(r'(?:autoriza[çc][ãa]o|presid[eê]ncia).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['autorizacao'] = list(set(seis_autorizacao)) if seis_autorizacao else []
    
    # 6. SEI de Relação de Funcionários
    seis_relacao = re.findall(r'(?:rela[çc][ãa]o.*?funcion[áa]rios).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['relacao_funcionarios'] = list(set(seis_relacao)) if seis_relacao else []
    
    # 7. SEI de Folha de Pagamento
    seis_folha = re.findall(r'(?:folha.*?pagamento).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['folha_pagamento'] = list(set(seis_folha)) if seis_folha else []
    
    # 8. SEI de Comprovante de Salários
    seis_salarios = re.findall(r'(?:comprovante.*?sal[áa]rios).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['comprovante_salarios'] = list(set(seis_salarios)) if seis_salarios else []
    
    # 9. SEI de Vale Transporte
    seis_vt = re.findall(r'(?:vale.*?transporte|vt).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['vale_transporte'] = list(set(seis_vt)) if seis_vt else []
    
    # 10. SEI de Alimentação
    seis_ali = re.findall(r'(?:alimenta[çc][ãa]o|cesta).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['alimentacao'] = list(set(seis_ali)) if seis_ali else []
    
    # 11. SEI de FGTS
    seis_fgts = re.findall(r'(?:fgts|crf).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['fgts'] = list(set(seis_fgts)) if seis_fgts else []
    
    # 12. SEI de INSS
    seis_inss = re.findall(r'(?:inss|previdenci[áa]ria).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['inss'] = list(set(seis_inss)) if seis_inss else []
    
    # 13. SEI de Folha de Ponto
    seis_ponto = re.findall(r'(?:folha.*?ponto|ponto.*?funcion[áa]rios).*?(\d{8,9})', texto, re.IGNORECASE | re.DOTALL)
    seis['folha_ponto'] = list(set(seis_ponto)) if seis_ponto else []
    
    return seis

def verificar_mao_obra(texto):
    """Verifica se há indícios de mão-de-obra"""
    palavras = ['mao de obra', 'terceirizado', 'funcionario', 'empregado', 'posto de trabalho',
                'folha de pagamento', 'salário', 'vale transporte', 'cesta básica', 'recibo de pagamento']
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

def formatar_observacao(seis_lista, prefixo=""):
    """Formata a observação com os SEIs encontrados"""
    if seis_lista:
        return f"{prefixo} {', '.join(seis_lista)}".strip()
    return "Não localizado"

# ============================================
# FUNÇÃO PARA GERAR PDF (CORRIGIDA)
# ============================================

def gerar_pdf_final(dados, certidoes, seis_docs, resultados, conclusao_texto, observacao_texto):
    """
    Gera um PDF profissional com formatação correta
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
        fontSize=6.5,
        fontName='Helvetica',
        leading=9,
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
    
    # Dados do processo em tabela compacta
    dados_processo = [
        [Paragraph(f"<b>Fornecedor:</b> {dados['fornecedor'][:60]}", styles['InfoValue']),
         Paragraph(f"<b>CNPJ:</b> {dados['cnpj']}", styles['InfoValue'])],
        [Paragraph(f"<b>Contrato:</b> {dados['contrato']} | <b>Vigência:</b> {dados['vigencia']}", styles['InfoValue']),
         Paragraph(f"<b>NF:</b> {dados['nota_fiscal']}", styles['InfoValue'])],
        [Paragraph(f"<b>Valor:</b> R$ {dados['valor']} | <b>Gestor:</b> {dados['gestores'][:40]}", styles['InfoValue']),
         Paragraph("", styles['InfoValue'])]
    ]
    
    tabela_dados = Table(dados_processo, colWidths=[10*cm, 7.5*cm])
    tabela_dados.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(tabela_dados)
    elements.append(Spacer(1, 0.3*cm))
    
    # Checklist
    cabecalho_checklist = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados:
        # Limitar tamanho das descrições
        descricao = res['descricao']
        if len(descricao) > 60:
            descricao = descricao[:57] + "..."
        
        # Limitar tamanho das observações
        obs = res['observacao']
        if len(obs) > 35:
            obs = obs[:32] + "..."
        
        cabecalho_checklist.append([
            Paragraph(str(res['item']), ParagraphStyle('Item', fontSize=7, alignment=TA_CENTER)),
            Paragraph(descricao, styles['TabelaItem']),
            Paragraph(res['status'], ParagraphStyle('Status', fontSize=7, alignment=TA_CENTER)),
            Paragraph(obs, styles['TabelaObs'])
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
            
            # Extrair dados
            dados = extrair_dados_basicos(texto)
            certidoes = extrair_certidoes(texto)
            seis_docs = extrair_seis_especificos(texto)
            tem_mao_obra = verificar_mao_obra(texto)
            
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
                st.info(dados['nota_fiscal'])
                st.markdown("**Valor:**")
                st.info(f"R$ {dados['valor']}")
                st.markdown("**Contrato:**")
                st.info(dados['contrato'])
            
            # Mostrar SEIs encontrados
            st.markdown("---")
            st.subheader("🔍 NÚMEROS SEI ENCONTRADOS")
            cols = st.columns(3)
            i = 0
            for tipo, lista in seis_docs.items():
                if lista:
                    with cols[i % 3]:
                        st.markdown(f"**{tipo.replace('_', ' ').title()}:**")
                        st.caption(", ".join(lista))
                    i += 1
            
            st.markdown("---")
            
            # Verificar validade das certidões
            data_atual = datetime.now()
            
            # Certidão Federal
            if certidoes['federal'] != "Não identificado":
                valida, _ = verificar_validade(certidoes['federal'])
                cert_federal_obs = f"Válida até {certidoes['federal']}"
            else:
                cert_federal_obs = "Não identificado"
            
            # Certidão FGTS
            if certidoes['fgts_fim'] != "Não identificado":
                valida, _ = verificar_validade(certidoes['fgts_fim'])
                cert_fgts_obs = f"{certidoes['fgts_inicio']} a {certidoes['fgts_fim']}"
            else:
                cert_fgts_obs = "Não identificado"
            
            # Certidão Trabalhista
            if certidoes['trabalhista'] != "Não identificado":
                valida, _ = verificar_validade(certidoes['trabalhista'])
                cert_trab_obs = f"Válida até {certidoes['trabalhista']}"
            else:
                cert_trab_obs = "Não identificado"
            
            # Montar resultados
            resultados = [
                {"item": 1, "descricao": checklist[0]["descricao"], 
                 "status": "S" if dados['ne'] != "Não identificado" else "N",
                 "observacao": f"{dados['ne']} (Gerando {dados['nl']} de {dados['data_nl']})" if dados['ne'] != "Não identificado" else "Não localizado"},
                
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
                 "status": "S" if "retenção" in texto.lower() else "NA",
                 "observacao": "Há retenções" if "retenção" in texto.lower() else "Não se aplica"},
                
                {"item": 7, "descricao": checklist[6]["descricao"], 
                 "status": "NA", "observacao": "Não se aplica"},
                
                {"item": 8, "descricao": checklist[7]["descricao"], 
                 "status": "S" if dados['portaria'] != "Não identificado" else "N",
                 "observacao": f"Portaria IPEM nº {dados['portaria']}" if dados['portaria'] != "Não identificado" else "Não localizado"},
                
                {"item": 9, "descricao": checklist[8]["descricao"], 
                 "status": "S" if seis_docs.get('atestado') else "N",
                 "observacao": formatar_observacao(seis_docs.get('atestado', []), "SEI")},
                
                {"item": 10, "descricao": checklist[9]["descricao"], 
                 "status": "S" if seis_docs.get('relacao_funcionarios') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('relacao_funcionarios', []), "SEI") if seis_docs.get('relacao_funcionarios') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 11, "descricao": checklist[10]["descricao"], 
                 "status": "NA" if not tem_mao_obra else "N",
                 "observacao": "Sem mão-de-obra" if not tem_mao_obra else "Não localizado"},
                
                {"item": 12, "descricao": checklist[11]["descricao"], 
                 "status": "S" if seis_docs.get('inss') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('inss', []), "SEI") if seis_docs.get('inss') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 13, "descricao": checklist[12]["descricao"], 
                 "status": "S" if seis_docs.get('fgts') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('fgts', []), "SEI") if seis_docs.get('fgts') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 14, "descricao": checklist[13]["descricao"], 
                 "status": "NA" if not tem_mao_obra else "N",
                 "observacao": "Sem mão-de-obra" if not tem_mao_obra else "Não localizado"},
                
                {"item": 15, "descricao": checklist[14]["descricao"], 
                 "status": "S" if seis_docs.get('folha_pagamento') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('folha_pagamento', []), "SEI") if seis_docs.get('folha_pagamento') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 16, "descricao": checklist[15]["descricao"], 
                 "status": "S" if seis_docs.get('comprovante_salarios') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('comprovante_salarios', []), "SEI") if seis_docs.get('comprovante_salarios') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 17, "descricao": checklist[16]["descricao"], 
                 "status": "S" if seis_docs.get('vale_transporte') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('vale_transporte', []), "SEI") if seis_docs.get('vale_transporte') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 18, "descricao": checklist[17]["descricao"], 
                 "status": "S" if seis_docs.get('alimentacao') else "NA" if not tem_mao_obra else "N",
                 "observacao": formatar_observacao(seis_docs.get('alimentacao', []), "SEI") if seis_docs.get('alimentacao') else ("Sem mão-de-obra" if not tem_mao_obra else "Não localizado")},
                
                {"item": 19, "descricao": checklist[18]["descricao"], 
                 "status": "NA" if not tem_mao_obra else "N",
                 "observacao": "Sem mão-de-obra" if not tem_mao_obra else "Não localizado"}
            ]
            
            # Mostrar resultados
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
            
            # Perguntas
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
            
            # Botão PDF
            st.markdown("---")
            if st.button("📥 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf_final(dados, certidoes, seis_docs, resultados, conclusao, observacao_texto)
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
st.caption(f"IPEM-RJ - Auditoria Interna | Sistema de Análise Automática v12.0 - Corrigido | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
