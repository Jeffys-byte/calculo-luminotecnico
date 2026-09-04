import streamlit as st
import pandas as pd
import math
import io
import datetime
import base64
import sqlite3
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Luminotécnica Profissional - Teste SQLite",
    page_icon="💡",
    layout="wide"
)

# --- SISTEMA DE PERSISTÊNCIA COM SQLITE ---
BANCO_DADOS_SQLITE = "luminotecnica_teste.db"

def inicializar_banco():
    conn = sqlite3.connect(BANCO_DADOS_SQLITE)
    cursor = conn.cursor()
    
    # Tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            senha TEXT NOT NULL,
            criacao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            assinante INTEGER NOT NULL
        )
    ''')
    
    # Tabela de Clientes vinculados ao usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_email TEXT,
            nome TEXT,
            email_cliente TEXT,
            telefone TEXT,
            cidade TEXT,
            FOREIGN KEY (usuario_email) REFERENCES usuarios (email)
        )
    ''')
    
    # Inserir usuário Admin padrão se não existir
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", ("jefkar27@gmail.com",))
    if not cursor.fetchone():
        data_criacao_padrao = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        cursor.execute(
            "INSERT INTO usuarios (email, senha, criacao, tipo, assinante) VALUES (?, ?, ?, ?, ?)",
            ("jefkar27@gmail.com", "123", data_criacao_padrao, "admin", 1)
        )
        cursor.execute(
            "INSERT INTO clientes (usuario_email, nome, email_cliente, telefone, cidade) VALUES (?, ?, ?, ?, ?)",
            ("jefkar27@gmail.com", "Cliente Geral", "contato@clientegeral.com", "(21) 99999-9999", "Rio de Janeiro - RJ")
        )
        
    conn.commit()
    conn.close()

inicializar_banco()

def db_obter_usuario(email):
    conn = sqlite3.connect(BANCO_DADOS_SQLITE)
    cursor = conn.cursor()
    cursor.execute("SELECT email, senha, criacao, tipo, assinante FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "email": row[0],
            "senha": row[1],
            "criacao": datetime.datetime.fromisoformat(row[2]),
            "tipo": row[3],
            "assinante": bool(row[4])
        }
    return None

def db_salvar_usuario(email, senha, tipo="cliente", assinante=False):
    conn = sqlite3.connect(BANCO_DADOS_SQLITE)
    cursor = conn.cursor()
    agora_str = datetime.datetime.now().isoformat()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO usuarios (email, senha, criacao, tipo, assinante) VALUES (?, ?, ?, ?, ?)",
            (email, senha, agora_str, tipo, int(assinante))
        )
        cursor.execute(
            "INSERT INTO clientes (usuario_email, nome, email_cliente, telefone, cidade) VALUES (?, ?, ?, ?, ?)",
            (email, "Cliente Exemplo", "exemplo@email.com", "(21) 98888-8888", "Rio de Janeiro - RJ")
        )
        conn.commit()
        sucesso = True
    except Exception as e:
        sucesso = False
    conn.close()
    return sucesso

def db_obter_clientes(email):
    conn = sqlite3.connect(BANCO_DADOS_SQLITE)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, email_cliente, telefone, cidade FROM clientes WHERE usuario_email = ?", (email,))
    rows = cursor.fetchall()
    conn.close()
    clientes = []
    for r in rows:
        clientes.append({
            "Nome": r[0],
            "Email": r[1],
            "Telefone": r[2],
            "Cidade": r[3]
        })
    if not clientes:
        clientes = [{"Nome": "Cliente Geral", "Email": "contato@clientegeral.com", "Telefone": "(21) 99999-9999", "Cidade": "Rio de Janeiro - RJ"}]
    return clientes

def db_adicionar_cliente(email, nome, email_cli, tel_cli, cidade_cli):
    conn = sqlite3.connect(BANCO_DADOS_SQLITE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clientes (usuario_email, nome, email_cliente, telefone, cidade) VALUES (?, ?, ?, ?, ?)",
        (email, nome, email_cli, tel_cli, cidade_cli)
    )
    conn.commit()
    conn.close()

# FUNÇÕES EXCLUSIVAS PARA O PAINEL ADMIN
def db_listar_todos_usuarios():
    conn = sqlite3.connect(BANCO_DADOS_SQLITE)
    df = pd.read_sql_query("SELECT email, senha, criacao, tipo, assinante FROM usuarios", conn)
    conn.close()
    return df

def db_listar_todos_clientes():
    conn = sqlite3.connect(BANCO_DADOS_SQLITE)
    df = pd.read_sql_query("SELECT usuario_email, nome, email_cliente, telefone, cidade FROM clientes", conn)
    conn.close()
    return df

# --- FUNÇÃO DE FUNDO PERSONALIZADO (CSS / BASE64) ---
def definir_fundo_personalizado_base64(img_bytes=None, url_imagem=None):
    if img_bytes:
        encoded = base64.b64encode(img_bytes).decode()
        bg_val = f"url('data:image/jpeg;base64,{encoded}')"
    elif url_imagem:
        bg_val = f"url('{url_imagem}')"
    else:
        return
        
    css = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(10, 15, 30, 0.75), rgba(10, 15, 30, 0.85)), {bg_val};
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- SISTEMA DE AUTENTICAÇÃO ---
def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario_email" not in st.session_state:
        st.session_state.usuario_email = None

    if not st.session_state.autenticado:
        definir_fundo_personalizado_base64(url_imagem="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1920&auto=format&fit=crop")
        
        st.markdown("<h2 style='text-align: center; color: #ffffff;'>🔐 Área Restrita - Luminotécnica (Teste SQLite)</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #cbd5e0;'>Ambiente de Testes com Banco SQLite Local. Crie sua conta e ganhe <b>24 horas de teste gratuito</b>.</p>", unsafe_allow_html=True)
        
        tab_login, tab_cadastro, tab_planos = st.tabs(["🔑 Fazer Login", "📝 Criar Conta Grátis (Teste 24h)", "💳 Assinar (R$ 19,90/mês)"])
        
        with tab_login:
            with st.form("form_login_teste"):
                email_input = st.text_input("E-mail cadastrado", value="").strip().lower()
                senha_input = st.text_input("Senha", type="password", value="").strip()
                btn_entrar = st.form_submit_button("Entrar no Sistema")
                
                if btn_entrar:
                    user_data = db_obter_usuario(email_input)
                    if user_data and user_data["senha"] == senha_input:
                        agora = datetime.datetime.now()
                        tempo_criacao = user_data["criacao"]
                        horas_decorridas = (agora - tempo_criacao).total_seconds() / 3600
                        
                        if user_data["tipo"] == "admin" or horas_decorridas <= 24 or user_data["assinante"]:
                            st.session_state.autenticado = True
                            st.session_state.usuario_email = email_input
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("⏰ Seu período de teste de 24 horas expirou. Vá na aba 'Assinar' para continuar usando.")
                    else:
                        st.error("E-mail ou senha incorretos, ou usuário não encontrado.")

        with tab_cadastro:
            st.markdown("### ⚡ Comece a usar agora mesmo")
            with st.form("form_cadastro_teste"):
                novo_email = st.text_input("Seu E-mail principal", value="").strip().lower()
                nova_senha = st.text_input("Crie uma Senha", type="password", value="").strip()
                btn_cadastrar = st.form_submit_button("Criar Conta e Iniciar Teste Grátis")
                
                if btn_cadastrar:
                    if novo_email and nova_senha:
                        if db_obter_usuario(novo_email):
                            st.warning("Este e-mail já está cadastrado. Faça login na primeira aba.")
                        else:
                            sucesso = db_salvar_usuario(novo_email, nova_senha, tipo="cliente", assinante=False)
                            if sucesso:
                                st.session_state.autenticado = True
                                st.session_state.usuario_email = novo_email
                                st.success("Conta criada com sucesso no SQLite! Seu teste de 24 horas começou.")
                                st.rerun()
                            else:
                                st.error("Erro ao salvar usuário no banco SQLite.")
                    else:
                        st.error("Preencha todos os campos para criar a conta.")

        with tab_planos:
            st.markdown("### 🚀 Assinatura Profissional")
            st.info("💡 **Apenas R$ 19,90 / mês** — Cancele quando quiser.")
            link_mercado_pago = "https://mpago.la/2sbQvQ9"
            st.link_button("💳 Assinar Agora por R$ 19,90/mês via Mercado Pago", link_mercado_pago, use_container_width=True)
                    
        return False

    return True

if not verificar_autenticacao():
    st.stop()

email_atual = st.session_state.usuario_email
usuario_logado_obj = db_obter_usuario(email_atual)
eh_admin = usuario_logado_obj and usuario_logado_obj["tipo"] == "admin"

banco_clientes_usuario = db_obter_clientes(email_atual)

# --- SE O USUÁRIO FOR ADMIN, EXIBIR PAINEL DE CONTROLE NO TOPO ---
if eh_admin:
    with st.expander("👑 PAINEL DE CONTROLE ADMINISTRATIVO (Ver Logins e Cadastros)", expanded=False):
        st.markdown("### 👥 Usuários Cadastrados no Banco SQLite")
        df_usuarios = db_listar_todos_usuarios()
        st.dataframe(df_usuarios, use_container_width=True)
        
        st.markdown("### 📇 Todos os Clientes Salvos")
        df_clientes = db_listar_todos_clientes()
        st.dataframe(df_clientes, use_container_width=True)
        st.markdown("---")

# --- TABELA DE NORMAS (NBR ISO/CIE 8995-1) ---
TABELA_NORMA = {
    "Residências - Salas de Estar / Dormitórios": 150,
    "Residências - Cozinhas / Banheiros": 300,
    "Escritórios - Geral / Digitação": 500,
    "Escritórios - Reunião / Conferência": 300,
    "Comércio - Lojas de Departamento / Varejo": 500,
    "Comércio - Supermercados / Áreas de Circulação": 300,
    "Indústria - Montagem Grosso (Ex: Mecânica Pesada)": 200,
    "Indústria - Montagem Média (Ex: Eletrônicos)": 500,
    "Escolas - Salas de Aula / Laboratórios": 300,
    "Hospitais - Enfermarias": 100,
    "Garagens - Áreas de Estacionamento / Circulação": 75,
}

if "banco_luminarias" not in st.session_state:
    st.session_state.banco_luminarias = [
        {"Fabricante": "Ecolume", "Modelo": "Painel LED 24W Redondo Sobrepor", "Lumens": 1920, "Potencia": 24.0, "Tipo": "Painel/Luminária"},
        {"Fabricante": "Philips", "Modelo": "Painel LED 18W Quadrado Embutir", "Lumens": 1440, "Potencia": 18.0, "Tipo": "Painel/Luminária"},
        {"Fabricante": "Philips", "Modelo": "Painel LED 24W Redondo Embutir", "Lumens": 1920, "Potencia": 24.0, "Tipo": "Painel/Luminária"},
        {"Fabricante": "Osram", "Modelo": "Luminária LED Estanque 36W", "Lumens": 3600, "Potencia": 36.0, "Tipo": "Painel/Luminária"},
        {"Fabricante": "Taschibra", "Modelo": "Painel LED Slim 12W Quadrado", "Lumens": 960, "Potencia": 12.0, "Tipo": "Painel/Luminária"},
    ]

# --- FUNÇÃO DE GERAÇÃO DO RELATÓRIO EM WORD (DOCX) ---
def gerar_docx_consolidado(dados_cliente, dados_profissional, lista_ambientes, logo_file=None):
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

    HEX_COR_PRIMARIA = "1A365D"
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
    p_t = doc.add_paragraph()
    r_t = p_t.add_run("RELATÓRIO LUMINOTÉCNICO EXECUTIVO CONSOLIDADO (TESTE SQLITE)")
    r_t.bold = True
    r_t.font.size = Pt(14)
    r_t.font.color.rgb = COR_TEXTO_TITULO

    p_sub = doc.add_paragraph()
    p_sub.add_run(f"Cliente / Empreendimento: {dados_cliente.get('Nome', 'Cliente Geral')} | Método dos Lúmens\n")
    p_sub.add_run(f"Responsável Técnico: {dados_profissional.get('nome', 'Não informado')} — Registro: {dados_profissional.get('registro', 'Não informado')} | Data de Emissão: {data_atual_str}\n")
    p_sub.add_run(f"Norma de Referência: NBR ISO/CIE 8995-1 & NBR 5410")
    for r in p_sub.runs:
        r.font.size = Pt(9)

    doc.add_paragraph()

    for idx, amb in enumerate(lista_ambientes):
        if idx > 0:
            doc.add_page_break()

        p_amb = doc.add_paragraph()
        r_amb = p_amb.add_run(f"AMBIENTE: {amb['nome'].upper()}")
        r_amb.bold = True
        r_amb.font.size = Pt(11.5)
        r_amb.font.color.rgb = COR_TEXTO_TITULO

        t1 = doc.add_table(rows=15, cols=4)
        t1.alignment = WD_TABLE_ALIGNMENT.CENTER
        t1.autofit = False
        w1 = [Inches(2.5), Inches(1.0), Inches(1.8), Inches(1.2)]

        headers1 = ["Parâmetro", "Símbolo", "Valor Adotado", "Unidade"]
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
            ("Comprimento / Largura / Pé-Direito", "C x L x H", f"{amb['comp']:.2f} x {amb['larg']:.2f} x {amb['pe_direito']:.2f}", "m"),
            ("Área Total do Piso", "A", f"{amb['area']:.2f}", "m²"),
            ("Índice do Recinto (Geometria)", "k", f"{amb['k_indice']:.2f}", "—"),
            ("Iluminância Requerida (Normativa)", "Ereq", f"{amb['lux_req']:.2f}", "lx"),
            ("Fatores de Utilização e Depreciação", "u / d", f"u = {amb['fator_u']:.2f} | d = {amb['fator_d']:.2f}", "—"),
            ("Fonte Luminosa / Equipamento", "Φ", f"{amb['fluxo_unidade_rel']:,.2f} lm".replace(",", "."), amb['modelo_lum']),
            ("Quantidade de Equipamentos Adotada", "N", f"{amb['qtd_real_str']}", amb['unidade_medida_qtd']),
            ("Arranjo Luminoso Distribuído", "—", f"{amb['arranjo_str']}", "arr."),
            ("Espaçamentos e Afastamentos", "dc / dl", f"Entre: {amb['dist_c_entre']:.2f}m / {amb['dist_l_entre']:.2f}m", "m"),
            ("Iluminância Real Alcançada", "Ereal", f"{amb['lux_real']:.2f}", "lx"),
            ("Potência Total Instalada e DPI", "P / DPI", f"{amb['pot_total']:.2f} W | {amb['dpi']:.2f} W/m²", "W / W/m²"),
            ("Status Final de Conformidade", "—", "CONFORME (Aprovado)" if amb['conforme'] else "NÃO CONFORME", "—"),
            ("Responsabilidade Técnica", "ART", f"{dados_profissional.get('nome', 'N/A')}", "—")
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

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# --- INTERFACE PRINCIPAL ---
st.title("💡 Luminotécnica Profissional — Teste SQLite")
st.markdown(f"**Sessão Ativa (SQLite):** {email_atual}")

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

st.markdown("---")

# --- MÓDULO DE CADASTRO DE CLIENTES ---
st.markdown("### 📇 Cadastro e Seleção de Clientes (Salvo no SQLite)")
with st.expander("➕ Cadastrar Novo Cliente no Sistema"):
    with st.form("form_novo_cliente_sqlite"):
        col_nc1, col_nc2 = st.columns(2)
        with col_nc1:
            cad_nome_cli = st.text_input("Nome / Razão Social do Cliente")
            cad_tel_cli = st.text_input("Telefone / WhatsApp")
        with col_nc2:
            cad_email_cli = st.text_input("E-mail do Cliente")
            cad_cidade_cli = st.text_input("Cidade / Estado (Ex: Rio de Janeiro - RJ)")
            
        btn_salvar_cliente = st.form_submit_button("Salvar Cliente no SQLite")
        if btn_salvar_cliente:
            if cad_nome_cli.strip() != "":
                db_adicionar_cliente(email_atual, cad_nome_cli, cad_email_cli, cad_tel_cli, cad_cidade_cli)
                st.success(f"Cliente '{cad_nome_cli}' salvo permanentemente no banco SQLite!")
                st.rerun()
            else:
                st.error("O nome do cliente é obrigatório.")

banco_clientes_usuario = db_obter_clientes(email_atual)
lista_nomes_clientes = [c["Nome"] for c in banco_clientes_usuario]
cliente_selecionado_nome = st.selectbox("Selecione o Cliente para este Projeto", lista_nomes_clientes)
cliente_dados_obj = next((c for c in banco_clientes_usuario if c["Nome"] == cliente_selecionado_nome), banco_clientes_usuario[0])

st.markdown("---")
st.markdown(f"### 🛋️ Ambiente de Cálculo Ativo para: **{cliente_dados_obj['Nome']}**")

with st.expander("⚙️ Cadastrar Nova Luminária no Banco"):
    with st.form("form_nova_lum_sqlite"):
        col_fl1, col_fl2, col_fl3, col_fl4, col_fl5 = st.columns(5)
        with col_fl1:
            novo_tipo = st.selectbox("Categoria", ["Painel/Luminária", "Industrial"])
        with col_fl2:
            novo_fab = st.text_input("Fabricante", value="Philips")
        with col_fl3:
            novo_mod = st.text_input("Modelo", value="Painel LED")
        with col_fl4:
            novo_lum = st.number_input("Fluxo (lm)", value=1440.0, step=50.0)
        with col_fl5:
            nova_pot = st.number_input("Potência (W)", value=18.0, step=1.0)
            
        btn_salvar_lum = st.form_submit_button("Salvar no Banco")
        if btn_salvar_lum:
            st.session_state.banco_luminarias.append({
                "Fabricante": novo_fab, "Modelo": novo_mod, "Lumens": novo_lum, "Potencia": nova_pot, "Tipo": novo_tipo
            })
            st.success("Luminária cadastrada com sucesso!")

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
        st.markdown(f"#### 📐 Ambiente: {amb_atual['nome']}")
        
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            novo_nome = st.text_input("Nome do Ambiente", value=amb_atual['nome'], key=f"nome_amb_{amb_atual['id']}")
        with col_n2:
            tipo_atividade = st.selectbox("Atividade / Norma (NBR ISO/CIE 8995-1)", list(TABELA_NORMA.keys()), key=f"ativ_{amb_atual['id']}")

        lux_req = float(TABELA_NORMA[tipo_atividade])

        banco_ativo = st.session_state.banco_luminarias
        opcoes_banco_str = [f"{l['Fabricante']} - {l['Modelo']} ({l['Lumens']} lm / {l['Potencia']} W)" for l in banco_ativo]
        escolha_banco = st.selectbox("Selecionar Equipamento", opcoes_banco_str, key=f"lum_escolha_{amb_atual['id']}")
        
        idx_escolhido = opcoes_banco_str.index(escolha_banco)
        lum_sel = banco_ativo[idx_escolhido]
        fluxo_base, potencia_base = lum_sel["Lumens"], lum_sel["Potencia"]
        modelo_desc_relatorio = f"[Painel/Luminária] {lum_sel['Fabricante']} - {lum_sel['Modelo']}"

        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            comp = st.number_input("Comprimento (m)", value=3.0, step=0.1, key=f"comp_{amb_atual['id']}")
            pe_direito = st.number_input("Pé-Direito (m)", value=2.9, step=0.1, key=f"pd_{amb_atual['id']}")
        with col_g2:
            larg = st.number_input("Largura (m)", value=2.0, step=0.1, key=f"larg_{amb_atual['id']}")
            hp = st.number_input("Plano de Trabalho (m)", value=0.75, step=0.05, key=f"hp_{amb_atual['id']}")
        with col_g3:
            hp_desc = st.number_input("Rebaixamento / Suspensão (m)", value=0.0, step=0.05, key=f"hdesc_{amb_atual['id']}")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fator_u = st.slider("Fator de Utilização (u)", 0.3, 0.8, 0.70, 0.05, key=f"fu_{amb_atual['id']}")
        with col_f2:
            fator_d = st.slider("Fator de Depreciação (d)", 0.5, 0.9, 0.80, 0.05, key=f"fd_{amb_atual['id']}")

        area = comp * larg
        hu = pe_direito - hp - hp_desc
        k_indice = (comp * larg) / (hu * (comp + larg)) if hu > 0 else 1.0
        fluxo_req = (lux_req * area) / (fator_u * fator_d) if (fator_u * fator_d) > 0 else 0

        qtd_teorica = fluxo_req / fluxo_base if fluxo_base > 0 else 0
        qtd_min_sugerida = max(1, math.ceil(qtd_teorica))

        col_arr1, col_arr2 = st.columns(2)
        with col_arr1:
            linhas_man = st.number_input("Quantidade de Linhas", min_value=1, value=1, step=1, key=f"linhas_man_{amb_atual['id']}")
        with col_arr2:
            colunas_man = st.number_input("Quantidade de Colunas", min_value=1, value=2, step=1, key=f"colunas_man_{amb_atual['id']}")
        
        qtd_real = linhas_man * colunas_man
        arranjo_str = f"{linhas_man} Linhas x {colunas_man} Colunas"

        dist_c_entre = comp / colunas_man if colunas_man > 0 else comp
        dist_l_entre = larg / linhas_man if linhas_man > 0 else larg

        fluxo_instalado = qtd_real * fluxo_base
        pot_total = qtd_real * potencia_base
        lux_real = (fluxo_instalado * fator_u * fator_d) / area if area > 0 else 0
        dpi = pot_total / area if area > 0 else 0
        conforme = lux_real >= lux_req

        lista_calculos_ambientes.append({
            "id": amb_atual["id"],
            "nome": novo_nome,
            "comp": comp,
            "larg": larg,
            "pe_direito": pe_direito,
            "area": area,
            "k_indice": k_indice,
            "lux_req": lux_req,
            "fluxo_unidade_rel": fluxo_base,
            "fator_u": fator_u,
            "fator_d": fator_d,
            "modelo_lum": modelo_desc_relatorio,
            "qtd_real_str": str(int(qtd_real)),
            "unidade_medida_qtd": "un",
            "arranjo_str": arranjo_str,
            "dist_c_entre": dist_c_entre,
            "dist_l_entre": dist_l_entre,
            "lux_real": lux_real,
            "pot_total": pot_total,
            "dpi": dpi,
            "conforme": conforme
        })
        st.markdown("---")

st.subheader("3. Emissão de Relatório de Teste (.docx)")
if st.button("📄 Gerar Relatório Word (.docx) - SQLite", use_container_width=True):
    try:
        dados_prof_dict = {
            "nome": prof_nome if prof_nome else "Não informado",
            "registro": prof_registro if prof_registro else "Não informado"
        }
        logo_bytes = io.BytesIO(logo_upload.getvalue()) if logo_upload is not None else None
        arquivo_docx_bytes = gerar_docx_consolidado(cliente_dados_obj, dados_prof_dict, lista_ambientes=lista_calculos_ambientes, logo_file=logo_bytes)
        
        st.success("Relatório gerado com sucesso!")
        st.download_button(
            label="📥 Baixar Relatório Word (.docx)",
            data=arquivo_docx_bytes,
            file_name=f"Relatorio_Teste_{cliente_dados_obj['Nome'].replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erro ao gerar documento: {e}")
