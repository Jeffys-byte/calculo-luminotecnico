import streamlit as st
import sqlite3
import hashlib
import json
import math
import datetime
import random
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
            token_recuperacao TEXT
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

# --- FUNÇÃO PARA GERAR PREFERÊNCIA DE PAGAMENTO NO MERCADO PAGO ---
def criar_link_pagamento_mp(email_usuario):
    try:
        url_retorno = "https://calculo-luminotecnico.streamlit.app"
        
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
                "pending": f"{url_retorno}/?pagamento=pendente"
            },
            "auto_return": "approved",
        }
        
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
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

# --- INTERFACE WEB STREAMLIT ---
st.set_page_config(page_title="Sistema Luminotécnico SaaS", layout="wide")

import os
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

    adicionar_secao_tabela(
        "2. Parâmetros Luminotécnicos Adotados",
        ["Parâmetro Técnico", "Símbolo", "Valor Adotado", "Observações / Norma"],
        [Inches(2.5), Inches(0.8), Inches(1.2), Inches(2.0)],
        [
            ["Iluminância Requerida (Meta)", "Ereq", f"{d['lux_req']:.0f} lx", "NBR ISO/CIE 8995-1"],
            ["Fluxo Luminoso da Luminária", "Φlâmpada", f"{fluxo_fmt} lm", d.get('modelo_lum', 'Manual')],
            ["Potência Unitária da Luminária", "Punit", f"{d['potencia']:.1f} W", "Consumo (W)"],
            ["Índice do Recinto", "K", f"{d['k_indice']:.2f}", "Geometria (C × L) / [hu × (C + L)]"],
            ["Fator de Utilização", "u", f"{d['fator_u']:.2f} ({int(d['fator_u']*100)}%)", f"Refletância: {d['desc_utilizacao']}"],
            ["Fator de Depreciação / Perdas", "d", f"{d['fator_d']:.2f} ({int(d['fator_d']*100)}%)", f"Manutenção: {d['desc_depreciacao']}"]
        ]
    )

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

    if d.get("usar_pro", False):
        adicionar_secao_tabela(
            "4. Módulo PRO: Detalhamento de Fitas LED e Spots",
            ["Parâmetro Especializado", "Especificação Técnica", "Resultado do Dimensionamento", "Validação NBR 5410"],
            [Inches(2.5), Inches(1.8), Inches(1.5), Inches(1.2)],
            [
                ["Fita LED (Perímetro / Sanca)", f"{d['fita_comprimento']:.2f} m linear | {d['fita_pot_metro']} W/m", f"Potência Total: {d['fita_pot_total']:.1f} W", f"Fonte Recomendada: {d['fita_fonte_rec']:.1f} W ({d['fita_tensao']})"],
                ["Queda de Tensão Fita LED", f"Trecho contínuo: {d['fita_comprimento']:.2f} m", f"Limite crítico: 5.0 m", f"{'OK' if d['fita_comprimento'] <= 5 else 'ALERTA: Inserir nova injeção'}"],
                ["Spot de Destaque (Facho)", f"Abertura de feixe: {d['spot_angulo']}°", f"Diâmetro da mancha no piso: {d['spot_diametro']:.2f} m", f"Altura útil ref: {d['hu']:.2f} m"]
            ]
        )

    adicionar_secao_tabela(
        "5. Disposição Espacial e Layout de Instalação",
        ["Eixo de Instalação", "Arranjo (Linhas × Colunas)", "Distância entre Luminárias", "Distância das Paredes"],
        [Inches(2.2), Inches(1.8), Inches(1.3), Inches(1.2)],
        [
            ["Eixo Longitudinal (Comprimento)", f"{d['linhas']} Linhas", f"{d['dist_c']:.2f} m", f"{d['dist_parede_c']:.2f} m"],
            ["Eixo Transversal (Largura)", f"{d['colunas']} Colunas", f"{d['dist_l']:.2f} m", f"{d['dist_parede_l']:.2f} m"]
        ]
    )

    doc.add_heading("6. Parecer Técnico e Conclusão Normativa", level=2)
    p1 = doc.add_paragraph()
    p1.add_run("• Nível de Iluminância: ").bold = True
    p1.add_run(f"O valor projetado atinge {d['lux_real']:.2f} lx, ")
    if d['conforme']:
        p1.add_run(f"atendendo satisfatoriamente à meta de {d['lux_req']:.0f} lx da norma NBR ISO/CIE 8995-1.")
    else:
        p1.add_run(f"abaixo da meta de {d['lux_req']:.0f} lx da norma NBR ISO/CIE 8995-1.")

    p2 = doc.add_paragraph()
    p2.add_run("• Eficiência Energética: ").bold = True
    p2.add_run(f"A densidade de potência instalada é de {d['dpi']:.2f} W/m².")

    p3 = doc.add_paragraph()
    p3.add_run("• Status Final: ").bold = True
    run_status = p3.add_run("CONFORME (Aprovado)." if d['conforme'] else "NÃO CONFORME (Requer ajustes).")
    run_status.bold = True
    run_status.font.color.rgb = RGBColor(38, 128, 0) if d['conforme'] else RGBColor(200, 0, 0)

def gerar_docx_lote(dados_cliente, dados_prof, lista_dados_ambientes, logo_file=None):
    doc = docx.Document()
    for section in doc.sections:
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

# --- APLICAÇÃO DE IMAGEM DE FUNDO NA TELA DE LOGIN (ÁREA PRINCIPAL) ---
if not st.session_state["autenticado"]:
    # Cole aqui o link direto da imagem (ex: URL pública ou hospedada) ou substitua pelo link da sua foto da sala
    url_imagem_fundo = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1600&auto=format&fit=crop"
    
    css_fundo = f"""
    <style>
    /* Aplica a imagem de fundo com efeito escurecido/elegante na área principal (lado direito) */
    .stMain {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{url_imagem_fundo}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(css_fundo, unsafe_allow_html=True)

# --- BARRA LATERAL: AUTENTICAÇÃO E LOGO ---
st.sidebar.header("🔐 Portal do Cliente")

if not st.session_state["autenticado"]:
    logo_svg_html = """
    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 220" width="100%" height="110">
        <defs>
          <style>
            .bulb-stroke { fill: none; stroke: #FFFFFF; stroke-width: 8; stroke-linecap: round; stroke-linejoin: round; }
            .spark-stroke { fill: none; stroke: #FFD166; stroke-width: 8; stroke-linecap: round; stroke-linejoin: round; }
          </style>
        </defs>
        <g transform="translate(190, 5)">
          <path class="spark-stroke" d="M 60 20 L 60 5" />
          <path class="spark-stroke" d="M 90 30 L 100 20" />
          <path class="spark-stroke" d="M 30 30 L 20 20" />
          <path class="bulb-stroke" d="M 30 100 C 15 85 10 65 10 50 C 10 25 30 10 60 10 C 90 10 110 25 110 50 C 110 65 105 85 90 100 Z" />
          <path class="bulb-stroke" d="M 45 100 L 75 100" />
          <path class="bulb-stroke" d="M 50 112 L 70 112" />
          <path class="bulb-stroke" d="M 54 124 L 66 124" />
        </g>
      </svg>
    </div>
    """
    st.sidebar.markdown(logo_svg_html, unsafe_allow_html=True)

    aba_login, aba_cadastro, aba_recuperar = st.sidebar.tabs(["Entrar", "Criar Conta", "Recuperar"])
    
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

    with aba_recuperar:
        st.subheader("Recuperar Senha")
        email_rec = st.text_input("Digite seu e-mail cadastrado", key="email_rec")
        
        if "token_gerado_temp" not in st.session_state:
            st.session_state["token_gerado_temp"] = ""
            
        if st.button("Gerar Código de Recuperação", use_container_width=True, key="btn_gerar_token"):
            if email_rec:
                tk, msg_tk = gerar_token_recuperacao(email_rec)
                if tk:
                    st.session_state["token_gerado_temp"] = tk
                    st.session_state["email_alvo_rec"] = email_rec
                    st.success(f"Código gerado! Anote seu código: **{tk}**")
                else:
                    st.error(msg_tk)
            else:
                st.warning("Informe o e-mail.")
                
        if st.session_state["token_gerado_temp"]:
            st.markdown("---")
            token_digitado = st.text_input("Digite o Código de 6 Dígitos", key="tk_digitado")
            nova_senha_rec = st.text_input("Nova Senha", type="password", key="nova_s_rec")
            if st.button("Redefinir Senha", use_container_width=True, key="btn_confirmar_nova_senha"):
                if token_digitado and nova_senha_rec:
                    ok_red, msg_red = redefinir_senha_com_token(st.session_state["email_alvo_rec"], token_digitado, nova_senha_rec)
                    if ok_red:
                        st.success(msg_red + " Faça login na aba 'Entrar'.")
                        st.session_state["token_gerado_temp"] = ""
                    else:
                        st.error(msg_red)
                else:
                    st.warning("Preencha todos os campos para redefinir.")
                
    # Mensagem de Boas-vindas opcional no espaço direito antes de logar
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; text-align: center; color: white; padding: 20px;">
        <h1 style="font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">⚡ Sistema Luminotécnico Profissional</h1>
        <p style="font-size: 1.2rem; text-shadow: 1px 1px 3px rgba(0,0,0,0.8); max-width: 600px;">Faça login na barra lateral esquerda para acessar o painel completo de cálculo de lumens, fitas LED, spots e geração de laudos técnicos em Word.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    if st.sidebar.button("Pagar R$ 49,90 via Mercado Pago", use_container_width=True, key="btn_pagar_mercado_pago"):
        link_mp = criar_link_pagamento_mp(st.session_state["usuario_email"])
        if link_mp:
            st.sidebar.markdown(f"🔗 [Clique aqui para abrir o Checkout]({link_mp})", unsafe_allow_html=True)
        else:
            st.sidebar.error("Erro ao gerar link de pagamento. Verifique as credenciais.")
else:
    if st.sidebar.button("🔄 Voltar para Plano Básico (Teste)", use_container_width=True, key="btn_voltar_basico"):
        atualizar_status_pro(st.session_state["usuario_email"], False)
        st.session_state["is_pro"] = False
        st.rerun()

if st.sidebar.button("🚪 Sair da Conta", use_container_width=True, key="btn_sair_conta"):
    st.session_state["autenticado"] = False
    st.session_state["usuario_email"] = ""
    st.session_state["usuario_nome"] = ""
    st.session_state["is_pro"] = False
    st.rerun()

# TÍTULO DINÂMICO
if st.session_state["is_pro"]:
    st.title("⚡ Luminotécnica PRO")
else:
    st.title("⚡ Sistema Luminotécnico - Versão Básica")

st.write("Dimensionamento Luminotécnico Automatizado e Validação Normativa.")

st.sidebar.markdown("---")
st.sidebar.header("🎨 Personalização da Marca")
logo_upload = st.sidebar.file_uploader("Envie sua Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

st.sidebar.markdown("---")
st.sidebar.header("👨‍💻 Dados do Responsável Técnico")

lista_cat_prof = [
    "Engenheiro(a) Eletricista", 
    "Engenheiro(a) Civil", 
    "Arquiteto(a) e Urbanista", 
    "Técnico(a) em Eletrotecnica", 
    "Designer de Interiores",
    "Personalizado (Digitar Outro)"
]
escolha_cat_prof = st.sidebar.selectbox("Categoria Profissional", lista_cat_prof)

if escolha_cat_prof == "Personalizado (Digitar Outro)":
    titulo_prof = st.sidebar.text_input("Digite o Título Profissional", "", placeholder="Ex: Projetista Luminotécnico")
else:
    titulo_prof = escolha_cat_prof

prof_nome = st.sidebar.text_input("Nome do Profissional", "", placeholder="Seu Nome")
prof_registro = st.sidebar.text_input("Registro (CREA / CAU / CFT)", "", placeholder="Ex: CREA/RJ 000.000")
prof_contato = st.sidebar.text_input("E-mail / Contato", "", placeholder="contato@email.com")

TABELA_NORMA = {
    "Dormitórios / Suítes (Residencial)": 200,
    "Salas de Estar / Jantar": 150,
    "Cozinhas / Banheiros": 300,
    "Escritórios - Trabalho Geral": 500,
    "Corredores e Circulação": 100,
}

# --- SEÇÃO: BANCO DE DADOS DE LUMINÁRIAS ---
with st.expander("📚 Banco de Dados de Fabricantes e Luminárias (Cadastrar / Consultar)", expanded=False):
    st.write("Cadastre suas luminárias e marcas favoritas para selecioná-las rapidamente nos cálculos.")
    
    col_cad1, col_cad2 = st.columns(2)
    with col_cad1:
        novo_fab = st.text_input("Fabricante / Marca", placeholder="Ex: Philips, Ledvance, OSDA")
        novo_mod = st.text_input("Modelo da Luminária", placeholder="Ex: Painel LED 18W Embutir")
    with col_cad2:
        novo_lum = st.number_input("Fluxo Luminoso (Lúmens - lm)", value=1500.0, step=100.0)
        novo_pot = st.number_input("Potência (Watts - W)", value=18.0, step=1.0)
    
    if st.button("💾 Salvar Nova Luminária no Banco", key="btn_salvar_luminaria"):
        if novo_fab and novo_mod:
            st.session_state["banco_luminarias"].append({
                "Fabricante": novo_fab,
                "Modelo": novo_mod,
                "Lumens": novo_lum,
                "Potencia": novo_pot
            })
            salvar_banco_luminarias(st.session_state["banco_luminarias"])
            st.success(f"Luminária '{novo_mod}' cadastrada com sucesso!")
            st.rerun()
        else:
            st.warning("Preencha ao menos o Fabricante e o Modelo.")
            
    st.markdown("##### Luminárias Cadastradas Atualmente:")
    df_lum_cad = pd.DataFrame(st.session_state["banco_luminarias"])
    st.dataframe(df_lum_cad, use_container_width=True)

st.markdown("---")
st.subheader("1. Identificação Geral do Projeto")
cli_nome = st.text_input("Cliente / Empreendimento", "", placeholder="Nome do Cliente ou Obra")

st.markdown("---")
st.subheader("2. Gerenciamento de Ambientes do Projeto")

if "ambientes_lista" not in st.session_state:
    st.session_state["ambientes_lista"] = [{"id": 1, "nome": "Ambiente Principal"}]

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("➕ Adicionar Novo Ambiente", use_container_width=True, key="btn_adicionar_ambiente"):
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

        tipo_atividade = st.selectbox("Atividade / Norma (NBR ISO/CIE 8995-1)", list(TABELA_NORMA.keys()), key=f"ativ_{amb_atual['id']}")

        st.markdown("#### Geometria e Seleção de Luminária")
        
        opcoes_banco_str = [f"{item['Fabricante']} - {item['Modelo']} ({item['Lumens']} lm | {item['Potencia']} W)" for item in st.session_state["banco_luminarias"]]
        opcoes_banco_str.append("⚙️ Inserir Dados Manuais (Personalizado)")
        
        escolha_banco = st.selectbox("Selecionar Luminária do Banco de Dados", opcoes_banco_str, key=f"sel_banco_{amb_atual['id']}")
        
        if escolha_banco != "⚙️ Inserir Dados Manuais (Personalizado)":
            idx_escolhido = opcoes_banco_str.index(escolha_banco)
            lum_selecionada = st.session_state["banco_luminarias"][idx_escolhido]
            fluxo_lampada = lum_selecionada["Lumens"]
            potencia_lampada = lum_selecionada["Potencia"]
            modelo_desc_relatorio = f"{lum_selecionada['Fabricante']} - {lum_selecionada['Modelo']}"
            
            st.info(f"💡 **Luminária Selecionada:** {lum_selecionada['Fabricante']} {lum_selecionada['Modelo']} — **{fluxo_lampada} lm** | **{potencia_lampada} W**")
        else:
            fluxo_lampada = st.number_input("Fluxo Luminoso da Luminária (lm)", value=2000.0, step=100.0, key=f"flux_m_{amb_atual['id']}")
            potencia_lampada = st.number_input("Potência Unitária (W)", value=20.0, step=1.0, key=f"pot_m_{amb_atual['id']}")
            modelo_desc_relatorio = "Luminária Personalizada (Manual)"

        col_a, col_b = st.columns(2)
        with col_a:
            comprimento = st.number_input("Comprimento C (m)", value=6.00, step=0.1, key=f"comp_{amb_atual['id']}")
            largura = st.number_input("Largura L (m)", value=4.50, step=0.1, key=f"larg_{amb_atual['id']}")
            pe_direito = st.number_input("Pé-Direito Total H (m)", value=2.90, step=0.1, key=f"ped_{amb_atual['id']}")
            hp = st.number_input("Altura do Plano de Trabalho hp (m)", value=0.75, step=0.05, key=f"hp_{amb_atual['id']}")
            hp_desc = st.number_input("Pé-direito / Descimento hp' (m)", value=0.00, step=0.05, key=f"hpd_{amb_atual['id']}")

        with col_b:
            lux_padrao = TABELA_NORMA[tipo_atividade]
            iluminancia_req = st.number_input("Iluminância Meta Requerida (lx)", value=lux_padrao, step=50, key=f"lux_{amb_atual['id']}")
            
            opcoes_utilizacao = {
                "Ambiente Claro / Refletivo (u = 0.65)": 0.65,
                "Ambiente Médio / Comercial Padrão (u = 0.50)": 0.50,
                "Ambiente Escuro / Industrial (u = 0.35)": 0.35,
                "Valor Personalizado (Manual)": -1.0
            }
            escolha_ut_sel = st.selectbox("Fator de Utilização (u)", list(opcoes_utilizacao.keys()), key=f"ut_sel_{amb_atual['id']}")
            
            if opcoes_utilizacao[escolha_ut_sel] != -1.0:
                fator_u = opcoes_utilizacao[escolha_ut_sel]
                desc_utilizacao = escolha_ut_sel
            else:
                fator_u = st.number_input("Digite o Fator de Utilização (u)", min_value=0.05, max_value=1.0, value=0.50, step=0.01, key=f"ut_man_{amb_atual['id']}")
                desc_utilizacao = "Personalizado (Manual)"

            opcoes_depreciacao = {
                "Ambiente Limpo / Residencial (0.80)": 0.80,
                "Ambiente Comercial / Escritório (0.75)": 0.75,
                "Ambiente com Poeira / Cozinha (0.70)": 0.70,
                "Ambiente Industrial Severo (0.60)": 0.60
            }
            escolha_dep = st.selectbox("Fator de Depreciação / Manutenção (d)", list(opcoes_depreciacao.keys()), key=f"dep_sel_{amb_atual['id']}")
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

        if st.session_state["is_pro"]:
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
        else:
            st.info("💡 **Módulo PRO (Fitas LED & Spots):** Disponível apenas para assinantes do Plano PRO.")

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
            "modelo_lum": modelo_desc_relatorio,
            "k_indice": k_indice, "fator_u": fator_u, "desc_utilizacao": desc_utilizacao, 
            "fator_d": fator_d, "desc_depreciacao": desc_depreciacao,
            "fluxo_req": fluxo_req_teorico, "qtd_teorica": qtd_teorica,
            "qtd_real": qtd_real, "fluxo_instalado": fluxo_instalado,
            "lux_real": lux_real, "pot_total": pot_total, "dpi": dpi,
            "conforme": conforme, "linhas": linhas, "colunas": colunas,
            "dist_c": dist_c, "dist_parede_c": dist_parede_c,
            "dist_l": dist_l, "dist_parede_l": dist_parede_l,
            "modo_afastamento": modo_afastamento, "afastamento_fixo": afastamento_fixo_val,
            "razao_max": razao_max_input, "razao_atual": razao_atual, "espacamento_ok": espacamento_ok,
            "usar_pro": st.session_state["is_pro"], "fita_comprimento": fita_comprimento, "fita_pot_metro": fita_pot_metro,
            "fita_tensao": fita_tensao, "fita_pot_total": fita_pot_total, "fita_fonte_rec": fita_fonte_rec,
            "spot_angulo": spot_angulo, "spot_diametro": spot_diametro
        })

st.markdown("---")
st.subheader("📥 Emissão do Relatório Técnico Consolidado")

if st.button("Gerar e Baixar Relatório Completo (.docx)", use_container_width=True, key="btn_gerar_relatorio_geral"):
    dados_cliente = {"nome": cli_nome if cli_nome else "Cliente Geral"}
    dados_prof = {
        "nome": prof_nome if prof_nome else "Profissional Responsável",
        "titulo": titulo_prof,
        "registro": prof_registro if prof_registro else "CREA/CAU 00000"
    }
    
    arquivo_docx = gerar_docx_lote(dados_cliente, dados_prof, lista_calculos_ambientes, logo_upload)
    st.download_button(
        label="📥 Clique para Baixar o Relatório Word (.docx)",
        data=arquivo_docx,
        file_name="Relatorio_Luminotecnico.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        key="btn_download_docx_final"
    )
    
