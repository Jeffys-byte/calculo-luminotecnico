import streamlit as st
import pandas as pd
import math
import io
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Luminotécnica",
    page_icon="💡",
    layout="wide"
)

# --- SISTEMA DE LOGIN E CONTROLE DE ACESSO ---
def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("## 🔐 Área Restrita - Acesso ao Sistema Luminotécnica")
        st.markdown("Por favor, faça login ou escolha um plano de acesso para continuar.")
        
        tab_login, tab_planos = st.tabs(["🔑 Fazer Login", "💳 Assinar / Planos"])
        
        with tab_login:
            with st.form("form_login"):
                email_input = st.text_input("E-mail")
                senha_input = st.text_input("Senha", type="password")
                btn_entrar = st.form_submit_button("Entrar no Sistema")
                
                if btn_entrar:
                    if email_input.strip() == "jefkar27@gmail.com" and senha_input.strip() == "255859":
                        st.session_state.autenticado = True
                        st.session_state.usuario_email = email_input
                        st.session_state.plano_ativo = "Acesso Vitalício / Mestre"
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
                        
        with tab_planos:
            st.markdown("### Escolha o seu plano de acesso profissional:")
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.markdown("#### 🌟 Plano Semestral")
                st.markdown("**6 Meses de Acesso Completo**")
                st.markdown("### R$ 69,00")
                st.markdown("- Todos os cálculos luminotécnicos\n- Emissão de laudos completos em Word\n- Suporte a atualizações")
                if st.button("Assinar Plano Semestral", use_container_width=True):
                    st.info("Para liberar seu acesso imediato via PIX/Cartão, entre em contato com o suporte ou utilize o login mestre.")
                    
            with col_p2:
                st.markdown("#### 🚀 Plano Anual")
                st.markdown("**1 Ano de Acesso Completo**")
                st.markdown("### R$ 99,00")
                st.markdown("- **Melhor Custo-Benefício**\n- Todos os recursos liberados\n- Prioridade em novas atualizações")
                if st.button("Assinar Plano Anual", use_container_width=True):
                    st.info("Para liberar seu acesso imediato via PIX/Cartão, entre em contato com o suporte ou utilize o login mestre.")
                    
        return False
    return True

if not verificar_autenticacao():
    st.stop()

# --- TABELA DE NORMAS (NBR ISO/CIE 8995-1 / NBR 5410) ---
TABELA_NORMA = {
    "Escritórios - Geral / Digitação": 500,
    "Escritórios - Reunião / Conferência": 300,
    "Comércio - Lojas de Departamento / Varejo": 500,
    "Comércio - Supermercados / Áreas de Circulação": 300,
    "Indústria - Montagem Grosso (Ex: Mecânica Pesada)": 200,
    "Indústria - Montagem Média (Ex: Eletrônicos)": 500,
    "Indústria - Montagem Fina (Ex: Relojoaria)": 1000,
    "Residências - Salas de Estar / Dormitórios": 150,
    "Residências - Cozinhas / Banheiros": 300,
    "Escolas - Salas de Aula / Laboratórios": 300,
    "Hospitais - Enfermarias": 100,
    "Hospitais - Salas de Cirurgia / Emergência": 1000,
    "Garagens - Áreas de Estacionamento / Circulação": 75,
}

# --- FUNÇÃO DE GERAÇÃO DO WORD (DOCX) NO FORMATO EXATO SOLICITADO ---
def gerar_docx_lote(dados_cliente, dados_profissional, lista_ambientes, logo_file=None):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Arial'
    style_normal.font.size = Pt(9.5)
    style_normal.font.color.rgb = RGBColor(50, 50, 50)

    HEX_COR_PRIMARIA = "1A365D"    # Azul Marinho Escuro
    HEX_COR_SECUNDARIA = "E2E8F0"  # Cinza Claro
    COR_TEXTO_TITULO = RGBColor(26, 54, 93)

    def set_cell_background(cell, hex_color):
        shading_xml = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
        cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

    def set_cell_margins(cell, top=100, bottom=100, left=120, right=120):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)

    if logo_file:
        try:
            doc.add_picture(logo_file, width=Inches(1.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        except Exception:
            pass

    data_atual_str = datetime.date.today().strftime("%d/%m/%Y")

    for idx, amb in enumerate(lista_ambientes):
        if idx > 0:
            doc.add_page_break()

        # Título principal do ambiente
        p_t = doc.add_paragraph()
        r_t = p_t.add_run(f"RELATÓRIO DE DIMENSIONAMENTO LUMINOTÉCNICO\nAMBIENTE: {amb['nome'].upper()}")
        r_t.bold = True
        r_t.font.size = Pt(13)
        r_t.font.color.rgb = COR_TEXTO_TITULO

        p_sub = doc.add_paragraph()
        p_sub.add_run(f"Cliente / Empreendimento: {dados_cliente.get('nome', 'Cliente Geral')} | Método dos Lúmens\n")
        p_sub.add_run(f"Responsável Técnico: {dados_profissional.get('nome', 'Não informado')} — Registro: {dados_profissional.get('registro', 'Não informado')} | Data de Emissão: {data_atual_str}\n")
        p_sub.add_run(f"Norma de Referência: NBR ISO/CIE 8995-1 & NBR 5410")
        p_sub.runs[0].font.size = Pt(9)
        p_sub.runs[1].font.size = Pt(9)
        p_sub.runs[2].font.size = Pt(9)

        doc.add_paragraph()

        # 1. Identificação e Dados Geométricos
        h1 = doc.add_heading(level=2)
        r_h1 = h1.add_run("1. Identificação e Dados Geométricos")
        r_h1.font.size = Pt(11)
        r_h1.font.color.rgb = COR_TEXTO_TITULO

        t1 = doc.add_table(rows=10, cols=4)
        t1.alignment = WD_TABLE_ALIGNMENT.CENTER
        t1.autofit = False
        w1 = [Inches(2.5), Inches(0.8), Inches(1.8), Inches(1.4)]

        headers1 = ["Parâmetro", "Símbolo", "Valor", "Unidade"]
        for ci, h in enumerate(headers1):
            cell = t1.cell(0, ci)
            cell.width = w1[ci]
            set_cell_background(cell, HEX_COR_PRIMARIA)
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            run = p.add_run(h)
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8.5)

        dados_bloco1 = [
            ("Nome do Ambiente", "—", amb['nome'], "—"),
            ("Comprimento", "C", f"{amb['comp']:.2f}", "m"),
            ("Largura", "L", f"{amb['larg']:.2f}", "m"),
            ("Pé-Direito Total", "H", f"{amb['pe_direito']:.2f}", "m"),
            ("Plano de Trabalho", "hp", f"{amb['hp']:.2f}", "m"),
            ("Descimento do Plano", "hp'", f"{amb['hp_desc']:.2f}", "m"),
            ("Área Total", "A", f"{amb['area']:.2f}", "m²"),
            ("Altura Útil", "hu", f"{amb['hu']:.2f}", "m"),
            ("Índice do Local", "k", f"{amb['k_indice']:.2f}", "—")
        ]

        for ri, row_vals in enumerate(dados_bloco1):
            row_cells = t1.rows[ri + 1].cells
            bg = "F7FAFC" if ri % 2 == 0 else "FFFFFF"
            for ci, val in enumerate(row_vals):
                cell = row_cells[ci]
                cell.width = w1[ci]
                set_cell_background(cell, bg)
                set_cell_margins(cell)
                p = cell.paragraphs[0]
                run = p.add_run(val)
                run.font.size = Pt(8.5)

        doc.add_paragraph()

        # 2. Parâmetros Luminotécnicos
        h2 = doc.add_heading(level=2)
        r_h2 = h2.add_run("2. Parâmetros Luminotécnicos")
        r_h2.font.size = Pt(11)
        r_h2.font.color.rgb = COR_TEXTO_TITULO

        t2 = doc.add_table(rows=7, cols=4)
        t2.alignment = WD_TABLE_ALIGNMENT.CENTER
        t2.autofit = False
        w2 = [Inches(2.3), Inches(0.9), Inches(1.8), Inches(1.5)]

        headers2 = ["Parâmetro Técnico", "Símbolo", "Valor Adotado", "Norma / Descrição"]
        for ci, h in enumerate(headers2):
            cell = t2.cell(0, ci)
            cell.width = w2[ci]
            set_cell_background(cell, HEX_COR_PRIMARIA)
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            run = p.add_run(h)
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8.5)

        dados_bloco2 = [
            ("Iluminância Requerida", "Ereq", f"{amb['lux_req']:.0f} lx", "NBR ISO/CIE 8995-1"),
            ("Fluxo da Luminária", "Φlâmpada", f"{amb['fluxo']:,.0f} lm".replace(",", "."), amb['modelo_lum']),
            ("Potência Unitária", "Punit", f"{amb['potencia']:.1f} W", "Consumo (W)"),
            ("Fator de Utilização", "u", f"{amb['fator_u']:.2f}", f"{amb['fator_u']:.2f} ({amb['desc_utilizacao']})"),
            ("Fator de Depreciação", "d", f"{amb['fator_d']:.2f}", f"{amb['fator_d']:.2f} ({amb['desc_depreciacao']})")
        ]

        for ri, row_vals in enumerate(dados_bloco2):
            row_cells = t2.rows[ri + 1].cells
            bg = "F7FAFC" if ri % 2 == 0 else "FFFFFF"
            for ci, val in enumerate(row_vals):
                cell = row_cells[ci]
                cell.width = w2[ci]
                set_cell_background(cell, bg)
                set_cell_margins(cell)
                p = cell.paragraphs[0]
                run = p.add_run(val)
                run.font.size = Pt(8.5)

        doc.add_paragraph()

        # 3. Resultados do Dimensionamento
        h3 = doc.add_heading(level=2)
        r_h3 = h3.add_run("3. Resultados do Dimensionamento")
        r_h3.font.size = Pt(11)
        r_h3.font.color.rgb = COR_TEXTO_TITULO

        t3 = doc.add_table(rows=15, cols=4)
        t3.alignment = WD_TABLE_ALIGNMENT.CENTER
        t3.autofit = False
        w3 = [Inches(2.8), Inches(1.3), Inches(1.4), Inches(1.0)]

        headers3 = ["Item de Cálculo", "Valor Calculado", "Valor Adotado", "Unidade"]
        for ci, h in enumerate(headers3):
            cell = t3.cell(0, ci)
            cell.width = w3[ci]
            set_cell_background(cell, HEX_COR_PRIMARIA)
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            run = p.add_run(h)
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8.5)

        dados_bloco3 = [
            ("Fluxo Luminoso Necessário", f"{amb['fluxo_req']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), "—", "lm"),
            ("Fluxo Luminoso Instalado (Real)", f"{amb['fluxo_instalado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{amb['fluxo_instalado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), "lm"),
            ("Diferencial de Fluxo (Variância)", f"{amb['variacao_fluxo_pct']:+.1f}%", f"{amb['variacao_fluxo_pct']:+.1f}%", "%"),
            ("Qtd. de Luminárias", f"{amb['qtd_teorica']:.2f}", f"{amb['qtd_real']}", "un"),
            ("Arranjo (Linhas x Colunas)", f"{amb['linhas']} x {amb['colunas']}", f"{amb['linhas']} x {amb['colunas']}", "arr."),
            ("Distância entre Luminárias (C)", f"{amb['dist_c_entre']:.2f}", f"{amb['dist_c_entre']:.2f}", "m"),
            ("Distância até Parede (C)", f"{amb['dist_c_parede']:.2f}", f"{amb['dist_c_parede']:.2f}", "m"),
            ("Distância entre Luminárias (L)", f"{amb['dist_l_entre']:.2f}", f"{amb['dist_l_entre']:.2f}", "m"),
            ("Distância até Parede (L)", f"{amb['dist_l_parede']:.2f}", f"{amb['dist_l_parede']:.2f}", "m"),
            ("Iluminância Real Alcançada", "—", f"{amb['lux_real']:.2f}", "lx"),
            ("Potência Total", "—", f"{amb['pot_total']:.2f}", "W"),
            ("Densidade de Potência (DPI)", "—", f"{amb['dpi']:.2f}", "W/m²")
        ]

        for ri, row_vals in enumerate(dados_bloco3):
            row_cells = t3.rows[ri + 1].cells
            bg = "F7FAFC" if ri % 2 == 0 else "FFFFFF"
            for ci, val in enumerate(row_vals):
                cell = row_cells[ci]
                cell.width = w3[ci]
                set_cell_background(cell, bg)
                set_cell_margins(cell)
                p = cell.paragraphs[0]
                run = p.add_run(val)
                run.font.size = Pt(8.5)

        doc.add_paragraph()

        # 4. Parecer Técnico
        h4 = doc.add_heading(level=2)
        r_h4 = h4.add_run("4. Parecer Técnico")
        r_h4.font.size = Pt(11)
        r_h4.font.color.rgb = COR_TEXTO_TITULO

        p_par = doc.add_paragraph()
        status_txt = "CONFORME (Aprovado)." if amb['conforme'] else "NÃO CONFORME (Abaixo do Requerido)."
        r_par = p_par.add_run(f"• Status Final: {status_txt}")
        r_par.bold = True
        r_par.font.size = Pt(9.5)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# --- INTERFACE PRINCIPAL DO APLICATIVO ---
st.title("💡 Luminotécnica")
st.markdown(f"**Sessão Ativa:** {st.session_state.get('usuario_email', 'Usuário')} ({st.session_state.get('plano_ativo', 'Plano Ativo')})")

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏢 Logotipo do Projeto")
logo_upload = st.sidebar.file_uploader("Enviar Logo (.png, .jpg)", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 👷 Identificação do Profissional")
prof_nome = st.sidebar.text_input("Nome do Profissional", value="", key="prof_nome_input")
prof_registro = st.sidebar.text_input("Registro / CREA / CAU", value="", key="prof_reg_input")
prof_celular = st.sidebar.text_input("Celular / WhatsApp", value="", key="prof_cel_input")
prof_email = st.sidebar.text_input("E-mail Profissional", value="", key="prof_email_input")

st.markdown("---")
st.markdown("### 📋 1. Identificação do Cliente")

col_cli1, col_cli2 = st.columns(2)
with col_cli1:
    cli_nome = st.text_input("Nome do Cliente", value="", key="cli_nome_input")
with col_cli2:
    cli_email = st.text_input("E-mail do Cliente", value="", key="cli_email_input")

st.markdown("---")
st.markdown("### 🛋️ 2. Gerenciamento de Ambientes e Lâmpadas")

if "banco_luminarias" not in st.session_state:
    st.session_state.banco_luminarias = [
        {"Fabricante": "Philips", "Modelo": "Painel LED 18W Quadrado", "Lumens": 1440, "Potencia": 18.0},
        {"Fabricante": "Emalux", "Modelo": "Luminária Comercial 2x18W LED", "Lumens": 3200, "Potencia": 36.0},
        {"Fabricante": "Osram", "Modelo": "High Bay LED Industrial 150W", "Lumens": 19500, "Potencia": 150.0},
    ]

with st.expander("⚙️ Gerenciar / Cadastrar Novas Luminárias no Banco"):
    with st.form("form_nova_lum"):
        st.markdown("Adicione novos modelos ao seu banco de seleção rápida:")
        col_fl1, col_fl2, col_fl3, col_fl4 = st.columns(4)
        with col_fl1:
            novo_fab = st.text_input("Fabricante", value="Marca X")
        with col_fl2:
            novo_mod = st.text_input("Modelo", value="Painel 30W")
        with col_fl3:
            novo_lum = st.number_input("Fluxo (lm)", value=2400.0, step=100.0)
        with col_fl4:
            nova_pot = st.number_input("Potência (W)", value=30.0, step=1.0)
            
        btn_salvar_lum = st.form_submit_button("Salvar Nova Luminária no Banco")
        if btn_salvar_lum:
            st.session_state.banco_luminarias.append({
                "Fabricante": novo_fab,
                "Modelo": novo_mod,
                "Lumens": novo_lum,
                "Potencia": nova_pot
            })
            st.success(f"Luminária {novo_fab} - {novo_mod} adicionada com sucesso!")

if "ambientes" not in st.session_state:
    st.session_state.ambientes = [{"id": 1, "nome": "Ambiente 1"}]

col_add, col_rem = st.columns([1, 1])
with col_add:
    if st.button("➕ Adicionar Novo Ambiente"):
        novo_id = st.session_state.ambientes[-1]["id"] + 1 if st.session_state.ambientes else 1
        st.session_state.ambientes.append({"id": novo_id, "nome": f"Ambiente {novo_id}"})
        st.rerun()
with col_rem:
    if len(st.session_state.ambientes) > 1 and st.button("🗑️ Remover Último Ambiente"):
        st.session_state.ambientes.pop()
        st.rerun()

lista_calculos_ambientes = []

for amb_atual in st.session_state.ambientes:
    with st.container():
        st.markdown(f"#### 📐 Parâmetros do Ambiente: {amb_atual['nome']}")
        
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            novo_nome = st.text_input("Nome do Ambiente", value=amb_atual['nome'], key=f"nome_amb_{amb_atual['id']}")
        with col_n2:
            tipo_atividade = st.selectbox("Atividade / Norma (NBR ISO/CIE 8995-1)", list(TABELA_NORMA.keys()), key=f"ativ_{amb_atual['id']}")

        st.markdown("##### 💡 Fonte Luminosa")
        opcoes_banco_str = [f"{l['Fabricante']} - {l['Modelo']} ({l['Lumens']} lm / {l['Potencia']} W)" for l in st.session_state.banco_luminarias]
        opcoes_banco_str.append("⚙️ Inserir Manual / Personalizado")
        
        escolha_banco = st.selectbox("Selecionar Luminária", opcoes_banco_str, key=f"lum_escolha_{amb_atual['id']}")

        if escolha_banco != "⚙️ Inserir Manual / Personalizado":
            idx_escolhido = opcoes_banco_str.index(escolha_banco)
            lum_sel = st.session_state.banco_luminarias[idx_escolhido]
            fluxo_lampada, potencia_lampada = lum_sel["Lumens"], lum_sel["Potencia"]
            modelo_desc_relatorio = f"{lum_sel['Fabricante']} - {lum_sel['Modelo']}"
        else:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                fluxo_lampada = st.number_input("Fluxo Luminoso (lm)", value=1800.0, step=100.0, key=f"fluxo_man_{amb_atual['id']}")
            with col_m2:
                potencia_lampada = st.number_input("Potência da Luminária (W)", value=20.0, step=1.0, key=f"pot_man_{amb_atual['id']}")
            modelo_desc_relatorio = "Manual / Personalizado"

        st.markdown("##### Geometria e Fatores")
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            comp = st.number_input("Comprimento (m)", value=6.0, step=0.1, key=f"comp_{amb_atual['id']}")
            pe_direito = st.number_input("Pé-Direito (m)", value=2.9, step=0.1, key=f"pd_{amb_atual['id']}")
        with col_g2:
            larg = st.number_input("Largura (m)", value=4.5, step=0.1, key=f"larg_{amb_atual['id']}")
            hp = st.number_input("Plano de Trabalho (m)", value=0.75, step=0.05, key=f"hp_{amb_atual['id']}")
        with col_g3:
            hp_desc = st.number_input("Descimento da Luminária (m)", value=0.0, step=0.05, key=f"hdesc_{amb_atual['id']}")

        # Janelas com explicações detalhadas para os Fatores (Conforme solicitado)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fator_u = st.slider("Fator de Utilização (u)", 0.3, 0.8, 0.50, 0.05, key=f"fu_{amb_atual['id']}")
            with st.expander("ℹ️ O que é o Fator de Utilização (u)?"):
                st.markdown("""
                O **Fator de Utilização ($u$)** representa a eficiência com que o fluxo luminoso emitido pelas luminárias atinge o plano de trabalho. 
                Ele depende diretamente de:
                - **Geometria do ambiente** (Índice do local $k$).
                - **Reflexão das superfícies** (paredes, teto e piso).
                - **Distribuição fotométrica** da luminária.
                *Valores típicos variam de 0.3 (ambientes escuros/pequenos) a 0.8 (ambientes claros e amplos).*
                """)
        with col_f2:
            fator_d = st.slider("Fator de Depreciação (d)", 0.5, 0.9, 0.75, 0.05, key=f"fd_{amb_atual['id']}")
            with st.expander("ℹ️ O que é o Fator de Depreciação (d)?"):
                st.markdown("""
                O **Fator de Depreciação ($d$)** — também conhecido como fator de manutenção — considera a queda do fluxo luminoso ao longo do tempo devido a:
                - Acúmulo de poeira e sujeira nas luminárias e lâmpadas.
                - Redução natural do fluxo luminoso da fonte de luz com o envelhecimento.
                - Sujeira nas paredes e teto do ambiente.
                *Valores usuais: 0.80 para ambientes limpos, 0.70 a 0.75 para ambientes padrão e abaixo de 0.65 para ambientes industriais severos.*
                """)

        # --- MEMÓRIA DE CÁLCULO ---
        area = comp * larg
        hu = pe_direito - hp - hp_desc
        k_indice = (comp * larg) / (hu * (comp + larg)) if hu > 0 else 1.0
        lux_req = TABELA_NORMA[tipo_atividade]

        fluxo_req = (lux_req * area) / (fator_u * fator_d) if (fator_u * fator_d) > 0 else 0
        qtd_teorica = fluxo_req / fluxo_lampada if fluxo_lampada > 0 else 0
        qtd_real = math.ceil(qtd_teorica)
        if qtd_real < 1:
            qtd_real = 1

        proporcao = comp / larg if larg > 0 else 1.0
        colunas = math.ceil(math.sqrt(qtd_real * proporcao))
        linhas = math.ceil(qtd_real / colunas) if colunas > 0 else 1

        # Cálculo das distâncias entre luminárias e paredes
        dist_c_entre = comp / colunas if colunas > 0 else comp
        dist_c_parede = dist_c_entre / 2.0
        dist_l_entre = larg / linhas if linhas > 0 else larg
        dist_l_parede = dist_l_entre / 2.0

        fluxo_instalado = qtd_real * fluxo_lampada
        lux_real = (fluxo_instalado * fator_u * fator_d) / area if area > 0 else 0
        pot_total = qtd_real * potencia_lampada
        dpi = pot_total / area if area > 0 else 0
        variacao_fluxo_pct = ((fluxo_instalado - fluxo_req) / fluxo_req) * 100 if fluxo_req > 0 else 0
        conforme = lux_real >= lux_req

        lista_calculos_ambientes.append({
            "id": amb_atual["id"],
            "nome": novo_nome,
            "comp": comp,
            "larg": larg,
            "pe_direito": pe_direito,
            "hp": hp,
            "hp_desc": hp_desc,
            "hu": hu,
            "area": area,
            "k_indice": k_indice,
            "lux_req": lux_req,
            "fluxo_req": fluxo_req,
            "fluxo": fluxo_lampada,
            "potencia": potencia_lampada,
            "fator_u": fator_u,
            "fator_d": fator_d,
            "desc_utilizacao": "Ambiente médio / Padrão",
            "desc_depreciacao": "Limpeza periódica / Padrão",
            "modelo_lum": modelo_desc_relatorio,
            "fluxo_instalado": fluxo_instalado,
            "qtd_teorica": qtd_teorica,
            "qtd_real": qtd_real,
            "linhas": linhas,
            "colunas": colunas,
            "dist_c_entre": dist_c_entre,
            "dist_c_parede": dist_c_parede,
            "dist_l_entre": dist_l_entre,
            "dist_l_parede": dist_l_parede,
            "lux_real": lux_real,
            "pot_total": pot_total,
            "dpi": dpi,
            "variacao_fluxo_pct": variacao_fluxo_pct,
            "conforme": conforme
        })
        
        st.markdown("---")

st.subheader("3. Emissão de Laudo Técnico Luminotécnico (Word)")

if st.button("📄 Gerar Laudo Técnico Completo em DOCX", use_container_width=True):
    dados_cli_dict = {
        "nome": cli_nome if cli_nome else "Cliente Geral",
        "email": cli_email if cli_email else "Não informado"
    }
    dados_prof_dict = {
        "nome": prof_nome if prof_nome else "Não informado",
        "registro": prof_registro if prof_registro else "Não informado",
        "celular": prof_celular if prof_celular else "Não informado",
        "email": prof_email if prof_email else "Não informado"
    }
    
    logo_bytes = io.BytesIO(logo_upload.getvalue()) if logo_upload is not None else None
    
    arquivo_docx_bytes = gerar_docx_lote(dados_cli_dict, dados_prof_dict, lista_calculos_ambientes, logo_file=logo_bytes)
    
    st.success("Laudo técnico gerado com sucesso!")
    st.download_button(
        label="📥 Baixar Laudo Luminotécnico (.docx)",
        data=arquivo_docx_bytes,
        file_name=f"Laudo_Luminotecnico_{cli_nome.replace(' ', '_') if cli_nome else 'Projeto'}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
    
