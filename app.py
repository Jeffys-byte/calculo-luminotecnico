import streamlit as st
import pandas as pd
import math
import io
import datetime
import base64
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Luminotécnica Profissional",
    page_icon="💡",
    layout="wide"
)

# --- CONFIGURAÇÃO DO BANCO DE DADOS SQLITE ---
def init_db():
    conn = sqlite3.connect('luminotecnica.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            senha TEXT NOT NULL,
            criacao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            assinante INTEGER DEFAULT 0,
            token_recuperacao TEXT,
            token_expira TEXT
        )
    ''')
    
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas = [col[1] for col in cursor.fetchall()]
    if "token_recuperacao" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN token_recuperacao TEXT")
    if "token_expira" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN token_expira TEXT")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_usuario TEXT,
            nome TEXT,
            email_cli TEXT,
            telefone TEXT,
            cidade TEXT,
            FOREIGN KEY (email_usuario) REFERENCES usuarios(email)
        )
    ''')
    conn.commit()
    
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", ("jefkar27@gmail.com",))
    if not cursor.fetchone():
        data_criacao = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO usuarios (email, senha, criacao, tipo, assinante) VALUES (?, ?, ?, ?, ?)",
                       ("jefkar27@gmail.com", "123", data_criacao, "admin", 1))
        cursor.execute("INSERT INTO clientes (email_usuario, nome, email_cli, telefone, cidade) VALUES (?, ?, ?, ?, ?)",
                       ("jefkar27@gmail.com", "Cliente Geral", "contato@clientegeral.com", "(21) 99999-9999", "Rio de Janeiro - RJ"))
        conn.commit()
    conn.close()

init_db()

# --- FUNÇÃO DE ENVIO DE E-MAIL REAL ---
def enviar_email_token(destinatario, token):
    # INSIRA ABAIXO O SEU E-MAIL REAL E A SENHA DE APLICATIVO DO GMAIL
    remetente = "jeffys.job@gmail.com"  # Coloque seu e-mail aqui
    senha_app = "SUA_SENHA_DE_APLICATIVO_AQUI"  # Coloque a senha de 16 dígitos gerada no Google aqui
    
    # Se configurado via secrets do Streamlit, ele tem prioridade:
    if "EMAIL_USER" in st.secrets and "EMAIL_PASS" in st.secrets:
        remetente = st.secrets["EMAIL_USER"]
        senha_app = st.secrets["EMAIL_PASS"]

    assunto = "Código de Segurança - Recuperação de Senha"
    corpo = f"""
    Olá,
    
    Você solicitou a recuperação de senha para o sistema Luminotécnica Profissional.
    O seu Código de Segurança (Token) é: {token}
    
    Insira este código na tela de recuperação do sistema.
    """

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remetente, senha_app)
        servidor.sendmail(remetente, destinatario, msg.as_string())
        servidor.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

def carregar_usuario_db(email):
    conn = sqlite3.connect('luminotecnica.db')
    cursor = conn.cursor()
    cursor.execute("SELECT senha, criacao, tipo, assinante, token_recuperacao FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    senha, criacao_str, tipo, assinante, token_rec = row
    try:
        criacao = datetime.datetime.strptime(criacao_str, "%Y-%m-%d %H:%M:%S")
    except:
        criacao = datetime.datetime.now()
        
    cursor.execute("SELECT nome, email_cli, telefone, cidade FROM clientes WHERE email_usuario = ?", (email,))
    clientes_rows = cursor.fetchall()
    banco_clientes = [{"Nome": r[0], "Email": r[1], "Telefone": r[2], "Cidade": r[3]} for r in clientes_rows]
    if not banco_clientes:
        banco_clientes = [{"Nome": "Cliente Geral", "Email": "contato@clientegeral.com", "Telefone": "(21) 99999-9999", "Cidade": "Rio de Janeiro - RJ"}]

    conn.close()
    return {
        "senha": senha,
        "criacao": criacao,
        "tipo": tipo,
        "assinante": bool(assinante),
        "token_recuperacao": token_rec,
        "banco_clientes": banco_clientes
    }

def salvar_usuario_db(email, senha, tipo="cliente", assinante=0):
    conn = sqlite3.connect('luminotecnica.db')
    cursor = conn.cursor()
    data_criacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO usuarios (email, senha, criacao, tipo, assinante) VALUES (?, ?, ?, ?, ?)",
                   (email, senha, data_criacao, tipo, assinante))
    cursor.execute("INSERT INTO clientes (email_usuario, nome, email_cli, telefone, cidade) VALUES (?, ?, ?, ?, ?)",
                   (email, "Cliente Exemplo", "exemplo@email.com", "(21) 98888-8888", "Rio de Janeiro - RJ"))
    conn.commit()
    conn.close()

def atualizar_senha_db(email, nova_senha):
    conn = sqlite3.connect('luminotecnica.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET senha = ?, token_recuperacao = NULL WHERE email = ?", (nova_senha, email))
    conn.commit()
    conn.close()

def gerar_token_recuperacao(email):
    token = str(random.randint(100000, 999999))
    conn = sqlite3.connect('luminotecnica.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET token_recuperacao = ? WHERE email = ?", (token, email))
    conn.commit()
    conn.close()
    return token

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

def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario_email" not in st.session_state:
        st.session_state.usuario_email = None

    if not st.session_state.autenticado:
        definir_fundo_personalizado_base64(url_imagem="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1920&auto=format&fit=crop")
        
        st.markdown("<h2 style='text-align: center; color: #ffffff;'>🔐 Área Restrita - Luminotécnica Profissional</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #cbd5e0;'>Crie sua conta e ganhe <b>24 horas de teste gratuito</b>, ou faça login se já tiver cadastro.</p>", unsafe_allow_html=True)
        
        tab_login, tab_cadastro, tab_planos = st.tabs(["🔑 Fazer Login", "📝 Criar Conta Grátis (Teste 24h)", "💳 Assinar (R$ 19,90/mês)"])
        
        with tab_login:
            with st.form("form_login"):
                email_input = st.text_input("E-mail cadastrado", value="").strip().lower()
                senha_input = st.text_input("Senha", type="password", value="").strip()
                btn_entrar = st.form_submit_button("Entrar no Sistema")
                
                if btn_entrar:
                    user_data = carregar_usuario_db(email_input)
                    if user_data and user_data["senha"] == senha_input:
                        agora = datetime.datetime.now()
                        tempo_criacao = user_data["criacao"]
                        horas_decorridas = (agora - tempo_criacao).total_seconds() / 3600
                        
                        if user_data["tipo"] == "admin" or horas_decorridas <= 24 or user_data.get("assinante", False):
                            st.session_state.autenticado = True
                            st.session_state.usuario_email = email_input
                            st.success("Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("⏰ Seu período de teste de 24 horas expirou. Vá na aba 'Assinar' para continuar usando por apenas R$ 19,90/mês.")
                    else:
                        st.error("E-mail ou senha incorretos, ou usuário não encontrado.")

            with st.expander("🔑 Esqueci / Redefinir minha senha com Token"):
                st.markdown("Insira seu e-mail para receber um **Código de Segurança (Token)** real em sua caixa de entrada.")
                with st.form("form_pedir_token"):
                    email_rec = st.text_input("E-mail cadastrado para recuperação").strip().lower()
                    btn_gerar_token = st.form_submit_button("Enviar Código por E-mail")
                    
                    if btn_gerar_token:
                        if email_rec:
                            if carregar_usuario_db(email_rec):
                                token_criado = gerar_token_recuperacao(email_rec)
                                sucesso_envio = enviar_email_token(email_rec, token_criado)
                                if sucesso_envio:
                                    st.success(f"Código de segurança enviado com sucesso para **{email_rec}**! Verifique sua caixa de entrada ou spam.")
                                else:
                                    st.error("Erro ao disparar o e-mail. Verifique se o e-mail e a senha de aplicativo estão corretos.")
                            else:
                                st.error("Este e-mail não está cadastrado.")
                        else:
                            st.error("Informe o e-mail.")

                st.markdown("---")
                st.markdown("Já recebeu o código no e-mail? Digite-o abaixo junto com a nova senha:")
                with st.form("form_confirmar_token"):
                    email_conf = st.text_input("Confirme seu e-mail").strip().lower()
                    token_dig = st.text_input("Código de Segurança (Token de 6 dígitos)").strip()
                    nova_senha_rec = st.text_input("Digite a nova senha", type="password").strip()
                    btn_redefinir = st.form_submit_button("Validar e Atualizar Senha")
                    
                    if btn_redefinir:
                        if email_conf and token_dig and nova_senha_rec:
                            usr_check = carregar_usuario_db(email_conf)
                            if usr_check:
                                if usr_check["token_recuperacao"] == token_dig:
                                    atualizar_senha_db(email_conf, nova_senha_rec)
                                    st.success("Senha redefinida com segurança! Faça login na aba ao lado com a nova senha.")
                                else:
                                    st.error("Código de segurança (Token) inválido ou incorreto.")
                            else:
                                st.error("E-mail não encontrado.")
                        else:
                            st.error("Preencha todos os campos.")

        with tab_cadastro:
            st.markdown("### ⚡ Comece a usar agora mesmo")
            with st.form("form_cadastro"):
                novo_email = st.text_input("Seu E-mail principal", value="").strip().lower()
                nova_senha = st.text_input("Crie uma Senha", type="password", value="").strip()
                btn_cadastrar = st.form_submit_button("Criar Conta e Iniciar Teste Grátis")
                
                if btn_cadastrar:
                    if novo_email and nova_senha:
                        if carregar_usuario_db(novo_email):
                            st.warning("Este e-mail já está cadastrado. Faça login na primeira aba.")
                        else:
                            salvar_usuario_db(novo_email, nova_senha, tipo="cliente", assinante=0)
                            st.session_state.autenticado = True
                            st.session_state.usuario_email = novo_email
                            st.success("Conta criada com sucesso! Seu teste de 24 horas começou.")
                            st.rerun()
                    else:
                        st.error("Preencha todos os campos para criar a conta.")

        with tab_planos:
            st.markdown("### 🚀 Assinatura Profissional")
            st.markdown("Tenha acesso ilimitado a todos os cálculos normativos (NBR ISO/CIE 8995-1).")
            
            st.markdown("""
                <div style="background-color: #1a202c; border: 2px solid #ffc107; padding: 25px; border-radius: 8px; text-align: center; color: white; margin-top: 15px; margin-bottom: 15px;">
                    <h3 style="margin-top: 0; color: #ffc107;">Desbloqueie o Acesso Completo</h3>
                    <p style="font-size: 16px; color: #cbd5e0; margin-bottom: 5px;">Tenha relatórios ilimitados e sem restrições por apenas:</p>
                    <div style="font-size: 34px; font-weight: bold; color: #28a745; margin: 15px 0;">R$ 19,90 / mês</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.link_button("💳 Pagar com Mercado Pago (R$ 19,90)", "https://mpago.la/2sbQvQ9", use_container_width=True)
                    
        return False

    return True

if not verificar_autenticacao():
    st.stop()
