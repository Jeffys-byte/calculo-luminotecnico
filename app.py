import streamlit as st
import pandas as pd
import io
import math
import json
import os
import sqlite3
import hashlib
from datetime import datetime
import mercadopago

# --- CONFIGURAÇÕES DO MERCADO PAGO ---
# Dica: Para testes, use seu Access Token de Teste (Sandbox/Test) do Mercado Pago
ACCESS_TOKEN_MP = "TEST-seu-access-token-aqui" 

# --- BANCO DE DADOS DE USUÁRIOS E LICENÇAS (SQLITE) ---
ARQUIVO_DB_USUARIOS = "usuarios_sistema.db"

def inicializar_db_usuarios():
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            senha_hash TEXT NOT NULL,
            nome TEXT,
            is_pro INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

inicializar_db_usuarios()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def cadastrar_usuario(email, senha, nome):
    try:
        conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (email, senha_hash, nome, is_pro) VALUES (?, ?, ?, ?)",
                       (email, hash_senha(senha), nome, 0))
        conn.commit()
        conn.close()
        return True, "Cadastro realizado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Este e-mail já está cadastrado."

def verificar_login(email, senha):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("SELECT senha_hash, nome, is_pro FROM usuarios WHERE email = ?", (email,))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado and resultado[0] == hash_senha(senha):
        return True, resultado[1], bool(resultado[2])
    return False, "", False

def atualizar_status_pro(email, status_pro):
    conn = sqlite3.connect(ARQUIVO_DB_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET is_pro = ? WHERE email = ?", (1 if status_pro else 0, email))
    conn.commit()
    conn.close()

# --- FUNÇÃO PARA GERAR PREFERÊNCIA DE PAGAMENTO NO MERCADO PAGO ---
def criar_link_pagamento_mp(email_usuario):
    try:
        sdk = mercadopago.SDK(ACCESS_TOKEN_MP)
        
        # URL base do seu app (substitua pelo seu link oficial do Streamlit Cloud quando publicar)
        url_retorno = "https://seu-app.streamlit.app" 
        
        preference_data = {
            "items": [
                {
                    "title": "Licença PRO - Sistema Luminotécnico",
                    "quantity": 1,
                    "unit_price": 49.90,
                    "currency_id": "BRL"
                }
            ],
            "payer": {
                "email": email_usuario
            },
            "back_urls": {
                "success": f"{url_retorno}/?pagamento=sucesso",
                "failure": f"{url_retorno}/?pagamento=falha",
                "pending": f"{url_retornos}/?pagamento=pendente"
            },
            "auto_return": "approved",
        }
        
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        # Retorna o init_point (ou sandbox_init_point se estiver usando token de teste)
        return preference.get("init_point")
    except Exception as e:
        return None

# --- BANCO DE DADOS DE LUMINÁRIAS (JSON LOCAL) ---
ARQUIVO_BANCO_LUM = "banco_luminarias.json"

def carregar_banco_luminarias():
    if os.path.exists(ARQUIVO_BANCO_LUM):
        try:
            with open(ARQUIVO_BANCO_LUM, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return [
        {"Fabricante": "Genérica", "Modelo": "Painel LED Embutir 18W", "Lumens": 1440, "Potencia": 18.0},
        {"Fabricante": "Philips", "Modelo": "Ledinaire Downlight 20W", "Lumens": 1800, "Potencia": 20.0},
        {"Fabricante": "Ledvance", "Modelo": "Painel Superior 30W", "Lumens": 2700, "Potencia": 30.0}
    ]

def salvar_banco_luminarias(lista):
    with open(ARQUIVO_BANCO_LUM, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)

if "banco_luminarias" not in st.session_state:
    st.session_state["banco_luminarias"] = carregar_banco_luminarias()

# Gerenciamento de Sessão de Login
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_email" not in st.session_state:
    st.session_state["usuario_email"] = ""
if "usuario_nome" not in st.session_state:
    st.session_state["usuario_nome"] = ""
if "is_pro" not in st.session_state:
    st.session_state["is_pro"] = False

# --- CAPTURA DE RETORNO DO PAGAMENTO (QUERY PARAMS) ---
query_params = st.query_params
if "pagamento" in query_params and query_params["pagamento"] == "sucesso":
    if st.session_state["autenticado"] and not st.session_state["is_pro"]:
        atualizar_status_pro(st.session_state["usuario_email"], True)
        st.session_state["is_pro"] = True
        st.success("🎉 Pagamento aprovado com sucesso! Sua conta agora é PRO.")

# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Sistema Luminotécnico SaaS", layout="wide")

# --- BARRA LATERAL: AUTENTICAÇÃO E PLANOS ---
st.sidebar.header("🔐 Portal do Cliente")

if not st.session_state["autenticado"]:
    aba_login, aba_cadastro = st.sidebar.tabs(["Entrar", "Criar Conta"])
    
    with aba_login:
        st.subheader("Acessar Sistema")
        email_login = st.text_input("E-mail", key="email_l")
        senha_login = st.text_input("Senha", type="password", key="senha_l")
        if st.button("Entrar", use_container_width=True):
            sucesso, nome_cad, status_pro_db = verificar_login(email_login, senha_login)
            if sucesso:
                st.session_state["autenticado"] = True
                st.session_state["usuario_email"] = email_login
                st.session_state["usuario_nome"] = nome_cad
                st.session_state["is_pro"] = status_pro_db
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
                
    st.stop()

# Se já estiver logado:
st.sidebar.success(f"Olá, **{st.session_state['usuario_nome']}**!")
plano_atual_str = "🚀 PRO (Completo)" if st.session_state["is_pro"] else "📌 Básico (Padrão)"
st.sidebar.info(f"Plano Ativo: **{plano_atual_str}**")

# Botão de Pagamento Real via Mercado Pago
if not st.session_state["is_pro"]:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💎 Desbloquear Plano PRO")
    st.sidebar.write("Acesse Fitas LED, Spots e recursos avançados.")
    
    if st.sidebar.button("Pagar R$ 49,90 via Mercado Pago", use_container_width=True):
        link_mp = criar_link_pagamento_mp(st.session_state["usuario_email"])
        if link_mp:
            st.sidebar.markdown(f"🔗 [Clique aqui para abrir o Checkout do Mercado Pago]({link_mp})", unsafe_allow_html=True)
        else:
            st.sidebar.error("Erro ao gerar link de pagamento. Verifique as credenciais.")
else:
    if st.sidebar.button("🔄 Voltar para Plano Básico (Teste)", use_container_width=True):
        atualizar_status_pro(st.session_state["usuario_email"], False)
        st.session_state["is_pro"] = False
        st.rerun()

if st.sidebar.button("🚪 Sair da Conta", use_container_width=True):
    st.session_state["autenticado"] = False
    st.session_state["usuario_email"] = ""
    st.session_state["usuario_nome"] = ""
    st.session_state["is_pro"] = False
    st.rerun()

# [O restante do código de cálculo luminotécnico e geração de relatório continua exatamente igual...]
