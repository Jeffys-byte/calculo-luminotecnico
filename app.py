import streamlit as st
import sqlite3
import hashlib
import json
import math
import datetime
import random
import uuid
import io
import os
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
    # FORÇA A RECUPERAÇÃO DO BANCO: Se o arquivo existir, verifica integridade.
    # Se estiver corrompido ou travar, remove e recria para evitar o OperationalError.
    if os.path.exists(ARQUIVO_DB_USUARIOS):
        try:
            # Tenta abrir o banco apenas para leitura para verificar se está acessível
            test_conn = sqlite3.connect(f"file:{ARQUIVO_DB_USUARIOS}?mode=ro", uri=True)
            test_conn.execute("PRAGMA integrity_check;")
            test_conn.close()
        except sqlite3.OperationalError:
            # Banco corrompido ou travado, remove o arquivo
            try:
                os.remove(ARQUIVO_DB_USUARIOS)
            except PermissionError:
                # Se o arquivo estiver em uso e não puder ser removido,
                # tentaremos sobrescrevê-lo na conexão abaixo.
                pass
            except Exception:
                pass

    # Conecta e garante a estrutura correta
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    
    # Cria tabela de usuários se não existir
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
    
    # Cria tabela de luminárias se não existir com as colunas novas
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
    
    # Garante colunas de migração caso o CREATE TABLE IF NOT EXISTS não as tenha pego
    def garantir_coluna(tabela, coluna, definicao):
        try:
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas = [col[1] for col in cursor.fetchall()]
            if coluna not in colunas:
                cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
                conn.commit()
        except Exception:
            pass

    garantir_coluna("usuarios", "sessao_ativa", "TEXT")
    garantir_coluna("luminarias", "global", "INTEGER DEFAULT 0")
    garantir_coluna("luminarias", "email_usuario", "TEXT")
    
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

# Executa a inicialização forçada/segura
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
        cursor.execute("SELECT id, email_usuario, fabricante, modelo, lumens, potencia, global FROM luminarias")
    else:
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

if st.session_state["autenticado"]:
    if not validar_sessao_ativa(st.session_state["usuario_email"], st.session_state["token_sessao"]):
        st.session_state["autenticado"] = False
        st.error("⚠️ Sua conta foi acessada em outro dispositivo. Esta sessão foi encerrada.")
        st.stop()

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
        for c_idx, cell in enumerate(row
