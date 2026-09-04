import io
import datetime
import streamlit as st

# Configuração da página (deve ser o primeiro comando do Streamlit)
st.set_page_config(
    page_title="Cálculo Luminotécnico",
    page_icon="💡",
    layout="wide"
)

# ==========================================
# SIMULAÇÃO DE DADOS / FUNÇÕES AUXILIARES
# ==========================================

# Simulação do dicionário de usuário atual (ajuste conforme o seu sistema de autenticação)
user_info_atual = {"tipo": "admin", "assinante": True}

# Exemplo de dados simulados caso o seu script venha de um escopo maior
# (substitua ou mantenha integrado com as variáveis reais do seu app)
prof_nome = st.sidebar.text_input("Nome do Profissional", value="Jefferson Barcellos")
prof_registro = st.sidebar.text_input("Registro / CREA / CAU", value="CREA-RJ 123456")
prof_celular = st.sidebar.text_input("Celular / WhatsApp", value="(21) 99999-9999")
prof_email = st.sidebar.text_input("E-mail Profissional", value="jefferson@email.com")
logo_upload = st.sidebar.file_uploader("Logotipo do Projeto (.png, .jpg)", type=["png", "jpg"])

# Dados simulados do cliente e ambientes para o exemplo rodar completo
cliente_dados_obj = {"Nome": "Cliente Exemplo"}
lista_calculos_ambientes = [
    {
        "nome": "Sala de Estar",
        "comp": 5.0,
        "larg": 4.0,
        "pe_direito": 2.8,
        "area": 20.0,
        "lux_req": 200.0,
        "fluxo_unidade_rel": 2200.0,
        "modelo_lum": "Painel LED 20W",
        "qtd_real_str": "4",
        "unidade_medida_qtd": "unidades",
        "arranjo_str": "2 x 2",
        "lux_real": 220.0,
        "pot_total": 80.0,
        "dpi": 4.0,
        "conforme": True
    }
]

def gerar_docx_consolidado(dados_cliente, dados_profissional, lista_ambientes, logo_file=None):
    # Função simulada de geração do Word (.docx)
    # Substitua pela sua implementação original do python-docx se necessário
    buffer_docx = io.BytesIO()
    buffer_docx.write(b"Conteudo simulado do arquivo DOCX")
    buffer_docx.seek(0)
    return buffer_docx.getvalue()


# ==========================================
# INTERFACE E EMISSÃO DE RELATÓRIO
# ==========================================

st.subheader("3. Emissão de Relatório Luminotécnico")

is_admin_or_subscriber = (user_info_atual.get("tipo") == "admin" or user_info_atual.get("assinante", False))

def gerar_pdf_consolidado(dados_cliente, dados_profissional, lista_ambientes, logo_file=None):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    cor_primaria = colors.HexColor("#1A365D")
    
    titulo_style = ParagraphStyle(
        'TituloRelatorio',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=cor_primaria,
        spaceAfter=6
    )
    
    texto_style = ParagraphStyle(
        'TextoNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor("#323232")
    )

    story.append(Paragraph("RELATÓRIO LUMINOTÉCNICO CONSOLIDADO", titulo_style))
    data_atual_str = datetime.date.today().strftime("%d/%m/%Y")
    
    info_txt = f"<b>Cliente / Empreendimento:</b> {dados_cliente.get('Nome', 'Cliente Geral')} | Método dos Lúmens<br/>" \
               f"<b>Responsável Técnico:</b> {dados_profissional.get('nome', 'Não informado')} — Registro: {dados_profissional.get('registro', 'Não informado')} | Data: {data_atual_str}<br/>" \
               f"<b>Norma de Referência:</b> NBR ISO/CIE 8995-1 & NBR 5410"
    story.append(Paragraph(info_txt, texto_style))
    story.append(Spacer(1, 15))

    for idx, amb in enumerate(lista_ambientes):
        if idx > 0:
            story.append(PageBreak())

        story.append(Paragraph(f"<b>AMBIENTE: {amb['nome'].upper()}</b>", titulo_style))
        story.append(Spacer(1, 8))

        tabela_dados = [
            ["Parâmetro", "Símbolo", "Valor Adotado", "Unidade"],
            ["Nome do Ambiente", "—", amb['nome'], "—"],
            ["Comprimento / Largura / Pé-Direito", "C x L x H", f"{amb['comp']:.2f} x {amb['larg']:.2f} x {amb['pe_direito']:.2f}", "m"],
            ["Área Total", "A", f"{amb['area']:.2f}", "m²"],
            ["Iluminância Requerida", "Ereq", f"{amb['lux_req']:.2f} lx", "NBR ISO/CIE 8995-1"],
            ["Fonte Luminosa / Equipamento", "Φ", f"{amb['fluxo_unidade_rel']:,.2f} lm", amb['modelo_lum']],
            ["Quantidade de Equipamentos", "N", f"{amb['qtd_real_str']}", amb['unidade_medida_qtd']],
            ["Arranjo Luminoso", "—", f"{amb['arranjo_str']}", "arr."],
            ["Iluminância Real Alcançada", "Ereal", f"{amb['lux_real']:.2f} lx", "Calculado"],
            ["Potência Total e DPI", "P / DPI", f"{amb['pot_total']:.2f} W | {amb['dpi']:.2f} W/m²", "W / W/m²"],
            ["Status Final", "—", "CONFORME (Aprovado)" if amb['conforme'] else "NÃO CONFORME", "—"]
        ]

        t = Table(tabela_dados, colWidths=[180, 70, 190, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white])
        ]))
        
        story.append(t)
        story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

if not is_admin_or_subscriber:
    st.warning("🔒 **Recurso Exclusivo para Assinantes:** O período de teste permite realizar os cálculos na tela, mas a geração e o download dos relatórios oficiais (.docx e .pdf) exigem uma assinatura ativa. Vá na aba **'Assinar (R$ 19,90/mês)'** no topo da página para liberar!")
else:
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        if st.button("📄 Gerar Relatório Word (.docx)", use_container_width=True):
            try:
                dados_prof_dict = {
                    "nome": prof_nome if prof_nome else "Não informado",
                    "registro": prof_registro if prof_registro else "Não informado",
                    "celular": prof_celular if prof_celular else "Não informado",
                    "email": prof_email if prof_email else "Não informado"
                }
                logo_bytes = io.BytesIO(logo_upload.getvalue()) if logo_upload is not None else None
                arquivo_docx_bytes = gerar_docx_consolidado(cliente_dados_obj, dados_prof_dict, lista_calculos_ambientes, logo_file=logo_bytes)
                
                st.success("Word gerado com sucesso!")
                st.download_button(
                    label="📥 Baixar Arquivo .docx",
                    data=arquivo_docx_bytes,
                    file_name=f"Relatorio_{cliente_dados_obj['Nome'].replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro ao gerar Word: {e}")

    with col_dl2:
        if st.button("📑 Gerar Relatório PDF (.pdf)", use_container_width=True):
            try:
                dados_prof_dict = {
                    "nome": prof_nome if prof_nome else "Não informado",
                    "registro": prof_registro if prof_registro else "Não informado",
                    "celular": prof_celular if prof_celular else "Não informado",
                    "email": prof_email if prof_email else "Não informado"
                }
                logo_bytes = io.BytesIO(logo_upload.getvalue()) if logo_upload is not None else None
                arquivo_pdf_bytes = gerar_pdf_consolidado(cliente_dados_obj, dados_prof_dict, lista_calculos_ambientes, logo_file=logo_bytes)
                
                st.success("PDF gerado com sucesso!")
                st.download_button(
                    label="📥 Baixar Arquivo .pdf",
                    data=arquivo_pdf_bytes,
                    file_name=f"Relatorio_{cliente_dados_obj['Nome'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
