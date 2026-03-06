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
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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

# Checklist completo com palavras-chave
checklist = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo (art. 63, §1°, II, da Lei 4320/64)", 
     "palavras": ["nota de empenho", "empenho", "demonstrativo de saldo", "saldo", "ne", "empenhada", "nota de liquidação", "nl"],
     "tipo": "obrigatorio"},
    
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM, de acordo com o empenho e com o objeto", 
     "palavras": ["nota fiscal", "nf", "fatura", "ipem", "nota fiscal de serviço", "nfs"],
     "tipo": "obrigatorio"},
    
    {"item": 3, "descricao": "Certidão de regularidade relativo aos tributos federais e dívida ativa da União", 
     "palavras": ["certidao federal", "receita federal", "divida ativa", "tributos federais", "certidao conjunta"],
     "tipo": "obrigatorio"},
    
    {"item": 4, "descricao": "Certidão de regularidade junto ao FGTS", 
     "palavras": ["certidao fgts", "fgts", "regularidade fgts", "cnd fgts", "certidao de regularidade do fgts"],
     "tipo": "obrigatorio"},
    
    {"item": 5, "descricao": "Certidão de regularidade junto a Justiça do Trabalho", 
     "palavras": ["certidao trabalho", "justica do trabalho", "trabalhista", "cnd trabalhista", "certidao trabalhista"],
     "tipo": "obrigatorio"},
    
    {"item": 6, "descricao": "No caso de incidir tributos a serem retidos da fonte, consta indicação?", 
     "palavras": ["tributos retidos", "retencao", "fonte", "irrf", "pis", "cofins", "cssl"],
     "tipo": "condicional"},
    
    {"item": 7, "descricao": "Quando não incidir tributos, há documento de comprovação da não incidência?", 
     "palavras": ["nao incidencia", "isencao", "imunidade", "dispensa", "nao retencao"],
     "tipo": "condicional"},
    
    {"item": 8, "descricao": "Portaria de Nomeação de Fiscalização", 
     "palavras": ["portaria", "nomeacao", "fiscal", "gapre", "designacao", "portaria de nomeacao"],
     "tipo": "obrigatorio"},
    
    {"item": 9, "descricao": "Atestado do Gestor do contrato de que os serviços ou aquisições contratados foram prestados a contento", 
     "palavras": ["atestado", "gestor", "liquidacao", "servicos prestados", "a contento", "atestado de liquidacao"],
     "tipo": "obrigatorio"},
    
    {"item": 10, "descricao": "Relação dos funcionários que executaram o serviço", 
     "palavras": ["relacao funcionarios", "relacao de empregados", "funcionarios", "equipe", "lista de funcionarios"],
     "tipo": "mao_obra"},
    
    {"item": 11, "descricao": "Comprovante da GFIP", 
     "palavras": ["gfip", "guia fgts", "conectividade social", "sefp", "fgts digital"],
     "tipo": "mao_obra"},
    
    {"item": 12, "descricao": "Comprovante de pagamento do INSS", 
     "palavras": ["inss", "guia inss", "gps", "previdencia", "guia da previdencia"],
     "tipo": "mao_obra"},
    
    {"item": 13, "descricao": "Comprovante de pagamento do FGTS", 
     "palavras": ["fgts", "guia fgts", "recolhimento fgts", "comprovante fgts"],
     "tipo": "mao_obra"},
    
    {"item": 14, "descricao": "Protocolo do envio dos arquivos - Conectividade Social", 
     "palavras": ["conectividade social", "protocolo", "transmissao", "conectividade", "recibo de entrega"],
     "tipo": "mao_obra"},
    
    {"item": 15, "descricao": "Folha de pagamento", 
     "palavras": ["folha de pagamento", "folha", "payroll", "holerite", "folha salarial"],
     "tipo": "mao_obra"},
    
    {"item": 16, "descricao": "Comprovante de pagamento dos salários", 
     "palavras": ["comprovante salario", "recibo salario", "holerite", "contracheque", "recibo de pagamento"],
     "tipo": "mao_obra"},
    
    {"item": 17, "descricao": "Comprovante de pagamento do Vale transporte", 
     "palavras": ["vale transporte", "vt", "vale transport", "comprovante vt"],
     "tipo": "mao_obra"},
    
    {"item": 18, "descricao": "Comprovante de pagamento do Vale alimentação / refeição", 
     "palavras": ["vale alimentacao", "va", "vale refeicao", "vr", "alimentacao", "vale refeição"],
     "tipo": "mao_obra"},
    
    {"item": 19, "descricao": "Comprovante de pagamento de rescisão e FGTS", 
     "palavras": ["rescisao", "fgts rescisorio", "termino de contrato", "demissao", "verbas rescisorias"],
     "tipo": "mao_obra"}
]

# Função para extrair fornecedor
def extrair_fornecedor(texto):
    padroes = [
        r'(?:fornecedor|empresa|contratada|razao social)[:\s]+([A-Z][A-Z\s.]+)',
        r'(?:razao social|denominacao)[:\s]+([A-Z][A-Z\s.]+)',
        r'([A-Z][A-Z\s]+(?:LTDA|Ltda|ME|EIRELI|SA|S/A))'
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Não identificado"

# Função para extrair nota de empenho e liquidação (VINCULADA)
def extrair_ne_nl(texto):
    """
    Extrai e vincula automaticamente a Nota de Empenho com a Nota de Liquidação
    Formato: 2026NE00123 (Gerando a 2026NL00118 de 05/03/2026)
    """
    # Padrões para encontrar Nota de Empenho
    ne_pattern = r'2026NE\d{5}'
    ne_matches = re.findall(ne_pattern, texto)
    
    # Padrões para encontrar Nota de Liquidação
    nl_pattern = r'2026NL\d{5}'
    nl_matches = re.findall(nl_pattern, texto)
    
    # Se encontrou ambos
    if ne_matches and nl_matches:
        ne = ne_matches[0]  # Pega o primeiro NE encontrado
        
        # Tentar encontrar data da liquidação
        data_pattern = r'2026NL\d{5}.*?(\d{2}/\d{2}/\d{4})'
        data_match = re.search(data_pattern, texto, re.DOTALL)
        data = data_match.group(1) if data_match else "data não encontrada"
        
        # Procurar todas as NLs para ver qual está mais próxima da NE no texto
        melhor_nl = nl_matches[0]  # Pega a primeira por padrão
        
        # Tentar encontrar contexto onde NE e NL aparecem juntas
        contexto_pattern = fr'{ne}.*?({nl_pattern})'
        contexto_match = re.search(contexto_pattern, texto, re.DOTALL)
        if contexto_match:
            melhor_nl = contexto_match.group(1)
        
        return f"{ne} (Gerando a {melhor_nl} de {data})"
    
    # Se só encontrou NE
    elif ne_matches:
        return ne_matches[0]
    
    # Se não encontrou nada
    else:
        return "Não identificado"

# Função para extrair data de validade de certidões
def extrair_validade_certidao(texto, tipo):
    padroes = [
        r'validade[:\s]*(\d{2}/\d{2}/\d{4})',
        r'valido[:\s]*ate[:\s]*(\d{2}/\d{2}/\d{4})',
        r'válida[:\s]*até[:\s]*(\d{2}/\d{2}/\d{4})'
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

# Função para gerar PDF
def gerar_pdf_resultados(dados_processo, resultados_checklist, conclusao_texto, observacoes):
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
    
    # Estilos personalizados
    styles.add(ParagraphStyle(
        name='Cabecalho',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='TituloPrincipal',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5f9e'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    # Cabeçalho
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
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a5f9e')),
    ]))
    elements.append(cabecalho_table)
    
    # SEI
    sei_text = Paragraph(f"SEI - {dados_processo.get('processo', 'XXXXXX/XXXXXX/202X')}", styles['Cabecalho'])
    elements.append(sei_text)
    elements.append(Spacer(1, 0.3*cm))
    
    # Título
    titulo = Paragraph("CHECKLIST DE DOCUMENTAÇÃO DOS PROCESSO DE DESPESAS REGULARES", styles['TituloPrincipal'])
    elements.append(titulo)
    elements.append(Spacer(1, 0.5*cm))
    
    # Dados do processo
    dados_data = [
        [f"Nome do fornecedor: {dados_processo.get('fornecedor', '__________________')}", 
         f"CNPJ: {dados_processo.get('cnpj', '__________________')}"],
        [f"Contrato / Convênio: {dados_processo.get('processo', '__________________')}",
         f"Vigência: {dados_processo.get('vigencia', '__________________')}"],
        [f"Objeto do Contrato/Serv./Mat.: {dados_processo.get('objeto', '__________________')}", ""],
        [f"Gestor e Fiscais: {dados_processo.get('gestor', dados_processo.get('fiscal', '__________________'))}", ""],
        [f"Nº da NF / Fatura: {dados_processo.get('nota_fiscal', '__________________')}",
         f"Venc.: {dados_processo.get('vencimento', '__________________')}  Valor: R$ {dados_processo.get('valor', '__________________')}"]
    ]
    
    dados_table = Table(dados_data, colWidths=[doc.width/2.2, doc.width/2.2])
    dados_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(dados_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Checklist
    checklist_data = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados_checklist:
        # Quebrar descrição longa
        descricao = res['descricao']
        if len(descricao) > 70:
            descricao = descricao[:70] + "..."
        
        # Para o item 1, garantir que a observação mostre a vinculação NE → NL
        observacao = res['observacao']
        if res['item'] == 1 and 'Gerando a' in observacao:
            # Mantém o formato especial
            pass
        
        checklist_data.append([
            str(res['item']),
            descricao,
            res['status'],
            observacao
        ])
    
    checklist_table = Table(checklist_data, colWidths=[1.2*cm, 10*cm, 1.5*cm, 4*cm])
    checklist_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f9e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(checklist_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Legenda
    elements.append(Paragraph("S = Sim ; N = Não ; N.A. = Não Aplicável", 
                             ParagraphStyle('Legenda', parent=styles['Normal'], fontSize=8)))
    elements.append(Spacer(1, 0.5*cm))
    
    # Conclusão
    elements.append(Paragraph(f"Conclusão: {conclusao_texto}", styles['Normal']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Texto da conclusão detalhado
    if "Nada tem a opor" in conclusao_texto:
        conclusao_final = "X Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320, de 17/03/1964 e com a análise procedida da Nota Fiscal e documentação apresentada pela empresa sendo atestada e certificada sua regularidade através da liquidação de despesa pela Divisão de Contabilidade."
    else:
        conclusao_final = "Após a regularização das exigências, retornar à Auditoria Interna para análise processual, com fulcro no art. 62, da Lei 4.320, de 17/03/1964"
    
    elements.append(Paragraph(f"     {conclusao_final}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Observações
    elements.append(Paragraph(f"Observações: {observacoes}", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Assinatura
    elements.append(Paragraph("_________________________________________", 
                              ParagraphStyle('Assinatura', parent=styles['Normal'], alignment=TA_CENTER)))
    elements.append(Paragraph("Assinatura do Responsável", 
                              ParagraphStyle('AssinaturaLabel', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)))
    
    # Rodapé
    elements.append(Spacer(1, 0.5*cm))
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    footer = Paragraph(f"Relatório gerado automaticamente em {data_atual}", 
                      ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER, textColor=colors.grey))
    elements.append(footer)
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

# Sidebar com login
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
        with st.spinner("🔍 Analisando documento completo..."):
            # Ler o PDF
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            texto_completo = ""
            for page in pdf_reader.pages:
                texto_completo += page.extract_text() or ""
            
            texto_lower = texto_completo.lower()
            
            st.markdown(f'<div class="success-box">✅ PDF carregado: {uploaded_file.name} | 📄 Páginas: {len(pdf_reader.pages)} | 📊 Caracteres: {len(texto_completo)}</div>', unsafe_allow_html=True)
            
            # Extrair dados do processo
            st.subheader("📊 DADOS DO PROCESSO")
            
            dados_processo = {}
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                dados_processo['fornecedor'] = extrair_fornecedor(texto_completo)
                st.markdown("**Fornecedor:**")
                st.info(dados_processo['fornecedor'])
            
            with col2:
                cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto_completo)
                dados_processo['cnpj'] = cnpj.group() if cnpj else "Não identificado"
                st.markdown("**CNPJ:**")
                st.info(dados_processo['cnpj'])
            
            with col3:
                processo = re.search(r'(?:processo|sei)[:\s]*([\d/-]+)', texto_lower)
                dados_processo['processo'] = processo.group(1) if processo else "Não identificado"
                st.markdown("**Processo/SEI:**")
                st.info(dados_processo['processo'])
            
            with col4:
                fiscal = re.search(r'(?:fiscal|gestor)[:\s]*([A-Z][A-Z\s]+)', texto_completo)
                dados_processo['fiscal'] = fiscal.group(1).strip() if fiscal else "Não identificado"
                st.markdown("**Fiscal:**")
                st.info(dados_processo['fiscal'])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                nf = re.search(r'(?:nota fiscal|nf)[:\s]*[nº°]?\s*(\d+)', texto_lower)
                dados_processo['nota_fiscal'] = nf.group(1) if nf else "Não identificado"
                st.markdown("**Nota Fiscal:**")
                st.info(dados_processo['nota_fiscal'])
            
            with col2:
                valor = re.search(r'valor[:\s]*R?\$?\s*([\d.,]+)', texto_lower)
                dados_processo['valor'] = valor.group(1) if valor else "0,00"
                st.markdown("**Valor:**")
                st.info(f"R$ {dados_processo['valor']}")
            
            with col3:
                vigencia = re.search(r'vig[êe]ncia[:\s]*(\d{2}/\d{2}/\d{4})', texto_lower)
                dados_processo['vigencia'] = vigencia.group(1) if vigencia else "Não identificado"
                st.markdown("**Vigência:**")
                st.info(dados_processo['vigencia'])
            
            with col4:
                venc = re.search(r'vencimento[:\s]*(\d{2}/\d{2}/\d{4})', texto_lower)
                dados_processo['vencimento'] = venc.group(1) if venc else "Não identificado"
                st.markdown("**Vencimento:**")
                st.info(dados_processo['vencimento'])
            
            objeto = re.search(r'(?:objeto|contrato)[:\s]*([^\n]+)', texto_completo)
            dados_processo['objeto'] = objeto.group(1).strip() if objeto else "Extraído do processo"
            
            st.markdown("---")
            
            # Verificar se é serviço com mão-de-obra
            palavras_mao_obra = ['mao de obra', 'terceirizado', 'funcionario', 'empregado', 'posto de trabalho']
            tem_mao_obra = any(palavra in texto_lower for palavra in palavras_mao_obra)
            
            if tem_mao_obra:
                st.markdown('<div class="info-box">🔧 Serviço com mão-de-obra identificado</div>', unsafe_allow_html=True)
            
            # EXTRAIR NOTA DE EMPENHO E LIQUIDAÇÃO VINCULADAS
            ne_nl_vinculadas = extrair_ne_nl(texto_completo)
            
            # RESULTADO DA ANÁLISE
            st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
            
            resultados = []
            
            for doc in checklist:
                # Determinar status
                if doc['item'] >= 10 and not tem_mao_obra:
                    status = "NA"
                    observacao = "Sem mão-de-obra"
                else:
                    # Buscar palavras no texto
                    palavras_encontradas = []
                    for palavra in doc['palavras']:
                        if palavra in texto_lower:
                            palavras_encontradas.append(palavra)
                    
                    if palavras_encontradas:
                        status = "S"
                        
                        # TRATAMENTO ESPECIAL PARA O ITEM 1
                        if doc['item'] == 1:
                            if ne_nl_vinculadas != "Não identificado":
                                observacao = ne_nl_vinculadas
                            else:
                                observacao = "Documento encontrado"
                        
                        # Certidões (itens 3,4,5)
                        elif doc['item'] in [3,4,5]:
                            validade = extrair_validade_certidao(texto_lower, doc['item'])
                            if validade:
                                observacao = f"Válida até: {validade}"
                            else:
                                observacao = "Documento encontrado"
                        
                        # Portaria (item 8)
                        elif doc['item'] == 8:
                            portaria = re.search(r'portaria[:\s]*(\d+/\d{4})', texto_lower)
                            if portaria:
                                observacao = f"Portaria {portaria.group(1)}"
                            else:
                                observacao = "Documento encontrado"
                        
                        # Atestado (item 9)
                        elif doc['item'] == 9:
                            sei = re.search(r'sei[:\s]*(\d+)', texto_lower)
                            if sei:
                                observacao = f"Documento SEI {sei.group(1)}"
                            else:
                                observacao = "Documento encontrado"
                        
                        # Outros documentos
                        else:
                            observacao = "Documento encontrado"
                    else:
                        status = "N"
                        observacao = "Não localizado"
                
                resultados.append({
                    'item': doc['item'],
                    'descricao': doc['descricao'],
                    'status': status,
                    'observacao': observacao
                })
                
                # Mostrar resultado
                col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
                with col1:
                    st.markdown(f"**{doc['item']}**")
                with col2:
                    st.markdown(doc['descricao'])
                with col3:
                    if status == "S":
                        st.markdown(f"✅ **S**")
                    elif status == "N":
                        st.markdown(f"❌ **N**")
                    else:
                        st.markdown(f"⚪ **NA**")
                with col4:
                    st.caption(observacao)
            
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
                conclusao = "Nada tem a opor quanto ao prosseguimento"
                st.markdown(f'<div class="success-box">✅ {conclusao}, com fulcro no art. 62, da Lei 4.320/64</div>', unsafe_allow_html=True)
            else:
                conclusao = "Após a regularização das exigências, retornar à Auditoria Interna para análise processual"
                st.markdown(f'<div class="warning-box">⚠️ {conclusao}</div>', unsafe_allow_html=True)
            
            observacoes = st.text_area("📌 Observações:", 
                                      value=f"Despesa referente a {datetime.now().strftime('%m/%Y')}.", 
                                      height=100)
            
            # Botão para gerar PDF
            st.markdown("---")
            if st.button("📥 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf_resultados(dados_processo, resultados, conclusao, observacoes)
                    
                    st.download_button(
                        label="📄 Clique aqui para baixar o relatório PDF",
                        data=pdf_bytes,
                        file_name=f"relatorio_analise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.balloons()
            
            with st.expander("📄 Ver texto extraído do PDF"):
                st.text(texto_completo[:5000] + "...")
    
    else:
        st.info("👆 Faça upload de um PDF para iniciar a análise completa")
        
        with st.expander("📋 Ver lista completa de documentos (19 itens)"):
            for doc in checklist:
                st.write(f"**{doc['item']}.** {doc['descricao']}")
else:
    st.warning("🔐 Faça login no menu lateral para acessar o sistema")

st.markdown("---")
st.caption(f"IPEM-RJ - Auditoria Interna | Sistema de Análise Automática v3.0 | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
