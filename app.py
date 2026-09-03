import streamlit as st
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
import io
import tempfile
import os

# --- FUNÇÃO DE GERAÇÃO DE PDF NATIVO (FPDF2) ---
def gerar_pdf(dados_cliente, dados_prof, dados_ambiente, logo_file=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Inserção da Logo se enviada
    if logo_file is not None:
        logo_file.seek(0)
        ext = logo_file.name.split('.')[-1].lower()
        if ext in ['png', 'jpg', 'jpeg']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
                tmp_file.write(logo_file.read())
                tmp_path = tmp_file.name
            try:
                pdf.image(tmp_path, x=80, y=10, w=50)
                pdf.ln(25)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    # Cabeçalho do Documento
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MEMORIAL DE CÁLCULO LUMINOTÉCNICO", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Em conformidade com a NBR ISO/CIE 8995-1", ln=True, align="C")
    pdf.ln(8)
    
    # Bloco: Identificação das Partes
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. Identificação do Projeto", ln=True)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(0, 6, f"Cliente / Empreendimento: {dados_cliente['nome']}", ln=True)
    if dados_cliente['doc']:
        pdf.cell(0, 6, f"CPF/CNPJ: {dados_cliente['doc']}", ln=True)
    if dados_cliente['endereco']:
        pdf.cell(0, 6, f"Endereço: {dados_cliente['endereco']}", ln=True)
        
    pdf.ln(3)
    pdf.cell(0, 6, f"Responsável Técnico: {dados_prof['nome']}", ln=True)
    pdf.cell(0, 6, f"Registro (CREA/CFT): {dados_prof['registro']}", ln=True)
    if dados_prof['contato']:
        pdf.cell(0, 6, f"Contato/E-mail: {dados_prof['contato']}", ln=True)
    pdf.ln(6)

    # Bloco: Dados do Ambiente
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"2. Dados do Recinto: {dados_ambiente['nome']}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(0, 6, f"• Dimensões: {dados_ambiente['comprimento']}m (C) x {dados_ambiente['largura']}m (L) x {dados_ambiente['pe_direito']}m (H)", ln=True)
    pdf.cell(0, 6, f"• Área Útil Total: {dados_ambiente['area']:.2f} m²", ln=True)
    pdf.cell(0, 6, f"• Atividade: {dados_ambiente['atividade']}", ln=True)
    pdf.cell(0, 6, f"• Iluminância Alvo Requerida (NBR 8995-1): {dados_ambiente['lux_req']} lx", ln=True)
    pdf.ln(6)

    # Bloco: Resultados
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Dimensionamento e Resultados", ln=True)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(0, 6, f"• Índice do Recinto (K): {dados_ambiente['k_indice']:.2f}", ln=True)
    pdf.cell(0, 6, f"• Quantidade de Luminárias Necessárias: {dados_ambiente['qtd_lum']} un", ln=True)
    pdf.cell(0, 6, f"• Potência Instalada Total: {dados_ambiente['pot_total']:.1f} W", ln=True)
    pdf.cell(0, 6, f"• Densidade de Potência: {dados_ambiente['densidade']:.2f} W/m²", ln=True)
    pdf.ln(10)

    # Retorna o PDF gerado em memória
    buffer = io.BytesIO()
    pdf_output = pdf.output()
    buffer.write(pdf_output)
    buffer.seek(0)
    return buffer


# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Luminotécnica NBR 8995-1", layout="wide")

st.title("⚡ Sistema Luminotécnica")
st.write("Dimensionamento Profissional e Gerador de Memoriais de Cálculo.")

# Sidebar - Dados do Profissional e Logo
st.sidebar.header("🎨 Personalização da Marca")
logo_upload = st.sidebar.file_uploader("Envie a Logo para o Relatório (PNG/JPG)", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.header("👨‍💻 Dados do Responsável Técnico")
prof_nome = st.sidebar.text_input("Nome do Profissional", "Jefferson Borges")
prof_registro = st.sidebar.text_input("CREA / CFT", "Engenheiro Eletricista")
prof_contato = st.sidebar.text_input("Telefone / E-mail", "contato@empresa.com")

TABELA_NORMA = {
    "Escritórios - Escrever, digitar, ler, processar dados": 500,
    "Escritórios - Desenho técnico": 750,
    "Salas de Reunião / Conferência": 500,
    "Salas de Aula / Treinamento": 500,
    "Corredores e Áreas de Circulação": 100,
    "Depósitos / Almoxarifados (Trabalho bruto)": 100,
    "Depósitos / Almoxarifados (Trabalho fino)": 300,
    "Áreas de Produção Industrial (Geral)": 300,
    "Laboratórios / Testes e Inspeção": 750,
    "Personalizado (Digitar manualmente)": 500
}

tab1, tab2 = st.tabs(["📐 Dimensionamento Único", "📋 Gerenciamento em Lote"])

with tab1:
    st.subheader("1. Dados do Cliente")
    col_c1, col_c2, col_c3 = st.columns(3)
    cli_nome = col_c1.text_input("Cliente / Nome da Obra", "Hotel Xavier")
    cli_doc = col_c2.text_input("CPF / CNPJ (Opcional)", "")
    cli_end = col_c3.text_input("Endereço (Opcional)", "Barra Longa / MG")

    st.markdown("---")
    st.subheader("2. Entrada de Dados do Ambiente")
    col_a, col_b = st.columns(2)
    
    with col_a:
        nome_ambiente = st.text_input("Nome do Ambiente", "Sala de Reuniões 01")
        tipo_atividade = st.selectbox("Tipo de Atividade (NBR ISO/CIE 8995-1)", list(TABELA_NORMA.keys()))
        lux_padrao = TABELA_NORMA[tipo_atividade]
        
        iluminancia = st.number_input("Iluminância Requerida (lx)", value=lux_padrao, step=50)
        comprimento = st.number_input("Comprimento (m)", value=8.0, step=0.5)
        largura = st.number_input("Largura (m)", value=5.0, step=0.5)
        pe_direito = st.number_input("Pé-Direito (m)", value=3.0, step=0.1)

    with col_b:
        st.subheader("Dados da Luminária / Lâmpada")
        fluxo = st.number_input("Fluxo Luminoso por Luminária (lm)", value=3200, step=100)
        potencia = st.number_input("Potência por Luminária (W)", value=32, step=1)
        fator_utilizacao = st.slider("Fator de Utilização (u)", 0.10, 0.90, 0.55, step=0.01)
        fator_perdas = st.slider("Fator de Perdas/Manutenção (d)", 0.50, 0.95, 0.80, step=0.05)

    st.markdown("---")
    st.subheader("📊 Resultados do Cálculo")
    
    area = comprimento * largura
    altura_util = pe_direito - 0.85
    k_indice = area / (altura_util * (comprimento + largura)) if altura_util > 0 else 0
    fluxo_total_necessario = (iluminancia * area) / (fator_utilizacao * fator_perdas)
    qtd_luminarias = int(-(-fluxo_total_necessario // fluxo)) if fluxo > 0 else 0
    potencia_total = qtd_luminarias * potencia
    densidade_potencia = potencia_total / area if area > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Área Total", f"{area:.2f} m²")
    col2.metric("Índice do Recinto (K)", f"{k_indice:.2f}")
    col3.metric("Luminárias Necessárias", f"{qtd_luminarias} un")
    col4.metric("Densidade de Potência", f"{densidade_potencia:.2f} W/m²")

    st.markdown("---")
    
    # Organização das estruturas de dados
    dados_cliente = {"nome": cli_nome, "doc": cli_doc, "endereco": cli_end}
    dados_prof = {"nome": prof_nome, "registro": prof_registro, "contato": prof_contato}
    dados_ambiente = {
        "nome": nome_ambiente, "comprimento": comprimento, "largura": largura,
        "pe_direito": pe_direito, "area": area, "atividade": tipo_atividade,
        "lux_req": iluminancia, "k_indice": k_indice, "qtd_lum": qtd_luminarias,
        "pot_total": potencia_total, "densidade": densidade_potencia
    }
    
    # Geração do arquivo PDF em memória
    buffer_pdf = gerar_pdf(dados_cliente, dados_prof, dados_ambiente, logo_file=logo_upload)
    nome_sanitizado = nome_ambiente.replace(" ", "_")
    
    st.download_button(
        label="📄 Baixar Memorial de Cálculo em PDF",
        data=buffer_pdf,
        file_name=f"Memorial_Luminotecnico_{nome_sanitizado}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
