import streamlit as st
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- FUNÇÃO DE GERAÇÃO DO DOCUMENTO EM MEMÓRIA ---
def gerar_documento_docx(nome_ambiente, comprimento, largura, pe_direito, iluminancia_requerida, fluxo_lampada, potencia_lampada, logo_file=None):
    doc = docx.Document()
    
    # Se o usuário enviou uma logo, insere no topo do documento
    if logo_file is not None:
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Reseta o ponteiro do arquivo enviado para garantir a leitura correta
        logo_file.seek(0)
        # Adiciona a imagem com largura ajustada para 2 polegadas
        p_logo.add_run().add_picture(logo_file, width=Inches(2.0))
        doc.add_paragraph()  # Linha em branco para espaçamento

    # Título
    p_titulo = doc.add_paragraph()
    run_titulo = p_titulo.add_run(f"MEMORIAL DE CÁLCULO LUMINOTÉCNICO\n{nome_ambiente.upper()}")
    run_titulo.bold = True
    run_titulo.font.size = Pt(16)
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Cálculos
    area = comprimento * largura
    altura_util = pe_direito - 0.85
    k_indice = area / (altura_util * (comprimento + largura)) if altura_util > 0 else 0
    fator_utilizacao = 0.55
    fator_perdas = 0.80
    
    fluxo_total = (iluminancia_requerida * area) / (fator_utilizacao * fator_perdas)
    qtd_luminarias = int(-(-fluxo_total // fluxo_lampada)) if fluxo_lampada > 0 else 0
    potencia_total = qtd_luminarias * potencia_lampada
    densidade_potencia = potencia_total / area if area > 0 else 0
    
    # Seção de Dados
    doc.add_heading("1. Dados do Recinto e Iluminação", level=1)
    doc.add_paragraph(f"• Comprimento: {comprimento} m")
    doc.add_paragraph(f"• Largura: {largura} m")
    doc.add_paragraph(f"• Pé-Direito: {pe_direito} m")
    doc.add_paragraph(f"• Área Total: {area:.2f} m²")
    doc.add_paragraph(f"• Iluminância Alvo (NBR ISO/CIE 8995-1): {iluminancia_requerida} lx")
    
    # Seção de Resultados
    doc.add_heading("2. Resultados do Dimensionamento", level=1)
    doc.add_paragraph(f"• Índice do Recinto (K): {k_indice:.2f}")
    doc.add_paragraph(f"• Quantidade de Luminárias Requeridas: {qtd_luminarias} un")
    doc.add_paragraph(f"• Potência Instalada Total: {potencia_total} W")
    doc.add_paragraph(f"• Densidade de Potência: {densidade_potencia:.2f} W/m²")
    
    # Salva o arquivo Word em um buffer de memória
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Cálculo Luminotécnico NBR 8995-1", layout="wide")

st.title("⚡ Gerador de Memorial Luminotécnico")
st.write("Dimensionamento baseado na NBR ISO/CIE 8995-1 com exportação de relatórios.")

# Campo para o cliente anexar a própria logotipo
st.sidebar.header("🎨 Personalização da Marca")
logo_upload = st.sidebar.file_uploader("Envie a Logo para o Relatório (PNG, JPG)", type=["png", "jpg", "jpeg"])

if logo_upload is not None:
    st.sidebar.image(logo_upload, caption="Pré-visualização da Logo", use_container_width=True)

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
    st.subheader("Entrada de Dados do Ambiente")
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
    st.subheader("📊 Pré-visualização do Cálculo")
    
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
    
    # Geração do arquivo em memória para download (passando a logo se existir)
    buffer_doc = gerar_documento_docx(
        nome_ambiente=nome_ambiente,
        comprimento=comprimento,
        largura=largura,
        pe_direito=pe_direito,
        iluminancia_requerida=iluminancia,
        fluxo_lampada=fluxo,
        potencia_lampada=potencia,
        logo_file=logo_upload
    )
    
    nome_sanitizado = nome_ambiente.replace(" ", "_")
    
    st.download_button(
        label="📥 Baixar Memorial em Word (.DOCX)",
        data=buffer_doc,
        file_name=f"Memorial_Luminotecnico_{nome_sanitizado}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

with tab2:
    st.subheader("Geração de Múltiplos Memoriais")
    if "ambientes" not in st.session_state:
        st.session_state.ambientes = []

    with st.form("form_lote"):
        c1, c2, c3, c4 = st.columns(4)
        n = c1.text_input("Ambiente", "Corredor Principal")
        comp = c2.number_input("Comp. (m)", value=12.0)
        larg = c3.number_input("Larg. (m)", value=2.0)
        lux = c4.number_input("Lux (lx)", value=150)
        
        adicionar = st.form_submit_button("➕ Adicionar à Lista")
        if adicionar:
            st.session_state.ambientes.append({
                "nome": n, "comprimento": comp, "largura": larg, "pe_direito": 3.0,
                "iluminancia": lux, "fluxo": 3200, "potencia": 32
            })

    if st.session_state.ambientes:
        st.table(st.session_state.ambientes)
        
        for idx, item in enumerate(st.session_state.ambientes):
            buf = gerar_documento_docx(
                nome_ambiente=item["nome"],
                comprimento=item["comprimento"],
                largura=item["largura"],
                pe_direito=item["pe_direito"],
                iluminancia_requerida=item["iluminancia"],
                fluxo_lampada=item["fluxo"],
                potencia_lampada=item["potencia"],
                logo_file=logo_upload
            )
            st.download_button(
                label=f"📥 Baixar Memorial: {item['nome']} (.DOCX)",
                data=buf,
                file_name=f"Memorial_{item['nome'].replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"btn_lote_{idx}"
            )
