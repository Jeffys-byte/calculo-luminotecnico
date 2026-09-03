import streamlit as st
import pandas as pd
import io
import math
from datetime import datetime

# Importação segura do ReportLab para evitar tela preta caso o pacote falhe
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

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

# --- FUNÇÃO DE GERAÇÃO DE RELATÓRIO POR AMBIENTE (WORD) ---
def adicionar_relatorio_ambiente(doc, dados_cliente, dados_prof, d):
    data_emissao = datetime.now().strftime("%d/%m/%Y")

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
    p_info.add_run(f"Responsável Técnico: {dados_prof['nome']} ({dados_prof['titulo']}) — {dados_prof['registro']} | Data de Emissão: {data_emissao}\n")
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
            ["Fator de Utilização", "u", f"{d['fator_u']:.2f} ({int(d['fator_u']*100)}%)", "Refletância do ambiente"],
            ["Fator de Depreciação / Perdas", "d", f"{d['fator_d']:.2f} ({int(d['fator_d']*100)}%)", f"Manutenção: {d['desc_depreciacao']}"]
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

    # 4. Módulo PRO se aplicável
    if d.get("usar_pro", False):
        adicionar_secao_tabela(
            "4. Módulo PRO: Detalhamento de Fitas LED e Spots",
            ["Parâmetro Especializado", "Especificação Técnica", "Resultado do Dimensionamento", "Validação NBR 5410"],
            [Inches(2.5), Inches(1.8), Inches(1.5), Inches(1.2)],
            [
                ["Fita LED (Perímetro / Sanca)", f"{d['fita_comprimento']:.2f} m linear | {d['fita_pot_metro']} W/m", f"Potência Total: {d['fita_pot_total']:.1f} W", f"Fonte Recomendada: {d['fita_fonte_rec']:.1f} W ({d['fita_tensao']})"],
                ["Queda de Tensão Fita LED", f"Trecho contínuo: {d['fita_comprimento']:.2f} m", f"Limite crítico: 5.0 m", f"{'OK (Sem queda excessiva)' if d['fita_comprimento'] <= 5 else 'ALERTA: Inserir nova injeção de 12V/24V'}"],
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

    # 6. Parecer Técnico
    doc.add_heading("6. Parecer Técnico e Conclusão Normativa", level=2)
    
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
    p3.add_run("• Status Final de Aprovação: ").bold = True
    run_status = p3.add_run("CONFORME (Aprovado para detalhamento em projeto executivo)." if d['conforme'] else "NÃO CONFORME (Requer ajustes de projeto).")
    run_status.bold = True
    run_status.font.color.rgb = RGBColor(38, 128, 0) if d['conforme'] else RGBColor(200, 0, 0)

# --- FUNÇÃO DE GERAÇÃO EM LOTE (WORD) ---
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

# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Luminotécnica PRO", layout="wide")

st.title("⚡ Luminotécnica PRO")
st.write("Dimensionamento Avançado, Cálculos para Fitas LED, Spots e Geração de Relatórios com Validação Normativa.")

# Barra Lateral
st.sidebar.header("🔑 Licenciamento do Sistema")
tipo_licenca = st.sidebar.selectbox("Plano Ativo", ["Plano Básico (Gratuito/Demo)", "Plano PRO (Assinatura Anual)"])
is_pro = tipo_licenca == "Plano PRO (Assinatura Anual)"

if not is_pro:
    st.sidebar.info("💡 Você está no **Plano Básico**. Assine o **Plano PRO** para liberar o Módulo de Fitas LED, Spots, Queda de Tensão e adição de múltiplos ambientes.")

st.sidebar.markdown("---")
st.sidebar.header("🎨 Personalização da Marca")
logo_upload = st.sidebar.file_uploader("Envie a Logo para o Relatório (PNG/JPG)", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.header("👨‍💻 Dados do Responsável Técnico")

lista_categorias = [
    "Engenheiro(a) Eletricista",
    "Engenheiro(a) Civil",
    "Arquiteto(a) e Urbanista",
    "Técnico(a) em Eletrotecnica",
    "Designer de Interiores",
    "Outro (Personalizado)"
]
escolha_categoria = st.sidebar.selectbox("Categoria Profissional", lista_categorias)

if escolha_categoria == "Outro (Personalizado)":
    titulo_prof = st.sidebar.text_input("Digite o Título/Cargo", "Especialista em Iluminação")
else:
    titulo_prof = escolha_categoria

prof_nome = st.sidebar.text_input("Nome do Profissional", "", placeholder="Digite seu nome aqui")
prof_registro = st.sidebar.text_input("Registro (CREA / CAU / CFT)", "", placeholder="Ex: CREA/RJ 000.000")
prof_contato = st.sidebar.text_input("Contato / E-mail", "", placeholder="seu.email@empresa.com.br")

TABELA_NORMA = {
    "Dormitórios / Suítes (Residencial)": 200,
    "Salas de Estar / Jantar": 150,
    "Cozinhas / Banheiros": 300,
    "Escritórios - Trabalho Geral": 500,
    "Corredores e Áreas de Circulação": 100,
}

st.subheader("1. Identificação Geral do Projeto")
cli_nome = st.text_input("Cliente / Empreendimento", "", placeholder="Ex: Residência Unifamiliar ou Nome do Cliente")

st.markdown("---")
st.subheader("2. Gerenciamento de Ambientes do Projeto")

if "ambientes_lista" not in st.session_state:
    st.session_state["ambientes_lista"] = [{"id": 1, "nome": "Living Integrado"}]

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("➕ Adicionar Novo Ambiente", use_container_width=True):
        if is_pro or len(st.session_state["ambientes_lista"]) < 1:
            novo_id = max([a["id"] for a in st.session_state["ambientes_lista"]], default=0) + 1
            st.session_state["ambientes_lista"].append({"id": novo_id, "nome": f"Ambiente {novo_id}"})
            st.rerun()
        else:
            st.warning("⚠️ No Plano Básico é permitido apenas 1 ambiente. Faça upgrade para o Plano PRO para adicionar múltiplos ambientes.")

lista_calculos_ambientes = []

nomes_abas = [amb["nome"] for amb in st.session_state["ambientes_lista"]]
tabs = st.tabs(nomes_abas)

for idx, tab in enumerate(tabs):
    amb_atual = st.session_state["ambientes_lista"][idx]
    with tab:
        col_cab1, col_cab2 = st.columns([3, 1])
        with col_cab1:
            novo_nome = st.text_input("Nome do Ambiente", amb_atual["nome"], key=f"nome_amb_{amb_atual['id']}")
            st.session_state["ambientes_lista"][idx]["nome"] = novo_nome
        with col_cab2:
            if len(st.session_state["ambientes_lista"]) > 1:
                if st.button("🗑️ Remover", key=f"del_{amb_atual['id']}"):
                    st.session_state["ambientes_lista"].pop(idx)
                    st.rerun()

        tipo_atividade = st.selectbox("Atividade / Norma (NBR ISO/CIE 8995-1)", list(TABELA_NORMA.keys()), key=f"ativ_{amb_atual['id']}")

        st.markdown("#### Geometria e Parâmetros")
        col_a, col_b = st.columns(2)
        
        with col_a:
            comprimento = st.number_input("Comprimento C (m)", value=6.00, step=0.1, key=f"comp_{amb_atual['id']}")
            largura = st.number_input("Largura L (m)", value=4.50, step=0.1, key=f"larg_{amb_atual['id']}")
            pe_direito = st.number_input("Pé-Direito Total H (m)", value=2.90, step=0.1, key=f"ped_{amb_atual['id']}")
            hp = st.number_input("Altura do Plano de Trabalho hp (m)", value=0.75, step=0.05, key=f"hp_{amb_atual['id']}")
            hp_desc = st.number_input("Pendotamento / Descimento hp' (m)", value=0.00, step=0.05, key=f"hpd_{amb_atual['id']}")

        with col_b:
            lux_padrao = TABELA_NORMA[tipo_atividade]
            iluminancia_req = st.number_input("Iluminância Meta Requerida (lx)", value=lux_padrao, step=50, key=f"lux_{amb_atual['id']}")
            fluxo_lampada = st.number_input("Fluxo Luminoso da Luminária (lm)", value=2000, step=100, key=f"flux_{amb_atual['id']}")
            potencia_lampada = st.number_input("Potência Unitária da Luminária (W)", value=20, step=1, key=f"pot_{amb_atual['id']}")
            
            fator_u = st.slider("Fator de Utilização (u)", 0.10, 0.90, 0.50, step=0.01, key=f"fu_{amb_atual['id']}")
            
            opcoes_depreciacao = {
                "Ambiente Limpo / Residencial (Manutenção Boa) - 0.80": 0.80,
                "Ambiente Comercial / Escritório Padrão - 0.75": 0.75,
                "Ambiente com Poeira Moderada / Cozinha - 0.70": 0.70,
                "Ambiente Severo / Industrial - 0.60": 0.60,
                "Personalizado (Manual)": "custom"
            }
            escolha_dep = st.selectbox("Fator de Depreciação / Manutenção (d)", list(opcoes_depreciacao.keys()), key=f"dep_sel_{amb_atual['id']}")
            
            if escolha_dep == "Personalizado (Manual)":
                fator_d = st.number_input("Valor Personalizado de d", 0.50, 0.95, 0.80, step=0.05, key=f"fd_custom_{amb_atual['id']}")
                desc_depreciacao = f"Personalizado ({fator_d:.2f})"
            else:
                fator_d = opcoes_depreciacao[escolha_dep]
                desc_depreciacao = escolha_dep

            razao_max_input = st.slider("Razão Máx. de Espaçamento (Emax / hu)", 1.0, 2.0, 1.25, step=0.05, key=f"rz_{amb_atual['id']}")
            modo_afastamento = st.selectbox("Critério de Afastamento das Paredes", ["Proporcional (S/2)", "Fixo Personalizado"], key=f"afas_{amb_atual['id']}")
            afastamento_fixo_val = 0.50
            if modo_afastamento == "Fixo Personalizado":
                afastamento_fixo_val = st.number_input("Distância Fixa da Parede (m)", value=0.50, step=0.05, key=f"afas_val_{amb_atual['id']}")

        fita_comprimento = 0.0
        fita_pot_metro = 14.4
        fita_tensao = "12V"
        fita_pot_total = 0.0
        fita_fonte_rec = 0.0
        spot_angulo = 38
        spot_diametro = 0.0

        if is_pro:
            st.markdown("#### 🔥 Módulo PRO: Fitas LED & Spots")
            col_pro1, col_pro2 = st.columns(2)
            with col_pro1:
                fita_comprimento = st.number_input("Comprimento Linear da Fita / Sanca (m)", value=10.5, step=0.5, key=f"fita_c_{amb_atual['id']}")
                fita_pot_metro = st.selectbox("Potência da Fita LED (W/m)", [4.8, 9.6, 14.4, 19.2, 24.0], index=2, key=f"fita_p_{amb_atual['id']}")
                fita_tensao = st.selectbox("Tensão de Operação", ["12V", "24V"], key=f"fita_t_{amb_atual['id']}")
                fita_pot_total = fita_comprimento * fita_pot_metro
                fita_fonte_rec = fita_pot_total * 1.20
            with col_pro2:
                spot_angulo = st.slider("Abertura do Feixe do Spot (Graus)", 15, 60, 38, step=1, key=f"spot_a_{amb_atual['id']}")
                hu_calc_temp = max(pe_direito - hp - hp_desc, 0.1)
                spot_diametro = 2 * hu_calc_temp * math.tan(math.radians(spot_angulo / 2.0))
                st.metric("Diâmetro da Mancha de Luz", f"{spot_diametro:.2f} m")

        area = comprimento * largura
        hu = max(pe_direito - hp - hp_desc, 0.1)
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

        st.markdown("---")
        st.markdown(f"**Resultados Analíticos para: {novo_nome}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Área", f"{area:.2f} m²")
        c2.metric("Índice K", f"{k_indice:.2f}")
        c3.metric("Luminárias", f"{qtd_real} un")
        c4.metric("Iluminância", f"{lux_real:.2f} lx")

        if conforme:
            st.success(f"✅ Conforme NBR ISO/CIE 8995-1 ({lux_real:.2f} lx alcançados).")
        else:
            st.warning(f"⚠️ Abaixo da meta de {iluminancia_req} lx.")

        lista_calculos_ambientes.append({
            "nome": novo_nome, "comp": comprimento, "larg": largura,
            "pe_direito": pe_direito, "hp": hp, "hp_desc": hp_desc,
            "area": area, "hu": hu, "lux_req": iluminancia_req,
            "fluxo": fluxo_lampada, "potencia": potencia_lampada,
            "k_indice": k_indice, "fator_u": fator_u, "fator_d": fator_d,
            "desc_depreciacao": desc_depreciacao,
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
        })

st.markdown("---")
st.subheader("📥 Emissão do Relatório Consolidado")

dados_cliente = {"nome": cli_nome if cli_nome else "Cliente / Empreendimento"}
dados_prof = {
    "titulo": titulo_prof, 
    "nome": prof_nome if prof_nome else "[Nome do Profissional]", 
    "registro": prof_registro if prof_registro else "[Registro Profissional]", 
    "contato": prof_contato if prof_contato else "[Contato]"
}

if is_pro:
    docx_bytes = gerar_docx_lote(dados_cliente, dados_prof, lista_calculos_ambientes, logo_file=logo_upload)
    st.download_button(
        label="📝 Baixar Relatório Técnico Consolidado em Word (.DOCX)",
        data=docx_bytes,
        file_name="Relatorio_Luminotecnico_Consolidado.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
else:
    if len(lista_calculos_ambientes) > 0:
        docx_bytes = gerar_docx_lote(dados_cliente, dados_prof, [lista_calculos_ambientes[0]], logo_file=logo_upload)
        st.download_button(
            label="📝 Baixar Relatório Técnico em Word (.DOCX)",
            data=docx_bytes,
            file_name="Relatorio_Luminotecnico.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    st.info("🔒 Assine o **Plano PRO** para consolidar múltiplos ambientes em um único arquivo de relatório.")
