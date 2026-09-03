import streamlit as st
import pandas as pd
import math
import io
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Sistema de Cálculo Luminotécnico & Laudos",
    page_icon="💡",
    layout="wide"
)

# --- SISTEMA DE LOGIN E CONTROLE DE ACESSO ---
def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("## 🔐 Área Restrita - Acesso ao Sistema Luminotécnico")
        st.markdown("Por favor, faça login ou escolha um plano de acesso para continuar.")
        
        tab_login, tab_planos = st.tabs(["🔑 Fazer Login", "💳 Assinar / Planos"])
        
        with tab_login:
            with st.form("form_login"):
                email_input = st.text_input("E-mail")
                senha_input = st.text_input("Senha", type="password")
                btn_entrar = st.form_submit_button("Entrar no Sistema")
                
                if btn_entrar:
                    # Credenciais solicitadas
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

# Executa a verificação de login antes de renderizar o app
if not verificar_autenticacao():
    st.stop()

# --- TABELA DE NORMAS (NBR 5413 / ISO 8995) ---
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

# --- FUNÇÃO DE GERAÇÃO DO WORD (DOCX) PROFISSIONAL ---
def gerar_docx_lote(dados_cliente, dados_profissional, lista_ambientes, logo_file=None):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    doc = Document()
    
    # Margens da página
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Estilo base
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Arial'
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = RGBColor(50, 50, 50)

    HEX_COR_PRIMARIA = "1A365D"    # Azul Marinho Escuro
    HEX_COR_SECUNDARIA = "E2E8F0"  # Cinza Claro
    COR_TEXTO_TITULO = RGBColor(26, 54, 93)

    def set_cell_background(cell, hex_color):
        shading_xml = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
        cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

    def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)

    # Cabeçalho / Logo se houver
    if logo_file:
        try:
            doc.add_picture(logo_file, width=Inches(1.8))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        except Exception:
            pass

    # Capa / Título Principal
    p_titulo = doc.add_paragraph()
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_titulo = p_titulo.add_run("LAUDO TÉCNICO LUMINOTÉCNICO")
    run_titulo.bold = True
    run_titulo.font.size = Pt(18)
    run_titulo.font.color.rgb = COR_TEXTO_TITULO
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Memória de Cálculo e Projeto de Iluminação Baseado na NBR 5413 / ISO 8995")
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.add_paragraph()

    # 1. Identificação Geral
    h1 = doc.add_heading(level=2)
    run_h1 = h1.add_run("1. Identificação do Projeto e Partes Envolvidas")
    run_h1.font.color.rgb = COR_TEXTO_TITULO
    
    t_info = doc.add_table(rows=2, cols=2)
    t_info.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_info.autofit = False

    col_widths = [Inches(3.25), Inches(3.25)]
    dados_tabela_info = [
        [("Cliente:", f" {dados_cliente.get('nome', 'N/D')}"), ("E-mail do Cliente:", f" {dados_cliente.get('email', 'N/D')}")],
        [("Profissional Responsável:", f" {dados_profissional.get('nome', 'N/D')}"), ("Registro / Contato:", f" CREA: {dados_profissional.get('registro', 'N/D')} | Cel: {dados_profissional.get('celular', 'N/D')}")]
    ]

    for row_idx, row_data in enumerate(dados_tabela_info):
        for col_idx, (label, val) in enumerate(row_data):
            cell = t_info.cell(row_idx, col_idx)
            cell.width = col_widths[col_idx]
            set_cell_background(cell, HEX_COR_SECUNDARIA if row_idx == 0 else "FFFFFF")
            set_cell_margins(cell, top=140, bottom=140, left=150, right=150)
            
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            run_lbl = p.add_run(label)
            run_lbl.bold = True
            run_lbl.font.size = Pt(9.5)
            run_val = p.add_run(val)
            run_val.font.size = Pt(9.5)

    doc.add_paragraph()

    # 2. Resumo Executivo Consolidado
    h2 = doc.add_heading(level=2)
    run_h2 = h2.add_run("2. Resumo Consolidado dos Ambientes")
    run_h2.font.color.rgb = COR_TEXTO_TITULO

    t_res = doc.add_table(rows=len(lista_ambientes) + 1, cols=6)
    t_res.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_res.autofit = False

    larguras_res = [Inches(1.5), Inches(0.8), Inches(0.9), Inches(1.1), Inches(1.1), Inches(1.1)]
    cabecalhos_res = ["Ambiente", "Área (m²)", "Lux Req.", "Lux Real", "Qtd. Lâmp.", "Status"]

    for col_idx, texto in enumerate(cabecalhos_res):
        cell = t_res.cell(0, col_idx)
        cell.width = larguras_res[col_idx]
        set_cell_background(cell, HEX_COR_PRIMARIA)
        set_cell_margins(cell, top=150, bottom=150, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(texto)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(9)

    for idx, amb in enumerate(lista_ambientes):
        row_cells = t_res.rows[idx + 1].cells
        dados_linha = [
            amb["nome"],
            f"{amb['area']:.2f}",
            f"{amb['lux_req']:.0f} lx",
            f"{amb['lux_real']:.1f} lx",
            str(amb['qtd_real']),
            "CONFORME" if amb['conforme'] else "NÃO CONFORME"
        ]
        
        bg_cor = "F7FAFC" if idx % 2 == 0 else "FFFFFF"
        for col_idx, texto_val in enumerate(dados_linha):
            cell = row_cells[col_idx]
            cell.width = larguras_res[col_idx]
            set_cell_background(cell, bg_cor)
            set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
            p = cell.paragraphs[0]
            if col_idx > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(texto_val)
            run.font.size = Pt(9)
            if col_idx == 5:
                run.bold = True
                run.font.color.rgb = RGBColor(34, 139, 34) if amb['conforme'] else RGBColor(178, 34, 34)

    doc.add_page_break()

    # 3. Detalhamento Técnico Completo por Ambiente
    h3 = doc.add_heading(level=2)
    run_h3 = h3.add_run("3. Memória de Cálculo Detalhada por Ambiente")
    run_h3.font.color.rgb = COR_TEXTO_TITULO

    for idx, amb in enumerate(lista_ambientes):
        p_amb = doc.add_paragraph()
        r_amb = p_amb.add_run(f"3.{idx+1}. Ambiente: {amb['nome']}")
        r_amb.bold = True
        r_amb.font.size = Pt(11.5)
        r_amb.font.color.rgb = COR_TEXTO_TITULO

        t_det = doc.add_table(rows=7, cols=2)
        t_det.alignment = WD_TABLE_ALIGNMENT.CENTER
        t_det.autofit = False
        
        detalhes_dados = [
            ("Dimensões do Ambiente", f"Comprimento: {amb['comp']} m | Largura: {amb['larg']} m | Área: {amb['area']:.2f} m²"),
            ("Geometria e Pé-Direito", f"Pé-Direito: {amb['pe_direito']} m | Plano de Trabalho (hP): {amb['hp']} m | Altura Útil (hu): {amb['hu']:.2f} m"),
            ("Fatores Aplicados", f"Fator de Utilização (u): {amb['fator_u']} | Fator de Depreciação (d): {amb['fator_d']} | Índice K: {amb['k_indice']:.2f}"),
            ("Luminária / Fonte", f"Modelo: {amb['modelo_lum']} | Fluxo Unitário: {amb['fluxo']} lm | Potência Unitária: {amb['potencia']} W"),
            ("Resultados de Iluminância", f"Iluminância Requerida: {amb['lux_req']:.0f} lx | Iluminância Obtida: {amb['lux_real']:.1f} lx"),
            ("Arranjo Físico Proposto", f"Quantidade de Luminárias: {amb['qtd_real']} unidades ({amb['linhas']} linhas x {amb['colunas']} colunas)"),
            ("Carga e Eficiência Energética", f"Potência Total Instalada: {amb['pot_total']:.1f} W | Densidade de Potência (DPI): {amb['dpi']:.2f} W/m²")
        ]

        for r_i, (chave, valor) in enumerate(detalhes_dados):
            c_label, c_val = t_det.cell(r_i, 0), t_det.cell(r_i, 1)
            c_label.width, c_val.width = Inches(2.3), Inches(4.2)
            set_cell_background(c_label, HEX_COR_SECUNDARIA)
            set_cell_background(c_val, "FFFFFF")
            set_cell_margins(c_label, top=90, bottom=90, left=100, right=100)
            set_cell_margins(c_val, top=90, bottom=90, left=100, right=100)
            
            p0 = c_label.paragraphs[0]
            p0.paragraph_format.space_after = Pt(0)
            r_l = p0.add_run(chave)
            r_l.bold = True
            r_l.font.size = Pt(8.5)
            
            p1 = c_val.paragraphs[0]
            p1.paragraph_format.space_after = Pt(0)
            r_v = p1.add_run(valor)
            r_v.font.size = Pt(8.5)

        doc.add_paragraph()

    # Bloco de Assinatura
    p_ass = doc.add_paragraph()
    p_ass.paragraph_format.space_before = Pt(40)
    r_ass = p_ass.add_run(f"__________________________________________________\n{dados_profissional.get('nome', 'Profissional Responsável')}\nRegistro CREA/CAU: {dados_profissional.get('registro', 'N/D')}\nContato: {dados_profissional.get('celular', 'N/D')} | {dados_profissional.get('email', 'N/D')}")
    r_ass.font.size = Pt(9)
    p_ass.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# --- INTERFACE PRINCIPAL DO APLICATIVO ---
st.title("💡 Sistema Avançado de Cálculo Luminotécnico & Laudos")
st.markdown(f"**Sessão Ativa:** {st.session_state.get('usuario_email', 'Usuário')} ({st.session_state.get('plano_ativo', 'Plano Ativo')})")

# Botão de Sair/Logout na Barra Lateral
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

# Gerenciamento do Banco de Luminárias do Usuário no Session State
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
    st.session_state.ambientes = [{"id": 1, "nome": "Sala de Estar Principal"}]

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
            tipo_atividade = st.selectbox("Atividade / Norma (NBR 5413)", list(TABELA_NORMA.keys()), key=f"ativ_{amb_atual['id']}")

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
            comp = st.number_input("Comprimento (m)", value=5.0, step=0.1, key=f"comp_{amb_atual['id']}")
            pe_direito = st.number_input("Pé-Direito (m)", value=2.8, step=0.1, key=f"pd_{amb_atual['id']}")
        with col_g2:
            larg = st.number_input("Largura (m)", value=4.0, step=0.1, key=f"larg_{amb_atual['id']}")
            hp = st.number_input("Plano de Trabalho (m)", value=0.75, step=0.05, key=f"hp_{amb_atual['id']}")
        with col_g3:
            hp_desc = st.number_input("Descimento da Luminária (m)", value=0.0, step=0.05, key=f"hdesc_{amb_atual['id']}")
            fator_d = st.slider("Fator de Depreciação (d)", 0.5, 0.9, 0.8, 0.05, key=f"fd_{amb_atual['id']}")

        fator_u = st.slider("Fator de Utilização (u)", 0.3, 0.8, 0.55, 0.05, key=f"fu_{amb_atual['id']}")

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
            "modelo_lum": modelo_desc_relatorio,
            "fluxo_instalado": fluxo_instalado,
            "qtd_teorica": qtd_teorica,
            "qtd_real": qtd_real,
            "linhas": linhas,
            "colunas": colunas,
            "lux_real": lux_real,
            "pot_total": pot_total,
            "dpi": dpi,
            "variacao_fluxo_pct": variacao_fluxo_pct,
            "conforme": conforme
        })
        
        st.markdown("---")

st.subheader("3. Emissão de Laudo Técnico Profissional (Word)")

if st.button("📄 Gerar Laudo Técnico Completo em DOCX", use_container_width=True):
    dados_cli_dict = {
        "nome": cli_nome if cli_nome else "Cliente Não Informado",
        "email": cli_email if cli_email else "Não informado"
    }
    dados_prof_dict = {
        "nome": prof_nome if prof_nome else "Profissional Não Informado",
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
