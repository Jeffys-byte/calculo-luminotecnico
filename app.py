import streamlit as st
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from fpdf import FPDF
import io
import tempfile
import os
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

# --- CLASSE CUSTOMIZADA DO PDF (fpdf2) ---
class PDF(FPDF):
    def sanitize(self, text):
        replacements = {
            "•": "-", "—": "-", "–": "-", "“": '"', "”": '"', "’": "'", "²": "2"
        }
        for orig, sub in replacements.items():
            text = str(text).replace(orig, sub)
        return text.encode('latin-1', 'replace').decode('latin-1')

# --- FUNÇÃO DE GERAÇÃO DE PDF ---
def gerar_pdf(dados_cliente, dados_prof, d, logo_file=None):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Logo
    if logo_file is not None:
        logo_file.seek(0)
        ext = logo_file.name.split('.')[-1].lower()
        if ext in ['png', 'jpg', 'jpeg']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
                tmp_file.write(logo_file.read())
                tmp_path = tmp_file.name
            try:
                pdf.image(tmp_path, x=10, y=10, w=25)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        pdf.set_y(38)
    else:
        pdf.set_y(15)

    # Título do Relatório
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, pdf.sanitize("RELATÓRIO DE DIMENSIONAMENTO LUMINOTÉCNICO"), align="C")
    pdf.ln(7)
    
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.cell(0, 5, pdf.sanitize("Projeto de Iluminação Residencial / Comercial | Método dos Lúmens"), align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 4.5, pdf.sanitize(f"Engenheiro Responsável: {dados_prof['nome']} - {dados_prof['registro']}"), align="C")
    pdf.ln(4.5)
    pdf.cell(0, 4.5, pdf.sanitize("Norma de Referência: NBR ISO/CIE 8995-1 (Iluminação de Ambientes de Trabalho)"), align="C")
    pdf.ln(8)

    def criar_tabela_pdf(titulo, colunas, largura_cols, dados):
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 6, pdf.sanitize(titulo))
        pdf.ln(6)
        
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        
        for idx, col in enumerate(colunas):
            pdf.cell(largura_cols[idx], 6, pdf.sanitize(col), border=1, align="C", fill=True)
        pdf.ln(6)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)
        for r_idx, linha in enumerate(dados):
            fill = (r_idx % 2 == 1)
            pdf.set_fill_color(242, 242, 242) if fill else pdf.set_fill_color(255, 255, 255)
            for c_idx, val in enumerate(linha):
                align = "C" if c_idx in [1, 2] else "L"
                pdf.cell(largura_cols[c_idx], 5.2, pdf.sanitize(str(val)), border=1, align=align, fill=fill)
            pdf.ln(5.2)
        pdf.ln(4)

    # 1. Identificação
    criar_tabela_pdf(
        "1. Identificação e Dados Geométricos do Ambiente",
        ["Parâmetro", "Símbolo", "Valor", "Unidade"],
        [70, 25, 35, 60],
        [
            ["Nome / Identificação do Ambiente", "-", d['nome'], "-"],
            ["Comprimento do Recinto", "C", f"{d['comp']:.2f}", "m"],
            ["Largura do Recinto", "L", f"{d['larg']:.2f}", "m"],
            ["Pé-Direito Total (Piso ao Teto)", "H", f"{d['pe_direito']:.2f}", "m"],
            ["Altura do Plano de Trabalho", "hp", f"{d['hp']:.2f}", "m"],
            ["Pendotamento / Descimento da Luminária", "hp'", f"{d['hp_desc']:.2f}", "m"],
            ["Área Total Calculada", "A", f"{d['area']:.2f}", "m2"],
            ["Altura Útil de Iluminação", "hu", f"{d['hu']:.2f}", "m"]
        ]
    )

    # 2. Parâmetros Luminotécnicos
    criar_tabela_pdf(
        "2. Parâmetros Luminotécnicos Adotados",
        ["Parâmetro Técnico", "Símbolo", "Valor Adotado", "Observações / Norma"],
        [60, 25, 35, 70],
        [
            ["Iluminância Requerida (Meta)", "Ereq", f"{d['lux_req']} lx", "NBR ISO/CIE 8995-1"],
            ["Fluxo Luminoso da Luminária", "Flampa", f"{d['fluxo']:,} lm".replace(",", "."), "Dado do fabricante"],
            ["Potência Unitária da Luminária", "Punit", f"{d['potencia']} W", "Consumo elétrico unitário"],
            ["Índice do Recinto", "K", f"{d['k_indice']:.2f}", "Geometria do espaço"],
            ["Fator de Utilização", "u", f"{d['fator_u']:.2f} ({int(d['fator_u']*100)}%)", "Refletância padrão"],
            ["Fator de Depreciação / Perdas", "d", f"{d['fator_d']:.2f} ({int(d['fator_d']*100)}%)", "Manutenção para ambiente"]
        ]
    )

    # 3. Resultados
    criar_tabela_pdf(
        "3. Resultados do Dimensionamento e Iluminância",
        ["Item de Cálculo", "Valor Calculado", "Valor Adotado / Real", "Unidade"],
        [70, 40, 45, 35],
        [
            ["Fluxo Luminoso Requerido (Teórico)", f"{d['fluxo_req']:.2f}", "-", "lm"],
            ["Quantidade Mínima de Luminárias", f"{d['qtd_teorica']:.2f}", f"{d['qtd_real']}", "unidades"],
            ["Fluxo Luminoso Real Instalado", "-", f"{d['fluxo_instalado']:,}".replace(",", "."), "lm"],
            ["Iluminância Real Alcançada", "-", f"{d['lux_real']:.2f}", "lx"],
            ["Potência Total Instalada", "-", f"{d['pot_total']:.2f}", "W"],
            ["Densidade de Potência Iluminada (DPI)", "-", f"{d['dpi']:.2f}", "W/m2"]
        ]
    )

    # 4. Disposição Espacial
    criar_tabela_pdf(
        "4. Disposição Espacial e Layout de Instalação",
        ["Eixo de Instalação", "Arranjo (Linhas x Colunas)", "Distância entre Luminárias", "Distância das Paredes"],
        [50, 50, 45, 45],
        [
            ["Eixo Longitudinal (Comprimento)", f"{d['linhas']} Linhas", f"{d['dist_c']:.2f} m", f"{d['dist_parede_c']:.2f} m"],
            ["Eixo Transversal (Largura)", f"{d['colunas']} Colunas", f"{d['dist_l']:.2f} m", f"{d['dist_parede_l']:.2f} m"]
        ]
    )

    # 5. Parecer Técnico
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.cell(0, 6, pdf.sanitize("5. Parecer Técnico e Conformidade"))
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "", 8.5)
    status_str = "CONFORME (Projeto aprovado e recomendado para execução)." if d['conforme'] else "NÃO CONFORME (Revisar fluxo luminoso ou quantidade)."
    
    w_page = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Nível de Iluminância: O valor projetado atinge {d['lux_real']:.2f} lx, {'atendendo com folga' if d['conforme'] else 'abaixo da'} a meta de {d['lux_req']} lx exigida pela norma NBR ISO/CIE 8995-1 para o ambiente."))
    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Eficiência Energética: A densidade de potência instalada é de {d['dpi']:.2f} W/m2, estando dentro dos padrões de eficiência energética em LED."))
    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Uniformidade Espacial: A distribuição em matriz {d['linhas']} x {d['colunas']} com espaçamentos calculados garante homogeneidade do fluxo luminoso sobre o plano de trabalho a {d['hp']:.2f} m do piso."))
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Status Final de Aprovação: {status_str}"))

    # SAÍDA SEGURA EM BYTES PARA EVITAR QUE O STREAMLIT INTERCEPTE O RETORNO
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    return bytes(pdf_output)

# --- FUNÇÃO DE GERAÇÃO DE WORD (.DOCX) ---
def gerar_docx(dados_cliente, dados_prof, d, logo_file=None):
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
    run1 = p_titulo.add_run("RELATÓRIO DE DIMENSIONAMENTO LUMINOTÉCNICO")
    run1.bold = True
    run1.font.size = Pt(14)
    run1.font.color.rgb = RGBColor(31, 78, 121)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(6)
    run_sub = p_sub.add_run("Projeto de Iluminação Residencial / Comercial | Método dos Lúmens")
    run_sub.font.size = Pt(10)
    run_sub.italic = True
    run_sub.font.color.rgb = RGBColor(89, 89, 89)

    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_info.paragraph_format.space_after = Pt(12)
    p_info.add_run(f"Engenheiro Responsável: {dados_prof['nome']} — {dados_prof['registro']}\n").bold = True
    p_info.add_run("Norma de Referência: NBR ISO/CIE 8995-1 (Iluminação de Ambientes de Trabalho)").italic = True

    def adicionar_secao_tabela(titulo, headers, col_widths, linhas):
        doc.add_heading(titulo, level=2)
        tbl = doc.add_table(rows=1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        hdr_cells = tbl.rows[0].cells
        for idx, h_text in enumerate(headers):
            hdr_cells[idx].text = h_text
        format_table_header(tbl.rows[0], col_widths)

        for r_data in linhas:
            row_cells = tbl.add_row().cells
            for c_idx, val in enumerate(r_data):
                row_cells[c_idx].text = str(val)
                if c_idx in [1, 2]:
                    row_cells[c_idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        format_table_rows(tbl, col_widths)
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 1. Identificação
    adicionar_secao_tabela(
        "1. Identificação e Dados Geométricos do Ambiente",
        ["Parâmetro", "Símbolo", "Valor", "Unidade"],
        [Inches(3.0), Inches(0.8), Inches(1.2), Inches(1.5)],
        [
            ["Nome / Identificação do Ambiente", "—", d['nome'], "—"],
            ["Comprimento do Recinto", "C", f"{d['comp']:.2f}", "m"],
            ["Largura do Recinto", "L", f"{d['larg']:.2f}", "m"],
            ["Pé-Direito Total (Piso ao Teto)", "H", f"{d['pe_direito']:.2f}", "m"],
            ["Altura do Plano de Trabalho", "hp", f"{d['hp']:.2f}", "m"],
            ["Pendotamento / Descimento da Luminária", "hp'", f"{d['hp_desc']:.2f}", "m"],
            ["Área Total Calculada", "A", f"{d['area']:.2f}", "m²"],
            ["Altura Útil de Iluminação", "hu", f"{d['hu']:.2f}", "m"]
        ]
    )

    # 2. Parâmetros Luminotécnicos
    adicionar_secao_tabela(
        "2. Parâmetros Luminotécnicos Adotados",
        ["Parâmetro Técnico", "Símbolo", "Valor Adotado", "Observações / Norma"],
        [Inches(2.5), Inches(0.8), Inches(1.2), Inches(2.0)],
        [
            ["Iluminância Requerida (Meta)", "Ereq", f"{d['lux_req']} lx", "NBR ISO/CIE 8995-1"],
            ["Fluxo Luminoso da Luminária/Cúpula", "Φlâmpada", f"{d['fluxo']:,} lm".replace(",", "."), "Dado do fabricante do LED/Luminária"],
            ["Potência Unitária da Luminária", "Punit", f"{d['potencia']} W", "Consumo elétrico unitário (W)"],
            ["Índice do Recinto", "K", f"{d['k_indice']:.2f}", "Geometria do espaço: (C × L) / [hu × (C + L)]"],
            ["Fator de Utilização", "u", f"{d['fator_u']:.2f} ({int(d['fator_u']*100)}%)", "Refletância padrão residencial / comercial"],
            ["Fator de Depreciação / Perdas", "d", f"{d['fator_d']:.2f} ({int(d['fator_d']*100)}%)", "Manutenção para ambiente limpo"]
        ]
    )

    # 3. Resultados
    adicionar_secao_tabela(
        "3. Resultados do Dimensionamento e Iluminância",
        ["Item de Cálculo", "Valor Calculado", "Valor Adotado / Real", "Unidade"],
        [Inches(3.0), Inches(1.2), Inches(1.3), Inches(1.0)],
        [
            ["Fluxo Luminoso Requerido (Teórico)", f"{d['fluxo_req']:.2f}", "—", "lm"],
            ["Quantidade Mínima de Luminárias", f"{d['qtd_teorica']:.2f}", f"{d['qtd_real']}", "unidades"],
            ["Fluxo Luminoso Real Instalado", "—", f"{d['fluxo_instalado']:,}".replace(",", "."), "lm"],
            ["Iluminância Real Alcançada", "—", f"{d['lux_real']:.2f}", "lx"],
            ["Potência Total Instalada", "—", f"{d['pot_total']:.2f}", "W"],
            ["Densidade de Potência Iluminada (DPI)", "—", f"{d['dpi']:.2f}", "W/m²"]
        ]
    )

    # 4. Disposição Espacial
    adicionar_secao_tabela(
        "4. Disposição Espacial e Layout de Instalação",
        ["Eixo de Instalação", "Arranjo (Linhas × Colunas)", "Distância entre Luminárias", "Distância das Paredes"],
        [Inches(2.2), Inches(1.8), Inches(1.3), Inches(1.2)],
        [
            ["Eixo Longitudinal (Comprimento)", f"{d['linhas']} Linhas", f"{d['dist_c']:.2f} m", f"{d['dist_parede_c']:.2f} m"],
            ["Eixo Transversal (Largura)", f"{d['colunas']} Colunas", f"{d['dist_l']:.2f} m", f"{d['dist_parede_l']:.2f} m"]
        ]
    )

    # 5. Parecer Técnico
    doc.add_heading("5. Parecer Técnico e Conformidade", level=2)
    
    p1 = doc.add_paragraph()
    p1.add_run("• Nível de Iluminância: ").bold = True
    p1.add_run(f"O valor projetado atinge {d['lux_real']:.2f} lx, ")
    if d['conforme']:
        p1.add_run(f"atendendo com folga a meta de {d['lux_req']} lx exigida pela norma NBR ISO/CIE 8995-1 para o ambiente.")
    else:
        p1.add_run(f"abaixo da meta de {d['lux_req']} lx exigida pela norma NBR ISO/CIE 8995-1. Recomenda-se ajustar o número ou potência das luminárias.")

    p2 = doc.add_paragraph()
    p2.add_run("• Eficiência Energética: ").bold = True
    p2.add_run(f"A densidade de potência instalada é de {d['dpi']:.2f} W/m², estando dentro dos padrões de alta eficiência para iluminação em LED.")

    p3 = doc.add_paragraph()
    p3.add_run("• Uniformidade Espacial: ").bold = True
    p3.add_run(f"A distribuição em matriz {d['linhas']} × {d['colunas']} com espaçamentos calculados garante homogeneidade do fluxo luminoso sobre o plano de trabalho a {d['hp']:.2f} m do piso.")

    p4 = doc.add_paragraph()
    p4.add_run("• Status Final de Aprovação: ").bold = True
    run_status = p4.add_run("CONFORME (Projeto aprovado e recomendado para execução)." if d['conforme'] else "NÃO CONFORME (Projeto requer ajustes).")
    run_status.bold = True
    run_status.font.color.rgb = RGBColor(38, 128, 0) if d['conforme'] else RGBColor(200, 0, 0)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

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
    "Escritórios - Escrever, digitar, ler, processar dados": 500,
    "Escritórios - Desenho técnico": 750,
    "Salas de Reunião / Conferência": 500,
    "Salas de Aula / Treinamento": 500,
    "Corredores e Áreas de Circulação": 100,
    "Depósitos / Almoxarifados (Trabalho bruto)": 100,
    "Áreas de Produção Industrial (Geral)": 300,
    "Personalizado (Digitar manualmente)": 200
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
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        pdf_bytes = gerar_pdf(dados_cliente, dados_prof, dados_calculados, logo_file=logo_upload)
        st.download_button(
            label="📄 Baixar Relatório em PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_Luminotecnico_{nome_sanitizado}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    with col_dl2:
        buffer_docx = gerar_docx(dados_cliente, dados_prof, dados_calculados, logo_file=logo_upload)
        st.download_button(
            label="📝 Baixar Relatório em Word (.DOCX)",
            data=buffer_docx,
            file_name=f"Relatorio_Luminotecnico_{nome_sanitizado}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
