import streamlit as st
import PyPDF2
import re
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import base64

st.set_page_config(
    page_title="Análise IPEM-RJ",
    page_icon="✅",
    layout="wide"
)

st.title("📋 ANÁLISE DE PROCESSO DE PAGAMENTO - IPEM/RJ")
st.markdown("---")

# Checklist COMPLETO com 19 itens
checklist = [
    {"item": 1, "descricao": "Nota de empenho e demonstrativo de saldo (art. 63, §1°, II, da Lei 4320/64)", 
     "palavras": ["nota de empenho", "empenho", "demonstrativo de saldo", "saldo"]},
    
    {"item": 2, "descricao": "Nota Fiscal em nome do IPEM, de acordo com o empenho e com o objeto", 
     "palavras": ["nota fiscal", "nf", "fatura", "ipem"]},
    
    {"item": 3, "descricao": "Certidão de regularidade relativo aos tributos federais e dívida ativa da União junto a Receita Federal", 
     "palavras": ["certidao federal", "receita federal", "divida ativa", "tributos federais"]},
    
    {"item": 4, "descricao": "Certidão de regularidade junto ao FGTS", 
     "palavras": ["certidao fgts", "fgts", "regularidade fgts", "cnd fgts"]},
    
    {"item": 5, "descricao": "Certidão de regularidade junto a Justiça do Trabalho", 
     "palavras": ["certidao trabalho", "justica do trabalho", "trabalhista", "cnd trabalhista"]},
    
    {"item": 6, "descricao": "No caso de incidir tributos a serem retidos da fonte, consta indicação?", 
     "palavras": ["tributos retidos", "retencao", "fonte", "irrf", "pis", "cofins"]},
    
    {"item": 7, "descricao": "Quando não incidir tributos, há documento de comprovação da não incidência?", 
     "palavras": ["nao incidencia", "isencao", "imunidade", "dispensa"]},
    
    {"item": 8, "descricao": "Portaria de Nomeação de Fiscalização", 
     "palavras": ["portaria", "nomeacao", "fiscal", "gapre", "designacao"]},
    
    {"item": 9, "descricao": "Atestado do Gestor do contrato de que os serviços ou aquisições contratados foram prestados a contento (Lei nº 8666/93, art. 73 e 74)", 
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
    
    styles.add(ParagraphStyle(
        name='InfoLabel',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='InfoValue',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=5
    ))
    
    # Cabeçalho do governo
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
        ('SPACEAFTER', (0, -1), (-1, -1), 10),
    ]))
    elements.append(cabecalho_table)
    
    # Número SEI
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
        [f"Gestor e Fiscais: {dados_processo.get('gestor', '__________________')}", ""],
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
    
    # Tabela do checklist
    checklist_data = [["ITEM", "EVENTO A SER VERIFICADO", "S/N/NA", "OBSERVAÇÕES"]]
    
    for res in resultados_checklist:
        # Quebrar descrição longa
        descricao = res['descricao']
        if len(descricao) > 70:
            descricao = descricao[:70] + "..."
        
        checklist_data.append([
            str(res['item']),
            descricao,
            res['status'],
            res['observacao'][:40] if res['observacao'] else ""
        ])
    
    checklist_table = Table(checklist_data, colWidths=[1.2*cm, 10*cm, 1.5*cm, 4*cm])
    checklist_table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f9e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Linhas de dados
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    # Aplicar cores baseadas no status
    for i, res in enumerate(resultados_checklist, start=1):
        if res['status'] == 'S':
            bg_color = colors.HexColor('#d4edda')  # Verde claro
        elif res['status'] == 'N':
            bg_color = colors.HexColor('#f8d7da')  # Vermelho claro
        else:
            bg_color = colors.HexColor('#e2e3e5')  # Cinza claro
        
        checklist_table.setStyle(TableStyle([
            ('BACKGROUND', (2, i), (2, i), bg_color),
        ]))
    
    elements.append(checklist_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Legenda
    legenda = Paragraph("S = Sim ; N = Não ; N.A. = Não Aplicável", 
                        ParagraphStyle('Legenda', parent=styles['Normal'], fontSize=8, alignment=TA_LEFT))
    elements.append(legenda)
    elements.append(Spacer(1, 0.5*cm))
    
    # Exigências
    elements.append(Paragraph("Exigências:", styles['InfoLabel']))
    elements.append(Spacer(1, 0.2*cm))
    
    # Conclusão
    elements.append(Paragraph(f"Conclusão: {conclusao_texto}", styles['InfoValue']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Texto da conclusão
    if "Nada tem a opor" in conclusao_texto:
        conclusao_final = "X Nada tem a opor quanto ao prosseguimento, com fulcro no art. 62, da Lei 4.320, de 17/03/1964 e com a análise procedida da Nota Fiscal e documentação apresentada pela empresa sendo atestada e certificada sua regularidade através da liquidação de despesa pela Divisão de Contabilidade."
        elements.append(Paragraph(f"     {conclusao_final}", styles['InfoValue']))
    else:
        conclusao_final = "Após a regularização da(s) exigência(s), retornar à Auditoria Interna para análise processual, com fulcro no art. 62, da Lei 4.320, de 17/03/1964"
        elements.append(Paragraph(f"     {conclusao_final}", styles['InfoValue']))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Observações
    elements.append(Paragraph(f"Observações: {observacoes}", styles['InfoValue']))
    elements.append(Spacer(1, 1*cm))
    
    # Linha para assinatura
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
        
        dados_processo = {}
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # CNPJ
            cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto_completo)
            dados_processo['cnpj'] = cnpj.group() if cnpj else "Não identificado"
            st.markdown("**CNPJ:**")
            st.info(dados_processo['cnpj'])
        
        with col2:
            # Processo/SEI
            processo = re.search(r'(?:processo|sei)[:\s]*(\d+[.-]?\d*[.-]?\d*)', texto_lower)
            dados_processo['processo'] = processo.group(1) if processo else "Não identificado"
            st.markdown("**Processo/SEI:**")
            st.info(dados_processo['processo'])
        
        with col3:
            # Nota Fiscal
            nf = re.search(r'(?:nota fiscal|nf)[:\s]*n[º°]?\s*(\d+)', texto_lower)
            dados_processo['nota_fiscal'] = nf.group(1) if nf else "Não identificado"
            st.markdown("**Nota Fiscal:**")
            st.info(dados_processo['nota_fiscal'])
        
        with col4:
            # Valor
            valor = re.search(r'valor[:\s]*R?\$?\s*([\d.,]+)', texto_lower)
            dados_processo['valor'] = valor.group(1) if valor else "0,00"
            st.markdown("**Valor:**")
            st.info(f"R$ {dados_processo['valor']}")
        
        # Campos adicionais
        dados_processo['fornecedor'] = "Não identificado"
        dados_processo['vigencia'] = "Não identificado"
        dados_processo['gestor'] = "Não identificado"
        dados_processo['objeto'] = "Extraído do processo"
        
        st.markdown("---")
        
        # Verificar se é serviço com mão-de-obra
        palavras_mao_obra = ['mao de obra', 'terceirizado', 'funcionario', 'empregado', 'posto de trabalho']
        tem_mao_obra = any(palavra in texto_lower for palavra in palavras_mao_obra)
        
        if tem_mao_obra:
            st.info("🔧 **Identificado:** Serviço com mão-de-obra - itens 10 a 19 serão verificados")
        
        # RESULTADO DA ANÁLISE
        st.subheader("✅ CHECKLIST DE DOCUMENTAÇÃO")
        
        resultados = []
        
        # Analisar cada documento
        for doc in checklist:
            resultado = {
                'item': doc['item'],
                'descricao': doc['descricao']
            }
            
            # Determinar se aplicável
            if doc['item'] >= 10 and not tem_mao_obra:
                resultado['status'] = "NA"
                resultado['observacao'] = "Sem mão-de-obra no processo"
            else:
                # Buscar palavras no texto
                palavras_encontradas = []
                for palavra in doc['palavras']:
                    if palavra in texto_lower:
                        palavras_encontradas.append(palavra)
                
                # Definir status
                if len(palavras_encontradas) >= 1:
                    resultado['status'] = "S"
                    if doc['item'] in [3,4,5]:  # Certidões
                        data = re.search(r'validade[:\s]*(\d{2}/\d{2}/\d{4})', texto_lower)
                        if data:
                            resultado['observacao'] = f"Válida até: {data.group(1)}"
                        else:
                            resultado['observacao'] = f"Encontrado"
                    else:
                        resultado['observacao'] = f"Encontrado"
                else:
                    resultado['status'] = "N"
                    resultado['observacao'] = "Não localizado"
            
            resultados.append(resultado)
            
            # Mostrar resultado na tela
            col1, col2, col3, col4 = st.columns([0.5, 8, 0.8, 4])
            with col1:
                st.markdown(f"**{doc['item']}**")
            with col2:
                st.markdown(doc['descricao'][:70] + "..." if len(doc['descricao']) > 70 else doc['descricao'])
            with col3:
                if resultado['status'] == "S":
                    st.markdown(f"✅ **S**")
                elif resultado['status'] == "N":
                    st.markdown(f"❌ **N**")
                else:
                    st.markdown(f"⚪ **NA**")
            with col4:
                st.caption(resultado['observacao'])
        
        # RESUMO E CONCLUSÃO
        st.markdown("---")
        st.subheader("📝 CONCLUSÃO")
        
        # Verificar documentos obrigatórios
        docs_obrigatorios = [1,2,3,4,5,8,9]
        obrigatorios_encontrados = sum(1 for r in resultados if r['item'] in docs_obrigatorios and r['status'] == "S")
        
        if obrigatorios_encontrados == len(docs_obrigatorios):
            conclusao = "Nada tem a opor quanto ao prosseguimento"
            st.success("✅ " + conclusao)
        else:
            conclusao = "Após a regularização das exigências, retornar à Auditoria Interna"
            st.warning("⚠️ " + conclusao)
        
        # Observações
        observacoes = st.text_area("📌 Observações:", 
                                  value=f"Despesa referente a {datetime.now().strftime('%m/%Y')}.", 
                                  height=100)
        
        # Botão para gerar PDF
        st.markdown("---")
        if st.button("📥 GERAR RELATÓRIO PDF", type="primary", use_container_width=True):
            with st.spinner("Gerando PDF..."):
                pdf_bytes = gerar_pdf_resultados(dados_processo, resultados, conclusao, observacoes)
                
                # Download do PDF
                st.download_button(
                    label="📄 Clique aqui para baixar o relatório PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_analise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.balloons()
        
        # Mostrar texto completo (opcional)
        with st.expander("📄 Ver texto extraído do PDF"):
            st.text(texto_completo[:5000] + "...")
        
else:
    st.info("👆 Faça upload de um PDF para iniciar a análise completa")
    
    # Mostrar checklist
    with st.expander("📋 Ver lista completa de documentos (19 itens)"):
        for doc in checklist:
            st.write(f"**{doc['item']}.** {doc['descricao']}")

st.markdown("---")
st.caption(f"IPEM-RJ - Auditoria Interna | Análise em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
