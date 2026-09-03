import streamlit as st
import sqlite3
import hashlib
import json
import math
import datetime
import random
import uuid
import io
import pandas as pd
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import mercadopago

# --- CONFIGURAÇÕES GLOBAIS ---
ARQUIVO_DB_USUARIOS = "usuarios_sistema.db"
EMAIL_DONO_MESTRE = "jbengrj@gmai.com"
ACCESS_TOKEN_MP = "APP_USR-556244363968444-090314-235a12713b7c8a5fe8a8747b0e596775-3660992457"
sdk = mercadopago.SDK(ACCESS_TOKEN_MP)

# --- BANCO DE DADOS DE USUÁRIOS E LICENÇAS (SQLITE) ---
def inicializar_db_usuarios():
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            senha_hash TEXT NOT NULL,
            nome TEXT,
            is_pro INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            token_recuperacao TEXT,
            sessao_ativa TEXT
        )
    ''')
    
    # Tabela de Luminárias por Usuário (Privadas ou Globais)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS luminarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_usuario TEXT,
            fabricante TEXT,
            modelo TEXT,
            lumens REAL,
            potencia REAL,
            global INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    
    # Garante que o Dono Mestre exista e seja Admin/Pro automaticamente
    cursor.execute("SELECT email FROM usuarios WHERE email = ?", (EMAIL_DONO_MESTRE,))
    if not cursor.fetchone():
        senha_dono_hash = hashlib.sha256("peb@engenharia".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (email, senha_hash, nome, is_pro, is_admin) 
            VALUES (?, ?, ?, 1, 1)
        ''', (EMAIL_DONO_MESTRE, senha_dono_hash, "Jefferson Barcellos (Dono)"))
        conn.commit()
        
    conn.close()

inicializar_db_usuarios()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def cadastrar_usuario(email, senha, nome):
    try:
        conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
        cursor = conn.cursor()
        is_adm = 1 if email.strip().lower() == EMAIL_DONO_MESTRE.lower() else 0
        is_pr = 1 if is_adm else 0
        
        cursor.execute("INSERT INTO usuarios (email, senha_hash, nome, is_pro, is_admin) VALUES (?, ?, ?, ?, ?)",
                       (email.strip().lower(), hash_senha(senha), nome, is_pr, is_adm))
        conn.commit()
        conn.close()
        return True, "Cadastro realizado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Este e-mail já está cadastrado."

def verificar_login(email, senha):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    email_limpo = email.strip().lower()
    cursor.execute("SELECT senha_hash, nome, is_pro, is_admin FROM usuarios WHERE email = ?", (email_limpo,))
    resultado = cursor.fetchone()
    
    if resultado and resultado[0] == hash_senha(senha):
        # Gera um novo token de sessão única para derrubar outros acessos simultâneos
        nova_sessao = str(uuid.uuid4())
        cursor.execute("UPDATE usuarios SET sessao_ativa = ? WHERE email = ?", (nova_sessao, email_limpo))
        conn.commit()
        conn.close()
        return True, resultado[1], bool(resultado[2]), bool(resultado[3]), nova_sessao
        
    conn.close()
    return False, "", False, False, ""

def validar_sessao_ativa(email, token_atual):
    if not email or not token_atual:
        return True
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("SELECT sessao_ativa FROM usuarios WHERE email = ?", (email,))
    res = cursor.fetchone()
    conn.close()
    if res and res[0] != token_atual:
        return False
    return True

def atualizar_status_pro(email, status_pro):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET is_pro = ? WHERE email = ?", (1 if status_pro else 0, email))
    conn.commit()
    conn.close()

def gerar_token_recuperacao(email):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM usuarios WHERE email = ?", (email,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return None, "E-mail não encontrado no sistema."
    
    token = str(random.randint(100000, 999999))
    cursor.execute("UPDATE usuarios SET token_recuperacao = ? WHERE email = ?", (token, email))
    conn.commit()
    conn.close()
    return token, "Token gerado com sucesso."

def redefinir_senha_com_token(email, token_informado, nova_senha):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("SELECT token_recuperacao FROM usuarios WHERE email = ?", (email,))
    res = cursor.fetchone()
    
    if not res or res[0] != token_informado:
        conn.close()
        return False, "Token inválido ou incorreto."
    
    nova_hash = hash_senha(nova_senha)
    cursor.execute("UPDATE usuarios SET senha_hash = ?, token_recuperacao = NULL WHERE email = ?", (nova_hash, email))
    conn.commit()
    conn.close()
    return True, "Senha redefinida com sucesso!"

# --- GERENCIAMENTO DE LUMINÁRIAS POR USUÁRIO ---
def carregar_luminarias_usuario(email_usuario, is_admin):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    if is_admin:
        # Dono vê tudo (as globais e todas as cadastradas por qualquer usuário)
        cursor.execute("SELECT id, email_usuario, fabricante, modelo, lumens, potencia, global FROM luminarias")
    else:
        # Usuário comum vê as globais padrão + as que ele mesmo cadastrou
        cursor.execute("SELECT id, email_usuario, fabricante, modelo, lumens, potencia, global FROM luminarias WHERE global = 1 OR email_usuario = ?", (email_usuario,))
    
    rows = cursor.fetchall()
    conn.close()
    
    lista = []
    for r in rows:
        lista.append({
            "id": r[0],
            "email_criador": r[1],
            "Fabricante": r[2],
            "Modelo": r[3],
            "Lumens": r[4],
            "Potencia": r[5],
            "Global": bool(r[6])
        })
    
    # Se a lista estiver vazia para o usuário, injeta padrões globais iniciais
    if not lista and not is_admin:
        padroes = [
            ("Genérica", "Painel LED Embutir 18W", 1440.0, 18.0),
            ("Philips", "Ledinaire Downlight 20W", 1800.0, 20.0),
            ("Ledvance", "Painel Superior 30W", 2700.0, 30.0)
        ]
        conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
        cursor = conn.cursor()
        for fab, mod, lum, pot in padroes:
            cursor.execute("INSERT INTO luminarias (email_usuario, fabricante, modelo, lumens, potencia, global) VALUES (?, ?, ?, ?, ?, 1)",
                           ("sistema@global", fab, mod, lum, pot))
        conn.commit()
        conn.close()
        return carregar_luminarias_usuario(email_usuario, is_admin)
        
    return lista

def salvar_luminaria_banco(email_usuario, fabricante, modelo, lumens, potencia, global_flag=0):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO luminarias (email_usuario, fabricante, modelo, lumens, potencia, global) VALUES (?, ?, ?, ?, ?, ?)",
                   (email_usuario, fabricante, modelo, lumens, potencia, 1 if global_flag else 0))
    conn.commit()
    conn.close()

# --- FUNÇÃO PARA GERAR PREFERÊNCIA DE PAGAMENTO NO MERCADO PAGO ---
def criar_link_pagamento_mp(email_usuario):
    try:
        url_retorno = "https://calculo-luminotecnico.streamlit.app"
        preference_data = {
            "items": [{"title": "Licença PRO - Sistema Luminotécnico", "quantity": 1, "unit_price": 49.90, "currency_id": "BRL"}],
            "payer": {"email": email_usuario},
            "back_urls": {"success": f"{url_retorno}/?pagamento=sucesso", "failure": f"{url_retorno}/?pagamento=falha", "pending": f"{url_retorno}/?pagamento=pendente"},
            "auto_return": "approved",
        }
        preference_response = sdk.preference().create(preference_data)
        return preference_response["response"].get("init_point")
    except Exception as e:
        return None

# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Sistema Luminotécnico SaaS", layout="wide")

# Gerenciamento de Sessão de Login
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_email" not in st.session_state:
    st.session_state["usuario_email"] = ""
if "usuario_nome" not in st.session_state:
    st.session_state["usuario_nome"] = ""
if "is_pro" not in st.session_state:
    st.session_state["is_pro"] = False
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "token_sessao" not in st.session_state:
    st.session_state["token_sessao"] = ""

# Validação de Sessão Concorrente (Derruba se logou em outro dispositivo)
if st.session_state["autenticado"]:
    if not validar_sessao_ativa(st.session_state["usuario_email"], st.session_state["token_sessao"]):
        st.session_state["autenticado"] = False
        st.error("⚠️ Sua conta foi acessada em outro dispositivo. Esta sessão foi encerrada.")
        st.stop()

# --- CAPTURA DE RETORNO DO PAGAMENTO ---
query_params = st.query_params
if "pagamento" in query_params and query_params["pagamento"] == "sucesso":
    if st.session_state["autenticado"] and not st.session_state["is_pro"]:
        atualizar_status_pro(st.session_state["usuario_email"], True)
        st.session_state["is_pro"] = True
        st.success("🎉 Pagamento aprovado com sucesso! Sua conta agora é PRO.")

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

def adicionar_relatorio_ambiente(doc, dados_cliente, dados_prof, d):
    data_emissao = datetime.datetime.now().strftime("%d/%m/%Y")
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
    run_sub = p_sub.add_run(f"Cliente / Empreendimento: {dados_cliente['nome']} | Método dos Lúmens")
    run_sub.font.size = Pt(10)
    run_sub.italic = True
    run_sub.font.color.rgb = RGBColor(89, 89, 89)

    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_info.paragraph_format.space_after = Pt(10)
    p_info.add_run(f"Responsável Técnico: {dados_prof['nome']} ({dados_prof['titulo']}) — {dados_prof['registro']} | Data de Emissão: {data_emissao}\n")
    p_info.runs[0].bold = True
    run_norma = p_info.add_run("Norma de Referência: NBR ISO/CIE 8995-1 & NBR 5410")
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

    adicionar_secao_tabela("1. Identificação e Dados Geométricos", ["Parâmetro", "Símbolo", "Valor", "Unidade"], [Inches(3.0), Inches(0.8), Inches(1.2), Inches(1.5)], [
        ["Nome do Ambiente", "—", d['nome'], "—"],
        ["Comprimento", "C", f"{d['comp']:.2f}", "m"],
        ["Largura", "L", f"{d['larg']:.2f}", "m"],
        ["Pé-Direito Total", "H", f"{d['pe_direito']:.2f}", "m"],
        ["Plano de Trabalho", "hp", f"{d['hp']:.2f}", "m"],
        ["Área Total", "A", f"{d['area']:.2f}", "m²"],
        ["Altura Útil", "hu", f"{d['hu']:.2f}", "m"]
    ])
    adicionar_secao_tabela("2. Parâmetros Luminotécnicos", ["Parâmetro Técnico", "Símbolo", "Valor Adotado", "Norma"], [Inches(2.5), Inches(0.8), Inches(1.2), Inches(2.0)], [
        ["Iluminância Requerida", "Ereq", f"{d['lux_req']:.0f} lx", "NBR ISO/CIE 8995-1"],
        ["Fluxo da Luminária", "Φlâmpada", f"{fluxo_fmt} lm", d.get('modelo_lum', 'Manual')],
        ["Potência Unitária", "Punit", f"{d['potencia']:.1f} W", "Consumo (W)"],
        ["Fator de Utilização", "u", f"{d['fator_u']:.2f}", d['desc_utilizacao']],
        ["Fator de Depreciação", "d", f"{d['fator_d']:.2f}", d['desc_depreciacao']]
    ])
    adicionar_secao_tabela("3. Resultados do Dimensionamento", ["Item de Cálculo", "Valor Calculado", "Valor Adotado", "Unidade"], [Inches(3.0), Inches(1.2), Inches(1.3), Inches(1.0)], [
        ["Fluxo Requerido", f"{d['fluxo_req']:.2f}", "—", "lm"],
        ["Qtd. de Luminárias", f"{d['qtd_teorica']:.2f}", f"{d['qtd_real']}", "un"],
        ["Iluminância Real", "—", f"{d['lux_real']:.2f}", "lx"],
        ["Potência Total", "—", f"{d['pot_total']:.2f}", "W"],
        ["DPI", "—", f"{d['dpi']:.2f}", "W/m²"]
    ])
    
    doc.add_heading("4. Parecer Técnico", level=2)
    p1 = doc.add_paragraph()
    p1.add_run("• Status Final: ").bold = True
    run_status = p1.add_run("CONFORME (Aprovado)." if d['conforme'] else "NÃO CONFORME.")
    run_status.bold = True
    run_status.font.color.rgb = RGBColor(38, 128, 0) if d['conforme'] else RGBColor(200, 0, 0)

def gerar_docx_lote(dados_cliente, dados_prof, lista_dados_ambientes, logo_file=None):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(0.8)
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

# --- APLICAÇÃO DE IMAGEM DE FUNDO NA TELA DE LOGIN ---
if not st.session_state["autenticado"]:
    url_imagem_fundo = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1600&auto=format&fit=crop"
    st.markdown(f"""
    <style>
    .stMain {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{url_imagem_fundo}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL: AUTENTICAÇÃO E LOGIN ---
st.sidebar.header("🔐 Portal do Cliente")

if not st.session_state["autenticado"]:
    st.sidebar.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 220" width="100%" height="110">
        <path fill="none" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" d="M 195 105 C 180 90 175 70 175 55 C 175 30 195 15 225 15 C 255 15 275 30 275 55 C 275 70 270 90 255 105 Z M 210 105 L 240 105 M 215 117 L 235 117 M 219 129 L 231 129" />
      </svg>
    </div>
    """, unsafe_allow_html=True)

    aba_login, aba_cadastro, aba_recuperar = st.sidebar.tabs(["Entrar", "Criar Conta", "Recuperar"])
    
    with aba_login:
        st.subheader("Acessar Sistema")
        email_login = st.text_input("E-mail", key="email_l")
        senha_login = st.text_input("Senha", type="password", key="senha_l")
        if st.button("Entrar", use_container_width=True):
            sucesso, nome_cad, status_pro_db, status_admin_db, token_sessao_nova = verificar_login(email_login, senha_login)
            if sucesso:
                st.session_state["autenticado"] = True
                st.session_state["usuario_email"] = email_login.strip().lower()
                st.session_state["usuario_nome"] = nome_cad
                st.session_state["is_pro"] = status_pro_db
                st.session_state["is_admin"] = status_admin_db
                st.session_state["token_sessao"] = token_sessao_nova
                st.success("Login efetuado com sucesso!")
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")
                
    with aba_cadastro:
        st.subheader("Novo Cadastro")
        nome_cad_input = st.text_input("Nome Completo", key="nome_c")
        email_cad_input = st.text_input("E-mail", key="email_c")
        senha_cad_input = st.text_input("Senha", type="password", key="senha_c")
        if st.button("Cadastrar", use_container_width=True):
            if nome_cad_input and email_cad_input and senha_cad_input:
                ok, msg = cadastrar_usuario(email_cad_input, senha_cad_input, nome_cad_input)
                if ok:
                    st.success(msg + " Faça login na aba 'Entrar'.")
                else:
                    st.error(msg)
            else:
                st.warning("Preencha todos os campos.")

    with aba_recuperar:
        st.subheader("Recuperar Senha")
        email_rec = st.text_input("Seu e-mail cadastrado", key="email_rec")
        if "token_gerado_temp" not in st.session_state:
            st.session_state["token_gerado_temp"] = ""
        if st.button("Gerar Código", use_container_width=True):
            if email_rec:
                tk, msg_tk = gerar_token_recuperacao(email_rec)
                if tk:
                    st.session_state["token_gerado_temp"] = tk
                    st.session_state["email_alvo_rec"] = email_rec
                    st.success(f"Código: **{tk}**")
                else:
                    st.error(msg_tk)
            else:
                st.warning("Informe o e-mail.")
        if st.session_state["token_gerado_temp"]:
            token_digitado = st.text_input("Código de 6 Dígitos", key="tk_dig")
            nova_senha_rec = st.text_input("Nova Senha", type="password", key="ns_rec")
            if st.button("Redefinir", use_container_width=True):
                ok_red, msg_red = redefinir_senha_com_token(st.session_state["email_alvo_rec"], token_digitado, nova_senha_rec)
                if ok_red:
                    st.success(msg_red)
                    st.session_state["token_gerado_temp"] = ""
                else:
                    st.error(msg_red)
                    
    st.markdown("""
    <div style="text-align: center; color: white; padding: 20px;">
        <h1 style="font-size: 2.2rem;">⚡ Sistema Luminotécnico</h1>
        <p>Faça login na barra lateral para acessar o painel completo de cálculos e laudos seguros.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Se logado:
st.sidebar.success(f"Olá, **{st.session_state['usuario_nome']}**!")
plano_atual_str = "👑 ADMINISTRADOR (Dono)" if st.session_state["is_admin"] else ("🚀 PRO" if st.session_state["is_pro"] else "📌 Básico")
st.sidebar.info(f"Perfil: **{plano_atual_str}**")

if not st.session_state["is_admin"] and not st.session_state["is_pro"]:
    if st.sidebar.button("💎 Pagar R$ 49,90 via Mercado Pago", use_container_width=True):
        link_mp = criar_link_pagamento_mp(st.session_state["usuario_email"])
        if link_mp:
            st.sidebar.markdown(f"🔗 [Abrir Checkout]({link_mp})", unsafe_allow_html=True)

if st.sidebar.button("🚪 Sair da Conta", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

# --- PAINEL DO DONO (ADMIN) EXCLUSIVO ---
if st.session_state["is_admin"]:
    with st.expander("👑 Painel de Controle do Dono (Administrador)", expanded=False):
        st.write("Gerenciamento geral de usuários cadastrados no banco de dados.")
        conn_adm = sqlite3.connect(ARQUIVO_DB_USUARIOS)
        df_usuarios = pd.read_sql("SELECT email, nome, is_pro, is_admin FROM usuarios", conn_adm)
        conn_adm.close()
        st.dataframe(df_usuarios, use_container_width=True)
        
        email_alvo_pro = st.text_input("E-mail do usuário para alterar status PRO", placeholder="usuario@email.com")
        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            if st.button("Conceder PRO Manualmente"):
                if email_alvo_pro:
                    atualizar_status_pro(email_alvo_pro.strip().lower(), True)
                    st.success(f"Usuário {email_alvo_pro} agora é PRO!")
                    st.rerun()
        with col_adm2:
            if st.button("Remover PRO"):
                if email_alvo_pro:
                    atualizar_status_pro(email_alvo_pro.strip().lower(), False)
                    st.warning(f"Status PRO removido de {email_alvo_pro}.")
                    st.rerun()

st.title("⚡ Sistema Luminotécnico Profissional")
st.write("Ambiente seguro com dados isolados e proteção de relatórios por usuário.")

st.sidebar.markdown("---")
st.sidebar.header("🎨 Personalização")
logo_upload = st.sidebar.file_uploader("Sua Logo", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.header("👨‍💻 Responsável Técnico")
titulo_prof = st.sidebar.selectbox("Categoria", ["Engenheiro(a) Eletricista", "Arquiteto(a) e Urbanista", "Engenheiro(a) Civil"])
prof_nome = st.sidebar.text_input("Nome do Profissional", "")
prof_registro = st.sidebar.text_input("Registro (CREA / CAU)", "")

TABELA_NORMA = {
    "Dormitórios / Suítes": 200,
    "Salas de Estar / Jantar": 150,
    "Cozinhas / Banheiros": 300,
    "Escritórios - Trabalho": 500,
    "Corredores e Circulação": 100,
}

# --- BANCO DE DADOS DE LUMINÁRIAS ISOLADO / COMPARTILHADO ---
banco_luminarias_usuario = carregar_luminarias_usuario(st.session_state["usuario_email"], st.session_state["is_admin"])

with st.expander("📚 Banco de Luminárias (Cadastrar / Consultar)", expanded=False):
    st.write("Cadastre novas luminárias. Elas ficam privadas para você (ou visíveis para todos se você for o Administrador).")
    col_cad1, col_cad2 = st.columns(2)
    with col_cad1:
        novo_fab = st.text_input("Fabricante", placeholder="Ex: Philips")
        novo_mod = st.text_input("Modelo", placeholder="Ex: Painel 18W")
    with col_cad2:
        novo_lum = st.number_input("Fluxo (lm)", value=1500.0, step=100.0)
        novo_pot = st.number_input("Potência (W)", value=18.0, step=1.0)
    
    if st.button("💾 Salvar Luminária"):
        if novo_fab and novo_mod:
            salvar_luminaria_banco(st.session_state["usuario_email"], novo_fab, novo_mod, novo_lum, novo_pot, global_flag=st.session_state["is_admin"])
            st.success("Luminária salva com sucesso!")
            st.rerun()
        else:
            st.warning("Preencha os campos.")
            
    st.markdown("##### Catálogo Disponível para sua Conta:")
    st.dataframe(pd.DataFrame(banco_luminarias_usuario), use_container_width=True)

st.markdown("---")
st.subheader("1. Identificação Geral do Projeto")
cli_nome = st.text_input("Cliente / Empreendimento", "", placeholder="Nome do Cliente")

st.markdown("---")
st.subheader("2. Gerenciamento de Ambientes")

if "ambientes_lista" not in st.session_state:
    st.session_state["ambientes_lista"] = [{"id": 1, "nome": "Ambiente 1"}]

if st.button("➕ Adicionar Novo Ambiente"):
    novo_id = max([a["id"] for a in st.session_state["ambientes_lista"]], default=0) + 1
    st.session_state["ambientes_lista"].append({"id": novo_id, "nome": f"Ambiente {novo_id}"})
    st.rerun()

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

        tipo_atividade = st.selectbox("Atividade / Norma", list(TABELA_NORMA.keys()), key=f"ativ_{amb_atual['id']}")

        opcoes_banco_str = [f"{item['Fabricante']} - {item['Modelo']} ({item['Lumens']} lm | {item['Potencia']} W)" for item in banco_luminarias_usuario]
        opcoes_banco_str.append("⚙️ Inserir Manual")
        escolha_banco = st.selectbox("Luminária", opcoes_banco_str, key=f"sel_banco_{amb_atual['id']}")
        
        if escolha_banco != "⚙️ Inserir Manual":
            idx_escolhido = opcoes_banco_str.index(escolha_banco)
            lum_sel = banco_luminarias_usuario[idx_escolhido]
            fluxo_lampada, potencia_lampada = lum_sel["Lumens"], lum_sel["Potencia"]
            modelo_desc_relatorio = f"{lum_sel['Fabricante']} - {lum_sel['Modelo']}"
        else:
            fluxo_lampada = st.number_input("Fluxo (lm)", value=2000.0, key=f"flux_m_{amb_atual['id']}")
            potencia_lampada = st.number_input("Potência (W)", value=20.0, key=f"pot_m_{amb_atual['id']}")
            modelo_desc_relatorio = "Personalizado"

        col_a, col_b = st.columns(2)
        with col_a:
            comprimento = st.number_input("Comprimento C (m)", value=6.0, key=f"comp_{amb_atual['id']}")
            largura = st.number_input("Largura L (m)", value=4.5, key=f"larg_{amb_atual['id']}")
            pe_direito = st.number_input("Pé-Direito H (m)", value=2.9, key=f"ped_{amb_atual['id']}")
            hp = st.number_input("Plano de Trabalho hp (m)", value=0.75, key=f"hp_{amb_atual['id']}")
            hp_desc = st.number_input("Descimento hp' (m)", value=0.0, key=f"hpd_{amb_atual['id']}")
        with col_b:
            iluminancia_req = st.number_input("Meta (lx)", value=TABELA_NORMA[tipo_atividade], key=f"lux_{amb_atual['id']}")
            fator_u = st.selectbox("Fator de Utilização (u)", [0.65, 0.50, 0.35], index=1, key=f"ut_{amb_atual['id']}")
            fator_d = st.selectbox("Fator de Depreciação (d)", [0.80, 0.75, 0.70], index=1, key=f"dep_{amb_atual['id']}")

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

        st.markdown(f"**Resultado:** {qtd_real} luminárias | {lux_real:.2f} lx")

        lista_calculos_ambientes.append({
            "nome": novo_nome, "comp": comprimento, "larg": largura, "pe_direito": pe_direito,
            "hp": hp, "hp_desc": hp_desc, "area": area, "hu": hu, "lux_req": iluminancia_req,
            "fluxo": fluxo_lampada, "potencia": potencia_lampada, "modelo_lum": modelo_desc_relatorio,
            "k_indice": k_indice, "fator_u": fator_u, "desc_utilizacao": "Padrão", "fator_d": fator_d,
            "desc_depreciacao": "Padrão", "fluxo_req": fluxo_req_teorico, "qtd_teorica": qtd_teorica,
            "qtd_real": qtd_real, "fluxo_instalado": fluxo_instalado, "lux_real": lux_real,
            "pot_total": pot_total, "dpi": dpi, "conforme": conforme, "linhas": 1, "colunas": 1,
            "dist_c": 1, "dist_parede_c": 1, "dist_l": 1, "dist_parede_l": 1
        })

st.markdown("---")
st.subheader("📥 Emissão de Relatório Seguro (.docx)")

if st.button("Gerar Relatório Técnico Completo", use_container_width=True):
    dados_cliente = {"nome": cli_nome if cli_nome else "Cliente Geral"}
    dados_prof = {"nome": prof_nome if prof_nome else st.session_state["usuario_nome"], "titulo": titulo_prof, "registro": prof_registro or "CREA 0000"}
    arquivo_docx = gerar_docx_lote(dados_cliente, dados_prof, lista_calculos_ambientes, logo_upload)
    
    st.download_button(
        label="📥 Baixar Laudo Word Seguro",
        data=arquivo_docx,
        file_name="Laudo_Luminotecnico.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
