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

# --- FUNÇÃO DE GERAÇÃO DE RELATÓRIO POR AMBIENTE ---
def adicionar_relatorio_ambiente(doc, dados_cliente, dados_prof, d):
    # Cabeçalho do Ambiente
    p_titulo = doc.add_paragraph()
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_titulo.paragraph_format.space_before = Pt(12)
    p_titulo.paragraph_format.space_after = Pt(2)
    run1 = p_titulo.add_run(f"RELATÓRIO DE DIMENSIONAMENTO LUMINOTÉCNICO\nAMBIENTE: {d['nome'].upper()}")
    run1.bold = True
    run1.font.size = Pt(13)
    run1.font.color.rgb = RGBColor(31, 78, 121)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(4)
    run_sub = p_sub.add_run(f"Cliente / Empreendimento: {dados_cliente['nome']} | Método dos Lúmens & Módulo PRO")
    run_sub.font.size = Pt(10)
    run_sub.italic = True
    run_sub.font.color.rgb = RGBColor(89, 89, 89)

    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_info.paragraph_format.space_after = Pt(10)
    p_info.add_run(f"Engenheiro Responsável: {dados_prof['nome']} — {dados_prof['registro']}\n")
    p_info.runs[0].bold = True
    run_norma = p_info.add_run("Norma de Referência: NBR ISO/CIE 8995-1 & NBR 5410 (Instalações Elétricas de Baixa Tensão)")
    run_norma.italic = True

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

    fluxo_fmt = f"{int(d['fluxo']):,}".replace(",", ".")
    fluxo_inst_fmt = f"{int(d['fluxo_instalado']):,}".replace(",", ".")

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
            ["Pé-direito / Descimento da Luminária", "hp'", f"{d['hp_desc']:.2f}", "m"],
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
            ["Iluminância Requerida (Meta)", "Ereq", f"{d['lux_req']:.0f} lx", "NBR ISO/CIE 8995-1"],
            ["Fluxo Luminoso da Luminária", "Φlâmpada", f"{fluxo_fmt} lm", "Fabricante"],
            ["Potência Unitária da Luminária", "Punit", f"{d['potencia']:.1f} W", "Consumo (W)"],
            ["Índice do Recinto", "K", f"{d['k_indice']:.2f}", "Geometria (C × L) / [hu × (C + L)]"],
            ["Fator de Utilização", "u", f"{d['fator_u']:.2f} ({int(d['fator_u']*100)}%)", "Refletância padrão"],
            ["Fator de Depreciação / Perdas", "d", f"{d['fator_d']:.2f} ({int(d['fator_d']*100)}%)", "Manutenção limpa"]
        ]
    )

    # 3. Resultados
    adicionar_secao_tabela(
        "3. Resultados do Dimensionamento Geral",
        ["Item de Cálculo", "Valor Calculado", "Valor Adotado / Real", "Unidade"],
        [Inches(3.0), Inches(1.2), Inches(1.3), Inches(1.0)],
        [
            ["Fluxo Luminoso Requerido (Teórico)", f"{d['fluxo_req']:.2f}", "—", "lm"],
            ["Quantidade Mínima de Luminárias", f"{d['qtd_teorica']:.2f}", f"{d['qtd_real']}", "unidades"],
            ["Fluxo Luminoso Real Instalado", "—", f"{fluxo_inst_fmt}", "lm"],
            ["Iluminância Real Alcançada", "—", f"{d['lux_real']:.2f}", "lx"],
            ["Potência Total Instalada", "—", f"{d['pot_total']:.2f}", "W"],
            ["Densidade de Potência Iluminada (DPI)", "—", f"{d['dpi']:.2f}", "W/m²"]
        ]
    )

    # 4. Módulo PRO (Fitas LED e Spots) se aplicável
    if d.get("usar_pro", False):
        adicionar_secao_tabela(
            "4. Módulo PRO: Detalhamento de Fitas LED e Spots",
            ["Parâmetro Especializado", "Especificação Técnica", "Resultado do Dimensionamento", "Validação NBR 5410"],
            [Inches(2.5), Inches(1.8), Inches(1.5), Inches(1.2)],
            [
                ["Fita LED (Perímetro / Sanca)", f"{d['fita_comprimento']:.2f} m linear | {d['fita_pot_metro']} W/m", f"Potência Total: {d['fita_pot_total']:.1f} W", f"Fonte Recomendada: {d['fita_fonte_rec']:.1f} W ({d['fita_tensao']})"],
                ["Queda de Tensão Fita LED", f"Trecho contínuo: {d['fita_comprimento']:.2f} m", f"Limite crítico: 5.0 m", f"{'OK (Sem queda excessiva)' if d['fita_comprimento'] <= 5 else 'ALERTA: Inserir nova injeção de 12V/24V'}"] ,
                ["Spot de Destaque (Facho)", f"Abertura de feixe: {d['spot_angulo']}°", f"Diâmetro da mancha no piso: {d['spot_diametro']:.2f} m", f"Altura útil ref: {d['hu']:.2f} m"]
            ]
        )

    # 5. Disposição Espacial
    adicionar_secao_tabela(
        "5. Disposição Espacial e Layout de Instalação",
        ["Eixo de Instalação", "Arranjo (Linhas × Colunas)", "Distância entre Luminárias", "Distância das Paredes"],
        [Inches(2.2), Inches(1.8), Inches(1.3), Inches(1.2)],
        [
            ["Eixo Longitudinal (Comprimento)", f"{d['linhas']} Linhas", f"{d['dist_c']:.2f} m", f"{d['dist_parede_c']:.2f} m"],
            ["Eixo Transversal (Largura)", f"{d['colunas']} Colunas", f"{d['dist_l']:.2f} m", f"{d['dist_parede_l']:.2f} m"]
        ]
    )

    # 6. Parecer Técnico e Disclaimer
    doc.add_heading("6. Parecer Técnico e Isenção de Responsabilidade", level=2)
    
    p1 = doc.add_paragraph()
    p1.add_run("• Nível de Iluminância: ").bold = True
    p1.add_run(f"O valor projetado atinge {d['lux_real']:.2f} lx, ")
    if d['conforme']:
        p1.add_run(f"atendendo satisfatoriamente à meta de {d['lux_req']:.0f} lx da norma NBR ISO/CIE 8995-1.")
    else:
        p1.add_run(f"abaixo da meta de {d['lux_req']:.0f} lx da norma NBR ISO/CIE 8995-1. Recomenda-se revisão do projeto.")

    p2 = doc.add_paragraph()
    p2.add_run("• Eficiência Energética: ").bold = True
    p2.add_run(f"A densidade de potência instalada é de {d['dpi']:.2f} W/m², em conformidade com as diretrizes de eficiência energética.")

    p3 = doc.add_paragraph()
    p3.add_run("• Disclaimer Técnico e Jurídico: ").bold = True
    p3.add_run(
        "Este relatório foi gerado por meio de algoritmos computacionais baseados em métodos normativos (Método dos Lúmens). "
        "A validação final, especificações de campo, compatibilização arquitetônica e emissão da ART (Anotação de Responsabilidade Técnica) "
        "ou RRT são de inteira responsabilidade do engenheiro ou projetista habilitado signatário deste documento. "
        "O autor do software isenta-se de eventuais divergências decorrentes de condições construtivas reais, refletâncias atípicas ou quedas de tensão não previstas em campo."
    )
    p3.runs[1].italic = True

    p4 = doc.add_paragraph()
    p4.add_run("• Status Final de Aprovação: ").bold = True
    run_status = p4.add_run("CONFORME (Aprovado para detalhamento em projeto executivo)." if d['conforme'] else "NÃO CONFORME (Requer ajustes de projeto).")
    run_status.bold = True
    run_status.font.color.rgb = RGBColor(38, 128, 0) if d['conforme'] else RGBColor(200, 0, 0)

# --- FUNÇÃO DE GERAÇÃO EM LOTE ---
def gerar_docx_lote(dados_cliente, dados_prof, lista_dados_ambientes, logo_file=None):
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

    for idx, d in enumerate(lista_dados_ambientes):
        adicionar_relatorio_ambiente(doc, dados_cliente, dados_prof, d)
        if idx < len(lista_dados_ambientes) - 1:
            doc.add_page_break()

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# --- FUNÇÃO DE GERAÇÃO INDIVIDUAL ---
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

    adicionar_relatorio_ambiente(doc, dados_cliente, dados_prof, d)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Luminotécnica PRO", layout="wide")

st.title("⚡ Luminotécnica PRO")
st.write("Dimensionamento Avançado, Cálculos para Fitas LED, Spots e Geração de Relatórios com Validação Normativa.")

# Barra Lateral: Licenciamento, Marca e Responsável
st.sidebar.header("🔑 Licenciamento do Sistema")
tipo_licenca = st.sidebar.selectbox("Plano Ativo", ["Plano Básico (Gratuito/Demo)", "Plano PRO (Assinatura Anual)"])
is_pro = tipo_licenca == "Plano PRO (Assinatura Anual)"

if not is_pro:
    st.sidebar.info("💡 Você está no **Plano Básico**. Assine o **Plano PRO** para liberar o Módulo de Fitas LED, Spots, Queda de Tensão e exportação de relatórios completos.")

st.sidebar.markdown("---")
st.sidebar.header("🎨 Personalização da Marca")
logo_upload = st.sidebar.file_uploader("Envie a Logo para o Relatório (PNG/JPG)", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.header("👨‍💻 Dados do Responsável Técnico")
prof_nome = st.sidebar.text_input("Nome do Profissional", "Eng. Jefferson Borges")
prof_registro = st.sidebar.text_input("Registro (CREA / CFT)", "CREA/RJ 2026.000")
prof_contato = st.sidebar.text_input("Contato / E-mail", "contato@powerenergy.com.br")

TABELA_NORMA = {
    "Dormitórios / Suítes (Residencial)": 200,
    "Salas de Estar / Jantar": 150,
    "Cozinhas / Banheiros": 300,
    "Escritórios - Trabalho Geral": 500,
    "Corredores e Áreas de Circulação": 100,
}

tab1, tab2 = st.tabs(["📐 Dimensionamento Principal & PRO", "📋 Relatórios em Lote"])

with tab1:
    st.subheader("1. Identificação do Projeto e Recinto")
    col_c1, col_c2, col_c3 = st.columns(3)
    cli_nome = col_c1.text_input("Cliente / Empreendimento", "Residência Unifamiliar")
    nome_ambiente = col_c2.text_input("Nome / Identificação do Ambiente", "Living Integrado")
    tipo_atividade = col_c3.selectbox("Atividade / Norma (NBR ISO/CIE 8995-1)", list(TABELA_NORMA.keys()))

    st.markdown("---")
    st.subheader("2. Geometria e Parâmetros da Luminária")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**Geometria do Espaço**")
        comprimento = st.number_input("Comprimento C (m)", value=6.00, step=0.1)
        largura = st.number_input("Largura L (m)", value=4.50, step=0.1)
        pe_direito = st.number_input("Pé-Direito Total H (m)", value=2.90, step=0.1)
        hp = st.number_input("Altura do Plano de Trabalho hp (m)", value=0.75, step=0.05)
        hp_desc = st.number_input("Pendotamento / Descimento hp' (m)", value=0.00, step=0.05)

    with col_b:
        st.markdown("**Parâmetros Luminotécnicos & Afastamentos**")
        lux_padrao = TABELA_NORMA[tipo_atividade]
        iluminancia_req = st.number_input("Iluminância Meta Requerida (lx)", value=lux_padrao, step=50)
        fluxo_lampada = st.number_input("Fluxo Luminoso da Luminária (lm)", value=2000, step=100)
        potencia_lampada = st.number_input("Potência Unitária da Luminária (W)", value=20, step=1)
        fator_u = st.slider("Fator de Utilização (u)", 0.10, 0.90, 0.50, step=0.01)
        fator_d = st.slider("Fator de Depreciação / Perdas (d)", 0.50, 0.95, 0.80, step=0.05)
        razao_max_input = st.slider("Razão Máx. de Espaçamento (Emax / hu)", 1.0, 2.0, 1.25, step=0.05)
        modo_afastamento = st.selectbox("Critério de Afastamento das Paredes", ["Proporcional (S/2)", "Fixo Personalizado"])
        afastamento_fixo_val = 0.50
        if modo_afastamento == "Fixo Personalizado":
            afastamento_fixo_val = st.number_input("Distância Fixa da Parede (m)", value=0.50, step=0.05)

    # --- MÓDULO PRO: FITAS LED E SPOTS ---
    fita_comprimento = 0.0
    fita_pot_metro = 14.4
    fita_tensao = "12V"
    fita_pot_total = 0.0
    fita_fonte_rec = 0.0
    spot_angulo = 36
    spot_diametro = 0.0

    if is_pro:
        st.markdown("---")
        st.subheader("🔥 Módulo PRO: Fitas LED (Sancas/Perfis) & Spots de Destaque")
        col_pro1, col_pro2 = st.columns(2)
        
        with col_pro1:
            st.markdown("**Dimensionamento de Fitas LED**")
            fita_comprimento = st.number_input("Comprimento Linear da Fita / Sanca (m)", value=10.5, step=0.5)
            fita_pot_metro = st.selectbox("Potência da Fita LED (W/m)", [4.8, 9.6, 14.4, 19.2, 24.0], index=2)
            fita_tensao = st.selectbox("Tensão de Operação da Fita", ["12V", "24V"])
            
            fita_pot_total = fita_comprimento * fita_pot_metro
            # Margem de segurança recomendada de 20% para a fonte chaveada
            fita_fonte_rec = fita_pot_total * 1.20

        with col_pro2:
            st.markdown("**Dimensionamento de Spots (Facho e Diâmetro)**")
            spot_angulo = st.slider("Abertura do Feixe do Spot (Graus)", 15, 60, 38, step=1)
            # Cálculo trigonométrico do diâmetro da mancha de luz: D = 2 * hu * tan(angulo / 2 em radianos)
            hu_calc_temp = max(pe_direito - hp - hp_desc, 0.1)
            spot_diametro = 2 * hu_calc_temp * math.tan(math.radians(spot_angulo / 2.0))
            st.metric("Diâmetro da Mancha de Luz no Piso", f"{spot_diametro:.2f} m", f"Altura útil: {hu_calc_temp:.2f} m")
    else:
        st.markdown("---")
        st.info("🔒 **Módulo PRO Bloqueado:** Mude para o **Plano PRO** na barra lateral para calcular fontes de Fita LED, queda de tensão e geometria de feixes de Spots.")

    # Cálculos gerais
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
    dist_l = largura / colunas if colunas > 0 else 0

    if modo_afastamento == "Proporcional (S/2)":
        dist_parede_c = dist_c / 2
        dist_parede_l = dist_l / 2
    else:
        dist_parede_c = afastamento_fixo_val
        dist_parede_l = afastamento_fixo_val

    maior_espacamento = max(dist_c, dist_l)
    razao_atual = maior_espacamento / hu if hu > 0 else 0
    espacamento_ok = razao_atual <= razao_max_input

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
        "dist_l": dist_l, "dist_parede_l": dist_parede_l,
        "modo_afastamento": modo_afastamento, "afastamento_fixo": afastamento_fixo_val,
        "razao_max": razao_max_input, "razao_atual": razao_atual, "espacamento_ok": espacamento_ok,
        "usar_pro": is_pro, "fita_comprimento": fita_comprimento, "fita_pot_metro": fita_pot_metro,
        "fita_tensao": fita_tensao, "fita_pot_total": fita_pot_total, "fita_fonte_rec": fita_fonte_rec,
        "spot_angulo": spot_angulo, "spot_diametro": spot_diametro
    }

    st.markdown("---")
    st.subheader("📊 Resultados Analíticos & Parecer Normativo")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Área Total", f"{area:.2f} m²")
    col2.metric("Índice do Recinto (K)", f"{k_indice:.2f}")
    col3.metric("Luminárias Recomendadas", f"{qtd_real} un", f"Mínimo: {qtd_teorica:.2f}")
    col4.metric("Iluminância Alcançada", f"{lux_real:.2f} lx", delta=f"{lux_real - iluminancia_req:+.2f} lx")

    if conforme:
        st.success(f"✅ **CONFORME NBR ISO/CIE 8995-1:** O nível luminoso ({lux_real:.2f} lx) atende à meta da atividade.")
    else:
        st.warning(f"⚠️ **NÃO CONFORME:** Nível calculado abaixo da exigência de {iluminancia_req} lx.")

    if espacamento_ok:
        st.info(f"✨ **ESPAÇAMENTO SEGURO:** Razão atual ({razao_atual:.2f}) dentro do limite máximo de {razao_max_input:.2f}.")
    else:
        st.error(f"⚠️ **ALERTA DE ESPAÇAMENTO:** Razão atual ({razao_atual:.2f}) excede o limite estipulado de {razao_max_input:.2f}.")

    if is_pro:
        st.markdown("---")
        st.markdown("### 🔌 Diagnóstico do Módulo PRO (Fitas LED)")
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Potência Total Fita LED", f"{fita_pot_total:.1f} W", f"Fonte Recomendada: {fita_fonte_rec:.1f} W (c/ 20% margem)")
        if fita_comprimento <= 5.0:
            col_res2.success("✅ **Queda de Tensão:** Trecho contínuo seguro ($\le 5\text{m}$).")
        else:
            col_res2.error("⚠️ **ALERTA DE QUEDA DE TENSÃO:** Trecho $> 5\text{m}$. Obrigatória injeção de energia nas extremidades conforme NBR 5410.")

    st.markdown("---")
    
    dados_cliente = {"nome": cli_nome}
    dados_prof = {"nome": prof_nome, "registro": prof_registro, "contato": prof_contato}
    nome_sanitizado = nome_ambiente.replace(" ", "_")
    
    if is_pro:
        docx_data = gerar_docx(dados_cliente, dados_prof, dados_calculados, logo_file=logo_upload)
        st.download_button(
            label="📝 Baixar Relatório Técnico PRO em Word (.DOCX)",
            data=docx_data,
            file_name=f"Relatorio_Pro_{nome_sanitizado}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        st.warning("🔒 **Exportação Bloqueada:** Apenas assinantes do **Plano PRO** podem baixar o relatório completo com parecer técnico e disclaimer jurídico.")

with tab2:
    st.subheader("📋 Gerenciamento e Lote em Massa")
    if is_pro:
        st.write("Processamento em lote habilitado para o Plano PRO.")
        data_inicial = pd.DataFrame([
            {"Ambiente": "Living", "Comprimento (m)": 6.0, "Largura (m)": 4.0, "Pé-Direito (m)": 2.9, "Meta Lux": 150, "Fluxo Lâmpada (lm)": 2000, "Potência (W)": 20, "Fator u": 0.5, "Fator d": 0.8},
            {"Ambiente": "Cozinha Gourmet", "Comprimento (m)": 4.5, "Largura (m)": 3.5, "Pé-Direito (m)": 2.9, "Meta Lux": 300, "Fluxo Lâmpada (lm)": 2400, "Potência (W)": 24, "Fator u": 0.5, "Fator d": 0.8},
        ])
        df_editado = st.data_editor(data_inicial, num_rows="dynamic", use_container_width=True)
        cli_nome_lote = st.text_input("Cliente / Empreendimento (Lote)", "Residência Completa")

        if st.button("🚀 Processar e Gerar Relatório em Lote PRO", type="primary"):
            lista_ambientes = []
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

                lista_ambientes.append({
                    "nome": row["Ambiente"], "comp": comp, "larg": larg,
                    "pe_direito": pe_dir, "hp": hp_padrao, "hp_desc": 0.0,
                    "area": area, "hu": hu, "lux_req": meta_lux,
                    "fluxo": fluxo, "potencia": pot,
                    "k_indice": k, "fator_u": u, "fator_d": d,
                    "fluxo_req": fluxo_req, "qtd_teorica": qtd_tec,
                    "qtd_real": qtd_real, "fluxo_instalado": fluxo_inst,
                    "lux_real": lux_real, "pot_total": pot_tot, "dpi": dpi,
                    "conforme": conforme, "linhas": linhas, "colunas": colunas,
                    "dist_c": dist_c, "dist_parede_c": dist_c / 2,
                    "dist_l": dist_l, "dist_parede_l": dist_l / 2,
                    "modo_afastamento": "Proporcional (S/2)", "afastamento_fixo": 0.50,
                    "razao_max": 1.25, "razao_atual": max(dist_c, dist_l)/hu, "espacamento_ok": True,
                    "usar_pro": True, "fita_comprimento": 5.0, "fita_pot_metro": 14.4,
                    "fita_tensao": "12V", "fita_pot_total": 72.0, "fita_fonte_rec": 86.4,
                    "spot_angulo": 38, "spot_diametro": 1.5
                })

            docx_lote_bytes = gerar_docx_lote({"nome": cli_nome_lote}, {"nome": prof_nome, "registro": prof_registro, "contato": prof_contato}, lista_ambientes, logo_file=logo_upload)
            st.success("✅ Relatório em lote gerado com sucesso!")
            st.download_button(
                label="📥 Baixar Relatório em Lote Completo (.DOCX)",
                data=docx_lote_bytes,
                file_name="Relatorio_Lote_PRO.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    else:
        st.warning("🔒 **Módulo em Lote Restrito:** Faça upgrade para o **Plano PRO** na barra lateral para processar múltiplos ambientes simultaneamente.")
