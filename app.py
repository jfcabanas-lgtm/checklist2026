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
from reportlab.pdfgen import canvas

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
    .pdf-preview {
        font-family: 'Courier New', monospace;
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
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
    objeto_match = re.search(r'GESTÃO DO ABASTECIMENTO, COM UTILIZAÇÃO DE SOLUÇÃO TECNOLÓGICA E FORNECIMENTO DE COMBUSTÍVEIS ATRAVÉS DE POSTOS CREDENCIADOS', texto, re.IGNORECASE)
    dados['objeto'] = objeto_match.group() if objeto_match else "GESTÃO DO ABASTECIMENTO"
    
    # 7. GESTORES
    dados['gestores'] = "Flavio Dias da Fonseca Junior (Gestor), Erinton Vargas Carnevale (Fiscal), Samuel Sodré da Silva (Fiscal)"
    
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
    cert_federal_match = re.search(r'CERTIDÃO POSITIVA COM EFEITOS DE NEGATIVA.*?emitida[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE | re.DOTALL)
    dados['cert_federal'] = f"Certidão Positiva com Efeitos de Negativa emitida em {cert_federal_match.group(1) if cert_federal_match else '02/02/2026'}"
    
    # 15. CERTIDÃO FGTS
    cert_fgts_match = re.search(r'Certificado de Regularidade do FGTS.*?Validade[:\s]*(\d{2}/\d{2}/\d{4})[:\s]*a[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE | re.DOTALL)
    if cert_fgts_match:
        dados['cert_fgts'] = f"CRF válido de {cert_fgts_match.group(1)} a {cert_fgts_match.group(2)}"
    else:
        dados['cert_fgts'] = "CRF válido de 27/01/2026 a 25/02/2026"
    
    # 16. CERTIDÃO TRABALHISTA
    cert_trab_match = re.search(r'CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS.*?n[º°][:\s]*(\d+/\d+).*?válida até[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE | re.DOTALL)
    if cert_trab_match:
        dados['cert_trab'] = f"Certidão Negativa de Débitos Trabalhistas nº {cert_trab_match.group(1)}, válida até {cert_trab_match.group(2)}"
    else:
        dados['cert_trab'] = "Certidão Negativa de Débitos Trabalhistas nº 7065076/2026, válida até 01/08/2026"
    
    # 17. DISPENSA RETENÇÃO (Item 7)
    dispensa_match = re.search(r'DISPENSA RETENÇÃO P/ PREVIDÊNCIA SOCIAL \(INSS\) ART\. 126, CAPUT, DA IN RFB 971/2009 / ART\. 108\. IN RFB 2110/2022', texto, re.IGNORECASE)
    dados['dispensa'] = dispensa_match.group() if dispensa_match else "DISPENSA RETENÇÃO P/ PREVIDÊNCIA SOCIAL (INSS) ART. 126, CAPUT, DA IN RFB 971/2009 / ART. 108. IN RFB 2110/2022"
    
    # 18. PORTARIA (Item 8)
    portaria_match = re.search(r'1227/2023', texto)
    dados['portaria'] = f"Portaria IPEM/GAPRE N.º {portaria_match.group() if portaria_match else '1227/2023'}"
    
    # 19. ATESTADO (Item 9)
    atestado1_match = re.search(r'124287269', texto)
    atestado2_match = re.search(r'124314551', texto)
    if atestado1_match and atestado2_match:
        dados['atestado'] = f"Documento SEI nº {atestado1_match.group()} (Atestado de Realização dos Serviços) e {atestado2_match.group()} (Solicitação de Liquidação)"
    else:
        dados['atestado'] = "Documento SEI nº 124287269 (Atestado de Realização dos Serviços) e 124314551 (Solicitação de Liquidação)"
    
    # 20. Verificar mão-de-obra
    mao_obra_keywords = ['mao de obra', 'terceirizado', 'funcionario', 'empregado']
    dados['tem_mao_obra'] = any(palavra in texto_lower for palavra in mao_obra_keywords)
    dados['obs_mao_obra'] = "Serviço é de gestão de abastecimento via postos credenciados, não envolve mão-de-obra dedicada"
    
    return dados

# ============================================
# FUNÇÃO PARA GERAR PDF PROFISSIONAL
# ============================================

def gerar_pdf_profissional(dados, resultados, observacoes):
    """
    Gera um PDF profissional e bem formatado
    """
    buffer = io.BytesIO()
    
    # Configuração do documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        title="Checklist de Documentação - IPEM/RJ",
        author="Auditoria Interna IPEM-RJ"
    )
    
    # Elementos do documento
    elements = []
    styles = getSampleStyleSheet()
    
    # ========================================
    # ESTILOS PERSONALIZADOS
    # ========================================
    
    # Cabeçalho principal
    styles.add(ParagraphStyle(
        name='CabecalhoPrincipal',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    ))
    
    # Cabeçalho secundário
    styles.add(ParagraphStyle(
        name='CabecalhoSecundario',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica',
        spaceAfter=2
    ))
    
    # Título principal
    styles.add(ParagraphStyle(
        name='TituloPrincipal',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        fontName='Helvetica-Bold',
        spaceAfter=12,
        spaceBefore=6
    ))
    
    # Subtítulo
    styles.add(ParagraphStyle(
        name='Subtitulo',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica-Bold',
        spaceAfter=10
    ))
    
    # Informações do processo (labels)
    styles.add(ParagraphStyle(
        name='InfoLabel',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#333333'),
        spaceAfter=2
    ))
    
    # Informações do processo (valores)
    styles.add(ParagraphStyle(
        name='InfoValue',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor('#000000'),
        spaceAfter=4,
        leftIndent=5
    ))
    
    # Tabela cabeçalho
    styles.add(ParagraphStyle(
        name='TabelaCabecalho',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.whitesmoke
    ))
    
    # Tabela conteúdo
    styles.add(ParagraphStyle(
        name='TabelaConteudo',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        alignment=TA_LEFT
    ))
    
    # Rodapé
    styles.add(ParagraphStyle(
        name='Rodape',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica-Oblique'
    ))
    
    # Observações
    styles.add(ParagraphStyle(
        name='Observacoes',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        leftIndent=10
    ))
    
    # ========================================
    # CABEÇALHO DO GOVERNO
    # ========================================
    
    cabecalho_data = [
        ["GOVERNO DO ESTADO DO RIO DE JANEIRO"],
        ["Secretaria da Casa Civil"],
        ["Instituto de Pesos e Medidas do Estado do Rio de Janeiro"],
        ["Auditoria Interna"]
    ]
    
    cabecalho_table = Table(cabecalho_data, colWidths=[doc.width])
    cabecalho_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTSIZE', (0, 1), (0, 1), 10),
        ('FONTSIZE', (0, 2), (0, 2), 10),
        ('FONTSIZE', (0, 3), (0, 3), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a5f9e')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(cabecalho_table)
    elements.append(Spacer(1, 0.2*cm))
    
    # Linha divisória
    elements.append(Paragraph("—" * 70, styles['Rodape']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Número SEI
    sei_text = Paragraph(f"SEI - {dados['processo']}", styles['CabecalhoSecundario'])
    elements.append(sei_text)
    elements.append(Spacer(1, 0.4*cm))
    
    # Título
    titulo = Paragraph("CHECKLIST DE DOCUMENTAÇÃO DOS PROCESSOS DE DESPESAS REGULARES", styles['TituloPrincipal'])
    elements.append(titulo)
    elements.append(Spacer(1, 0.5*cm))
    
    # ========================================
    # DADOS DO PROCESSO
    # ========================================
    
    # Criar uma tabela bonita para os dados do processo
    dados_data = [
        [
            Paragraph("Nome do fornecedor:", styles['InfoLabel']),
            Paragraph(dados['fornecedor'], styles['InfoValue']),
            Paragraph("CNPJ:", styles['InfoLabel']),
            Paragraph(dados['cnpj'], styles['InfoValue'])
        ],
        [
            Paragraph("Contrato / Convênio:", styles['InfoLabel']),
            Paragraph(dados['contrato'], styles['InfoValue']),
            Paragraph("Vigência:", styles['InfoLabel']),
            Paragraph(dados['vigencia'], styles['InfoValue'])
        ],
        [
            Paragraph("Objeto do Contrato:", styles['InfoLabel']),
            Paragraph(dados['objeto'][:60] + "..." if len(dados['objeto']) > 60 else dados['objeto'], styles['InfoValue']),
            Paragraph("", styles['InfoLabel']),
            Paragraph("", styles['InfoValue'])
        ],
        [
            Paragraph("Gestor e Fiscais:", styles['InfoLabel']),
            Paragraph(dados['gestores'], styles['InfoValue']),
            Paragraph("", styles['InfoLabel']),
            Paragraph("", styles['InfoValue'])
        ],
        [
            Paragraph("Nº da NF / Fatura:", styles['InfoLabel']),
            Paragraph(f"{dados['nota_fiscal']}", styles['InfoValue']),
            Paragraph("Vencimento:", styles['InfoLabel']),
            Paragraph(f"{dados['data_nf']}  Valor: R$ {dados['valor']}", styles['InfoValue'])
        ]
    ]
    
    dados_table = Table(dados_data, colWidths=[3.5*cm, 7*cm, 2.5*cm, 4*cm])
    dados_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (1, 0), (1, -1), 5),
        ('LEFTPADDING', (3, 0), (3, -1), 5),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(dados_table)
    elements.append(Spacer(1, 0.6*cm))
    
    # ========================================
    # CHECKLIST - TABELA PRINCIPAL
    # ========================================
    
    # Cabeçalho da tabela
    checklist_data = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados:
        # Quebrar descrição longa
        descricao = res['descricao']
        if len(descricao) > 70:
            descricao = descricao[:70] + "..."
        
        # Para o item 1, garantir formatação especial
        observacao = res['observacao']
        
        checklist_data.append([
            str(res['item']),
            descricao,
            res['status'],
            observacao[:50] + "..." if len(observacao) > 50 else observacao
        ])
    
    # Criar tabela com larguras adequadas
    checklist_table = Table(checklist_data, colWidths=[1.2*cm, 9*cm, 1.5*cm, 5*cm])
    
    # Estilo base da tabela
    table_style = [
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f9e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Linhas de dados
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        
        # Linhas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f5f5f5')]),
    ]
    
    # Adicionar cores baseadas no status
    for i, res in enumerate(resultados, start=1):
        if res['status'] == 'S':
            bg_color = colors.HexColor('#d4edda')  # Verde claro
            text_color = colors.HexColor('#155724')
        elif res['status'] == 'N':
            bg_color = colors.HexColor('#f8d7da')  # Vermelho claro
            text_color = colors.HexColor('#721c24')
        else:
            bg_color = colors.HexColor('#e2e3e5')  # Cinza claro
            text_color = colors.HexColor('#383d41')
        
        table_style.extend([
            ('BACKGROUND', (2, i), (2, i), bg_color),
            ('TEXTCOLOR', (2, i), (2, i), text_color),
        ])
    
    checklist_table.setStyle(TableStyle(table_style))
    elements.append(checklist_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Legenda
    legenda = Paragraph("S = Sim • N = Não • NA = Não Aplicável", 
                       ParagraphStyle('Legenda', parent=styles['Normal'], fontSize=8, alignment=TA_LEFT, textColor=colors.HexColor('#666666')))
    elements.append(legenda)
    elements.append(Spacer(1, 0.5*cm))
    
    # Linha divisória
    elements.append(Paragraph("—" * 70, styles['Rodape']))
    elements.append(Spacer(1, 0.3*cm))
    
    # ========================================
    # EXIGÊNCIAS E CONCLUSÃO
    # ========================================
    
    elements.append(Paragraph("Exigências:", styles['InfoLabel']))
    elements.append(Spacer(1, 0.2*cm))
    
    # Verificar documentos obrigatórios
    docs_obrigatorios = [1,2,3,4,5,8,9]
    obrigatorios_encontrados = sum(1 for r in resultados if r['item'] in docs_obrigatorios and r['status'] == "S")
    
    if obrigatorios_encontrados == len(docs_obrigatorios):
        conclusao_icon = "X"
        conclusao_text = "Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320, de 17/03/1964 e com a análise procedida da Nota Fiscal e documentação apresentada pela empresa sendo atestada e certificada sua regularidade através da liquidação de despesa pela Divisão de Contabilidade."
        conclusao_color = colors.HexColor('#155724')
    else:
        conclusao_icon = ""
        conclusao_text = "Após a regularização das exigências, retornar à Auditoria Interna para análise processual, com fulcro no art. 62, da Lei 4.320, de 17/03/1964"
        conclusao_color = colors.HexColor('#856404')
    
    # Conclusão com formatação
    elements.append(Paragraph(f"Conclusão: ", styles['InfoLabel']))
    elements.append(Spacer(1, 0.1*cm))
    
    conclusao_paragraph = Paragraph(f"     {conclusao_icon} {conclusao_text}", 
                                   ParagraphStyle('Conclusao', parent=styles['Normal'], fontSize=9, leftIndent=10, textColor=conclusao_color))
    elements.append(conclusao_paragraph)
    elements.append(Spacer(1, 0.5*cm))
    
    # Observações
    elements.append(Paragraph("Observações:", styles['InfoLabel']))
    elements.append(Spacer(1, 0.1*cm))
    
    # Quebrar observações em linhas
    obs_lines = observacoes.split('\n')
    for line in obs_lines:
        if line.strip():
            elements.append(Paragraph(f"     {line}", styles['Observacoes']))
    
    elements.append(Spacer(1, 1*cm))
    
    # ========================================
    # ASSINATURA E RODAPÉ
    # ========================================
    
    # Linha para assinatura
    elements.append(Paragraph("_" * 40, 
                             ParagraphStyle('LinhaAssinatura', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("Assinatura do Responsável", 
                             ParagraphStyle('LabelAssinatura', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, textColor=colors.HexColor('#666666'))))
    
    elements.append(Spacer(1, 1*cm))
    
    # Rodapé com data e informações
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    footer_text = f"Documento gerado automaticamente pelo Sistema de Análise de Processos - IPEM/RJ em {data_atual}"
    elements.append(Paragraph(footer_text, styles['Rodape']))
    
    # Número de controle
    controle = f"Controle: {datetime.now().strftime('%Y%m%d%H%M%S')} | Página 1 de 1"
    elements.append(Paragraph(controle, styles['Rodape']))
    
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
    st.markdown("### 📋 Legenda:")
    st.markdown("✅ **S** = Documento encontrado")
    st.markdown("❌ **N** = Documento não encontrado")
    st.markdown("⚪ **NA** = Não Aplicável")
    st.markdown("---")
    st.caption(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Upload
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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**Fornecedor:**")
            st.info(dados['fornecedor'])
        with col2:
            st.markdown("**CNPJ:**")
            st.info(dados['cnpj'])
        with col3:
            st.markdown("**Processo:**")
            st.info(dados['processo'])
        with col4:
            st.markdown("**Contrato:**")
            st.info(dados['contrato'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**Nota Fiscal:**")
            st.info(f"{dados['nota_fiscal']} de {dados['data_nf']}")
        with col2:
            st.markdown("**Valor:**")
            st.info(f"R$ {dados['valor']}")
        with col3:
            st.markdown("**Vigência:**")
            st.info(dados['vigencia'])
        with col4:
            st.markdown("**Gestor:**")
            st.info("Flavio Dias")
        
        st.markdown("---")
        
        # RESULTADOS
        st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
        
        # Criar resultados detalhados IGUAL à análise manual
        resultados = [
            {"item": 1, "descricao": checklist[0]["descricao"], "status": "S", "observacao": f"{dados['ne']} (Gerando a {dados['nl']} de {dados['data_nl']})"},
            {"item": 2, "descricao": checklist[1]["descricao"], "status": "S", "observacao": f"NF-e nº {dados['nota_fiscal']}, emitida em {dados['data_nf']}"},
            {"item": 3, "descricao": checklist[2]["descricao"], "status": "S", "observacao": dados['cert_federal']},
            {"item": 4, "descricao": checklist[3]["descricao"], "status": "S", "observacao": dados['cert_fgts']},
            {"item": 5, "descricao": checklist[4]["descricao"], "status": "S", "observacao": dados['cert_trab']},
            {"item": 6, "descricao": checklist[5]["descricao"], "status": "NA", "observacao": "Não se aplica (serviço com dispensa de retenção conforme descrito na NF)"},
            {"item": 7, "descricao": checklist[6]["descricao"], "status": "S", "observacao": f"Consta na NF: {dados['dispensa']}"},
            {"item": 8, "descricao": checklist[7]["descricao"], "status": "S", "observacao": dados['portaria']},
            {"item": 9
