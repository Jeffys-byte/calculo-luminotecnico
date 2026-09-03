import streamlit as st
import pandas as pd
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import io
import math

# --- AUXILIARES PARA FORMATAÇÃO DO WORD ---
def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def format_table_header(row, col_widths=None):
    for idx, cell in enumerate(row.cells):
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(9.5)
        if col_widths and idx < len(col_widths):
            cell.width = col_widths[idx]

def format_table_rows(table, col_widths=None):
    for r_idx, row in enumerate(table.rows[1:]):
        bg_color = "F2F2F2" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell in enumerate(row.cells):
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.15
                for run in p.runs:
                    run.font.size = Pt(9.5)
            if col_widths and c_idx < len(col_widths):
                cell.width = col_widths[c_idx]

# --- FUNÇÃO DE GERAÇÃO DE WORD EM LOTE (.DOCX) ---
def gerar_docx_lote(dados_cliente, dados_prof, df_resultados, logo_file=None):
    doc = docx.Document()
    
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    if logo_file is not None:
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        logo_file.seek(0)
        p_logo.add_run().add_picture(logo_file, width=Inches(1.0))
        doc.add_paragraph()

    # Cabeçalho
    p_titulo = doc.add_paragraph()
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_titulo.paragraph_format.space_after = Pt(2)
    run1 = p_titulo.add_run("RELATÓRIO GERAL DE DIMENSIONAMENTO LUMINOTÉCNICO (EM LOTE)")
    run1.bold = True
    run1.font.size = Pt(14)
    run1.font.color.rgb = RGBColor(31, 78, 121)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(6)
    run_sub = p_sub.add_run(f"Cliente / Empreendimento: {dados_cliente['nome']}")
    run_sub.font.size = Pt(11)
    run_sub.bold = True

    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_info.paragraph_format.space_after = Pt(12)
    p_info.add_run(f"Engenheiro Responsável: {dados_prof['nome']} — {dados_prof['registro']}\n").bold = True
    p_info.add_run("Norma de Referência: NBR ISO/CIE 8995-1 (Iluminação de Ambientes de Trabalho)").italic = True

    doc.add_heading("1. Resumo Consolidado dos Ambientes", level=2)
    
    headers = ["Ambiente", "Área (m²)", "Meta (lx)", "Real (lx)", "Luminárias", "Pot. (W)", "Status"]
    col_widths = [Inches(1.8), Inches(0.9), Inches(0.9), Inches(0.9), Inches(1.0), Inches(0.9), Inches(1.2)]
    
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    hdr_cells = tbl.rows[0].cells
    for idx, h_text in enumerate(headers):
        hdr_cells[idx].text = h_text
    format_table_header(tbl.rows[0], col_widths)

    for _, row in df_resultados.iterrows():
        row_cells = tbl.add_row().cells
        row_cells[0].text = str(row['Ambiente'])
        row_cells[1].text = f"{row['Área (m²)']:.2f}"
        row_cells[2].text = f"{row['Meta (lx)']}"
        row_cells[3].text = f"{row['Real (lx)']:.2f}"
        row_cells[4].text = f"{row['Luminárias']} un"
        row_cells[5].text = f"{row['Pot. Total (W)']:.2f}"
        row_cells[6].text = "CONFORME" if row['Conforme'] else "NÃO CONFORME"
        
        for c_idx in range(1, len(headers)):
            row_cells[c_idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    format_table_rows(tbl, col_widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Detalhamento individual por ambiente
    doc.add_heading("2. Detalhamento Técnico por Ambiente", level=2)
    for _, r in df_resultados.iterrows():
        p_amb = doc.add_paragraph()
        p_amb.add_run(f"📌 Ambiente: {r['Ambiente']}").bold = True
        
        p_det = doc.add_paragraph()
        p_det.paragraph_format.left_indent = Inches(0.2)
        p_det.add_run(f"• Dimensões: {r['Comp (m)']:.2f}m × {r['Larg (m)']:.2f}m | Pé-Direito: {r['Pé-Direito (m)']:.2f}m\n")
        p_det.add_run(f"• Índice K: {r['Índice K']:.2f} | Fator Utilização (u): {r['Fator u']:.2f} | Depreciação (d): {r['Fator d']:.2f}\n")
        p_det.add_run(f"• Arranjo Espacial: {r['Linhas']} Linhas × {r['Colunas']} Colunas\n")
        p_det.add_run(f"• Espaçamentos: Eixo C = {r['Dist. C (m)']:.2f}m (Paredes: {r['Dist. Parede C (m)']:.2f}m) | Eixo L = {r['Dist. L (m)']:.2f}m (Paredes: {r['Dist. Parede L (m)']:.2f}m)\n")
        p_det.add_run(f"• Densidade de Potência (DPI): {r['DPI (W/m²)']:.2f} W/m²")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Luminotécnica", layout="wide")

st.title("⚡ Luminotécnica")
st.write("Dimensionamento Profissional e Gerador de Relatórios de Cálculo Luminotécnico.")

# Sidebar
st.sidebar.header("🎨 Personalização da Marca")
logo_upload = st.sidebar.file_uploader("Envie a Logo para o Relatório (PNG/JPG)", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.header("👨‍💻 Dados do Responsável Técnico")
prof_nome = st.sidebar.text_input("Nome do Profissional", "Jefferson Barcellos Borges")
prof_registro = st.sidebar.text_input("Registro (CREA / CFT)", "Engenheiro Eletricista")
prof_contato = st.sidebar.text_input("Contato / E-mail", "contato@empresa.com")

TABELA_NORMA = {
    "Dormitórios / Suítes (Residencial)": 200,
    "Salas de Estar / Jantar": 150,
    "Cozinhas / Banheiros": 300,
    "Escritórios - Trabalho Geral": 500,
    "Corredores e Áreas de Circulação": 100,
}

tab1, tab2 = st.tabs(["📐 Dimensionamento de Ambiente", "📋 Gerenciamento em Lote"])

with tab1:
    st.subheader("1. Identificação do Projeto e Recinto")
    col_c1, col_c2, col_c3 = st.columns(3)
    cli_nome = col_c1.text_input("Cliente / Empreendimento", "Projeto Residencial")
    nome_ambiente = col_c2.text_input("Nome / Identificação do Ambiente", "Quarto Suíte")
    tipo_atividade = col_c3.selectbox("Atividade / Norma (NBR ISO/CIE 8995-1)", list(TABELA_NORMA.keys()))

    st.markdown("---")
    st.subheader("2. Geometria e Parâmetros da Luminária")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**Geometria do Espaço**")
        comprimento = st.number_input("Comprimento C (m)", value=5.98, step=0.1)
        largura = st.number_input("Largura L (m)", value=4.70, step=0.1)
        pe_direito = st.number_input("Pé-Direito Total H (m)", value=2.80, step=0.1)
        hp = st.number_input("Altura do Plano de Trabalho hp (m)", value=0.75, step=0.05)
        hp_desc = st.number_input("Pendotamento / Descimento hp' (m)", value=0.00, step=0.05)

    with col_b:
        st.markdown("**Parâmetros Luminotécnicos**")
        lux_padrao = TABELA_NORMA[tipo_atividade]
        iluminancia_req = st.number_input("Iluminância Meta Requerida (lx)", value=lux_padrao, step=50)
        fluxo_lampada = st.number_input("Fluxo Luminoso da Luminária (lm)", value=1800, step=100)
        potencia_lampada = st.number_input("Potência Unitária da Luminária (W)", value=24, step=1)
        fator_u = st.slider("Fator de Utilização (u)", 0.10, 0.90, 0.50, step=0.01)
        fator_d = st.slider("Fator de Depreciação / Perdas (d)", 0.50, 0.95, 0.80, step=0.05)

    # --- CÁLCULOS TÉCNICOS ---
    area = comprimento * largura
    hu = pe_direito - hp - hp_desc
    hu = max(hu, 0.1)
    
    k_indice = (comprimento * largura) / (hu * (comprimento + largura))
    fluxo_req_teorico = (iluminancia_req * area) / (fator_u * fator_d)
    qtd_teorica = fluxo_req_teorico / fluxo_lampada if fluxo_lampada > 0 else 0
    qtd_real = math.ceil(qtd_teorica)
    
    fluxo_instalado = qtd_real * fluxo_lampada
    lux_real = (fluxo_instalado * fator_u * fator_d) / area if area > 0 else 0
    pot_total = qtd_real * potencia_lampada
    dpi = pot_total / area if area > 0 else 0
    conforme = lux_real >= iluminancia_req

    ratio = comprimento / largura if largura > 0 else 1
    colunas = max(1, round(math.sqrt(qtd_real / ratio)))
    linhas = max(1, math.ceil(qtd_real / colunas))
    
    dist_c = comprimento / linhas if linhas > 0 else 0
    dist_parede_c = dist_c / 2
    dist_l = largura / colunas if colunas > 0 else 0
    dist_parede_l = dist_l / 2

    dados_calculados = {
        "nome": nome_ambiente, "comp": comprimento, "larg": largura,
        "pe_direito": pe_direito, "hp": hp, "hp_desc": hp_desc,
        "area": area, "hu": hu, "lux_req": iluminancia_req,
        "fluxo": fluxo_lampada, "potencia": potencia_lampada,
        "k_indice": k_indice, "fator_u": fator_u, "fator_d": fator_d,
        "fluxo_req": fluxo_req_teorico, "qtd_teorica": qtd_teorica,
        "qtd_real": qtd_real, "fluxo_instalado": fluxo_instalado,
        "lux_real": lux_real, "pot_total": pot_total, "dpi": dpi,
        "conforme": conforme, "linhas": linhas, "colunas": colunas,
        "dist_c": dist_c, "dist_parede_c": dist_parede_c,
        "dist_l": dist_l, "dist_parede_l": dist_parede_l
    }

    st.markdown("---")
    st.subheader("📊 Resultados do Dimensionamento")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Área Total", f"{area:.2f} m²")
    col2.metric("Índice do Recinto (K)", f"{k_indice:.2f}")
    col3.metric("Luminárias Recomendadas", f"{qtd_real} un", f"Mínimo teórico: {qtd_teorica:.2f}")
    col4.metric("Iluminância Alcançada", f"{lux_real:.2f} lx", delta=f"{lux_real - iluminancia_req:+.2f} lx")

    if conforme:
        st.success(f"✅ **PROJETO CONFORME:** A iluminância calculada ({lux_real:.2f} lx) atende à exigência da NBR ISO/CIE 8995-1 ({iluminancia_req} lx).")
    else:
        st.warning(f"⚠️ **PROJETO NÃO CONFORME:** A iluminância calculada ({lux_real:.2f} lx) está abaixo da meta ({iluminancia_req} lx). Aumente a quantidade de luminárias ou o fluxo individual.")

    st.markdown("---")
    
    dados_cliente = {"nome": cli_nome}
    dados_prof = {"nome": prof_nome, "registro": prof_registro, "contato": prof_contato}
    nome_sanitizado = nome_ambiente.replace(" ", "_")
    
    # Gerar Word individual
    from docx import Document # type: ignore
    # (A função gerar_docx está disponível do contexto anterior, mas vamos usar a lógica direta ou redefinir se precisar)

# --- ABA DE GERENCIAMENTO EM LOTE ---
with tab2:
    st.subheader("📋 Planilha de Dimensionamento em Lote")
    st.write("Adicione ou edite os ambientes diretamente na tabela abaixo. O sistema calculará automaticamente os resultados para todos os cômodos de uma só vez.")

    # Dados padrão iniciais para a tabela em lote
    data_inicial = pd.DataFrame([
        {"Ambiente": "Sala de Estar", "Comprimento (m)": 6.0, "Largura (m)": 4.0, "Pé-Direito (m)": 2.8, "Meta Lux": 150, "Fluxo Lâmpada (lm)": 1800, "Potência (W)": 24, "Fator u": 0.5, "Fator d": 0.8},
        {"Ambiente": "Cozinha", "Comprimento (m)": 4.0, "Largura (m)": 3.0, "Pé-Direito (m)": 2.8, "Meta Lux": 300, "Fluxo Lâmpada (lm)": 2400, "Potência (W)": 30, "Fator u": 0.5, "Fator d": 0.8},
        {"Ambiente": "Quarto Principal", "Comprimento (m)": 4.5, "Largura (m)": 3.5, "Pé-Direito (m)": 2.8, "Meta Lux": 200, "Fluxo Lâmpada (lm)": 1800, "Potência (W)": 24, "Fator u": 0.5, "Fator d": 0.8},
        {"Ambiente": "Banheiro", "Comprimento (m)": 2.5, "Largura (m)": 2.0, "Pé-Direito (m)": 2.8, "Meta Lux": 300, "Fluxo Lâmpada (lm)": 1200, "Potência (W)": 15, "Fator u": 0.5, "Fator d": 0.8},
        {"Ambiente": "Corredor", "Comprimento (m)": 5.0, "Largura (m)": 1.5, "Pé-Direito (m)": 2.8, "Meta Lux": 100, "Fluxo Lâmpada (lm)": 900, "Potência (W)": 12, "Fator u": 0.4, "Fator d": 0.8},
    ])

    df_editado = st.data_editor(data_inicial, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 Processar e Gerar Relatório Consolidado em Lote", type="primary"):
        resultados_lote = []
        hp_padrao = 0.75

        for _, row in df_editado.iterrows():
            comp = float(row["Comprimento (m)"])
            larg = float(row["Largura (m)"])
            pe_dir = float(row["Pé-Direito (m)"])
            meta_lux = float(row["Meta Lux"])
            fluxo = float(row["Fluxo Lâmpada (lm)"])
            pot = float(row["Potência (W)"])
            u = float(row["Fator u"])
            d = float(row["Fator d"])

            area = comp * larg
            hu = max(pe_dir - hp_padrao, 0.1)
            k = (comp * larg) / (hu * (comp + larg))
            
            fluxo_req = (meta_lux * area) / (u * d)
            qtd_tec = fluxo_req / fluxo if fluxo > 0 else 0
            qtd_real = math.ceil(qtd_tec)
            
            fluxo_inst = qtd_real * fluxo
            lux_real = (fluxo_inst * u * d) / area if area > 0 else 0
            pot_tot = qtd_real * pot
            dpi = pot_tot / area if area > 0 else 0
            conforme = lux_real >= meta_lux

            ratio = comp / larg if larg > 0 else 1
            colunas = max(1, round(math.sqrt(qtd_real / ratio)))
            linhas = max(1, math.ceil(qtd_real / colunas))
            dist_c = comp / linhas if linhas > 0 else 0
            dist_l = larg / colunas if colunas > 0 else 0

            resultados_lote.append({
                "Ambiente": row["Ambiente"],
                "Área (m²)": area,
                "Comp (m)": comp,
                "Larg (m)": larg,
                "Pé-Direito (m)": pe_dir,
                "Meta (lx)": meta_lux,
                "Real (lx)": lux_real,
                "Luminárias": qtd_real,
                "Pot. Total (W)": pot_tot,
                "DPI (W/m²)": dpi,
                "Conforme": conforme,
                "Índice K": k,
                "Fator u": u,
                "Fator d": d,
                "Linhas": linhas,
                "Colunas": colunas,
                "Dist. C (m)": dist_c,
                "Dist. Parede C (m)": dist_c / 2,
                "Dist. L (m)": dist_l,
                "Dist. Parede L (m)": dist_l / 2
            })

        df_res = pd.DataFrame(resultados_lote)
        
        st.success("✅ Dimensionamento em lote concluído com sucesso!")
        st.dataframe(df_res[["Ambiente", "Área (m²)", "Meta (lx)", "Real (lx)", "Luminárias", "Pot. Total (W)", "Conforme"]], use_container_width=True)

        dados_cliente = {"nome": "Projeto Residencial / Lote"}
        dados_prof = {"nome": prof_nome, "registro": prof_registro, "contato": prof_contato}
        
        docx_lote_bytes = gerar_docx_lote(dados_cliente, dados_prof, df_res, logo_file=logo_upload)

        st.download_button(
            label="📥 Baixar Relatório Consolidado em Word (.DOCX)",
            data=docx_lote_bytes,
            file_name="Relatorio_Luminotecnico_Lote.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
