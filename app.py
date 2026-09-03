import streamlit as st
import pandas as pd
import math
import io
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Luminotécnica Profissional",
    page_icon="💡",
    layout="wide"
)

# --- BANCO DE DADOS LOCAL DE USUÁRIOS (MEMÓRIA DO APP) ---
if "usuarios_cadastrados" not in st.session_state:
    st.session_state.usuarios_cadastrados = {
        "jefkar27@gmail.com": {
            "senha": "123", 
            "criacao": datetime.datetime.now() - datetime.timedelta(days=30),
            "tipo": "admin",
            "banco_clientes": [
                {"Nome": "Cliente Geral", "Email": "contato@clientegeral.com", "Telefone": "(21) 99999-9999", "Cidade": "Rio de Janeiro - RJ"}
            ]
        }
    }

# --- SISTEMA DE AUTENTICAÇÃO, CADASTRO E TESTE DE 24H ---
def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario_email" not in st.session_state:
        st.session_state.usuario_email = None

    if not st.session_state.autenticado:
        st.markdown("## 🔐 Área Restrita - Luminotécnica Profissional")
        st.markdown("Crie sua conta e ganhe **24 horas de teste gratuito**, ou faça login se já tiver cadastro.")
        
        tab_login, tab_cadastro, tab_planos = st.tabs(["🔑 Fazer Login", "📝 Criar Conta Grátis (Teste 24h)", "💳 Assinar (R$ 19,90/mês)"])
        
        with tab_login:
            with st.form("form_login"):
                email_input = st.text_input("E-mail cadastrado", value="").strip().lower()
                senha_input = st.text_input("Senha", type="password", value="").strip()
                btn_entrar = st.form_submit_button("Entrar no Sistema")
                
                if btn_entrar:
                    if email_input in st.session_state.usuarios_cadastrados:
                        user_data = st.session_state.usuarios_cadastrados[email_input]
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
                        st.error("E-mail não encontrado. Crie sua conta na aba ao lado!")

        with tab_cadastro:
            st.markdown("### ⚡ Comece a usar agora mesmo")
            st.markdown("Cadastre seu e-mail e ganhe **24 horas de acesso total e gratuito** para testar todos os recursos na obra.")
            
            with st.form("form_cadastro"):
                novo_email = st.text_input("Seu E-mail principal", value="").strip().lower()
                nova_senha = st.text_input("Crie uma Senha", type="password", value="").strip()
                btn_cadastrar = st.form_submit_button("Criar Conta e Iniciar Teste Grátis")
                
                if btn_cadastrar:
                    if novo_email and nova_senha:
                        if novo_email in st.session_state.usuarios_cadastrados:
                            st.warning("Este e-mail já está cadastrado. Faça login na primeira aba.")
                        else:
                            st.session_state.usuarios_cadastrados[novo_email] = {
                                "senha": nova_senha,
                                "criacao": datetime.datetime.now(),
                                "tipo": "cliente",
                                "assinante": False,
                                "banco_clientes": [
                                    {"Nome": "Cliente Exemplo", "Email": "exemplo@email.com", "Telefone": "(21) 98888-8888", "Cidade": "Rio de Janeiro - RJ"}
                                ]
                            }
                            st.session_state.autenticado = True
                            st.session_state.usuario_email = novo_email
                            st.success("Conta criada com sucesso! Seu teste de 24 horas começou.")
                            st.rerun()
                    else:
                        st.error("Preencha todos os campos para criar a conta.")

        with tab_planos:
            st.markdown("### 🚀 Assinatura Profissional")
            st.markdown("Tenha acesso ilimitado a todos os cálculos normativos (NBR ISO/CIE 8995-1), fitas LED e liberação de downloads de relatórios.")
            st.info("💡 **Apenas R$ 19,90 / mês** — Cancele quando quiser.")
            
            link_mercado_pago = "https://mpago.la/2sbQvQ9"
            st.link_button("💳 Assinar Agora por R$ 19,90/mês via Mercado Pago", link_mercado_pago, use_container_width=True)
            st.markdown("*(Assim que assinar, seu acesso é liberado permanentemente).*")
                    
        return False

    return True

if not verificar_autenticacao():
    st.stop()

email_atual = st.session_state.usuario_email
user_info_atual = st.session_state.usuarios_cadastrados.get(email_atual, {})

if email_atual in st.session_state.usuarios_cadastrados:
    if "banco_clientes" not in st.session_state.usuarios_cadastrados[email_atual]:
        st.session_state.usuarios_cadastrados[email_atual]["banco_clientes"] = [
            {"Nome": "Cliente Geral", "Email": "contato@clientegeral.com", "Telefone": "(21) 99999-9999", "Cidade": "Rio de Janeiro - RJ"}
        ]
    banco_clientes_usuario = st.session_state.usuarios_cadastrados[email_atual]["banco_clientes"]
else:
    banco_clientes_usuario = [{"Nome": "Cliente Geral", "Email": "contato@clientegeral.com", "Telefone": "(21) 99999-9999", "Cidade": "Rio de Janeiro - RJ"}]

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

if "banco_fitas" not in st.session_state:
    st.session_state.banco_fitas = [
        {"Fabricante": "Gaya", "Modelo": "Fita LED 10W/m IP20", "Lumens": 900, "Potencia": 10.0},
        {"Fabricante": "Super LED", "Modelo": "Fita LED 14.4W/m SMD5050", "Lumens": 1200, "Potencia": 14.4},
    ]

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
    r_t = p_t.add_run("RELATÓRIO LUMINOTÉCNICO CONSOLIDADO")
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

        h1 = doc.add_heading(level=2)
        r_h1 = h1.add_run("1. Identificação e Dados Geométricos")
        r_h1.font.size = Pt(10.5)
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
            ("Rebaixamento / Suspensão", "hp'", f"{amb['hp_desc']:.2f}", "m"),
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

        h2 = doc.add_heading(level=2)
        r_h2 = h2.add_run("2. Parâmetros Luminotécnicos")
        r_h2.font.size = Pt(10.5)
        r_h2.font.color.rgb = COR_TEXTO_TITULO

        t2 = doc.add_table(rows=6, cols=4)
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
            ("Iluminância Requerida", "Ereq", f"{amb['lux_req']:.2f} lx", "Manual / NBR ISO/CIE 8995-1"),
            ("Fonte Luminosa / Equipamento", "Φ", f"{amb['fluxo_unidade_rel']:,.2f} lm".replace(",", "."), amb['modelo_lum']),
            ("Potência Unitária", "Punit", f"{amb['pot_unidade_rel']:.2f}", amb['unidade_pot_desc']),
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

        h3 = doc.add_heading(level=2)
        r_h3 = h3.add_run("3. Resultados do Dimensionamento e Espaçamentos")
        r_h3.font.size = Pt(10.5)
        r_h3.font.color.rgb = COR_TEXTO_TITULO

        t3 = doc.add_table(rows=13, cols=4)
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
            ("Qtd. de Equipamentos / Metragem", f"{amb['qtd_teorica']:.2f}", f"{amb['qtd_real_str']}", amb['unidade_medida_qtd']),
            ("Arranjo / Distribuição", f"{amb['arranjo_str']}", f"{amb['arranjo_str']}", "arr."),
            ("Distância entre Pontos (C)", f"{amb['dist_c_entre']:.2f}", f"{amb['dist_c_entre']:.2f}", "m"),
            ("Distância até Parede (C) [Metade]", f"{amb['dist_c_parede']:.2f}", f"{amb['dist_c_parede']:.2f}", "m"),
            ("Distância entre Pontos (L)", f"{amb['dist_l_entre']:.2f}", f"{amb['dist_l_entre']:.2f}", "m"),
            ("Distância até Parede (L) [Metade]", f"{amb['dist_l_parede']:.2f}", f"{amb['dist_l_parede']:.2f}", "m"),
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

        h4 = doc.add_heading(level=2)
        r_h4 = h4.add_run("4. Parecer Técnico")
        r_h4.font.size = Pt(10.5)
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

# --- INTERFACE PRINCIPAL ---
st.title("💡 Luminotécnica Profissional")
st.markdown(f"**Sessão Ativa:** {st.session_state.get('usuario_email', 'Usuário')}")

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

# --- MÓDULO DE CADASTRO DE CLIENTES (PRIVATIVO POR USUÁRIO) ---
st.markdown("### 📇 Cadastro e Seleção de Clientes")
with st.expander("➕ Cadastrar Novo Cliente no Sistema"):
    with st.form("form_novo_cliente"):
        col_nc1, col_nc2 = st.columns(2)
        with col_nc1:
            cad_nome_cli = st.text_input("Nome / Razão Social do Cliente")
            cad_tel_cli = st.text_input("Telefone / WhatsApp")
        with col_nc2:
            cad_email_cli = st.text_input("E-mail do Cliente")
            cad_cidade_cli = st.text_input("Cidade / Estado (Ex: Rio de Janeiro - RJ)")
            
        btn_salvar_cliente = st.form_submit_button("Salvar Cliente")
        if btn_salvar_cliente:
            if cad_nome_cli.strip() != "":
                novo_cliente_obj = {
                    "Nome": cad_nome_cli,
                    "Email": cad_email_cli if cad_email_cli else "Não informado",
                    "Telefone": cad_tel_cli if cad_tel_cli else "Não informado",
                    "Cidade": cad_cidade_cli if cad_cidade_cli else "Não informado"
                }
                st.session_state.usuarios_cadastrados[email_atual]["banco_clientes"].append(novo_cliente_obj)
                st.success(f"Cliente '{cad_nome_cli}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("O nome do cliente é obrigatório.")

lista_nomes_clientes = [c["Nome"] for c in banco_clientes_usuario]
cliente_selecionado_nome = st.selectbox("Selecione o Cliente para este Projeto", lista_nomes_clientes)
cliente_dados_obj = next((c for c in banco_clientes_usuario if c["Nome"] == cliente_selecionado_nome), banco_clientes_usuario[0])

st.markdown("---")

aba_principal, aba_fitas = st.tabs(["🏠 1. Cálculo de Luminárias e Painéis", "✨ 2. Projeto de Fitas LED (PRO)"])

with aba_principal:
    st.markdown(f"### 🛋️ Ambientes para o Cliente: **{cliente_dados_obj['Nome']}**")

    with st.expander("⚙️ Cadastrar Nova Luminária no Banco"):
        with st.form("form_nova_lum"):
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
                    "Fabricante": novo_fab,
                    "Modelo": novo_mod,
                    "Lumens": novo_lum,
                    "Potencia": nova_pot,
                    "Tipo": novo_tipo
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

            lux_padrao_norma = TABELA_NORMA[tipo_atividade]
            col_lux1, col_lux2 = st.columns(2)
            with col_lux1:
                usar_lux_manual = st.checkbox("Alterar Iluminância (Lux) Manualmente?", key=f"chk_lux_{amb_atual['id']}")
            with col_lux2:
                if usar_lux_manual:
                    lux_req = st.number_input("Iluminância Desejada (lx)", value=float(lux_padrao_norma), step=10.0, key=f"lux_man_{amb_atual['id']}")
                else:
                    lux_req = float(lux_padrao_norma)
                    st.markdown(f"**Iluminância Normativa:** {lux_req} lx")

            st.markdown("##### 💡 Seleção de Luminária / Painel")
            banco_ativo = st.session_state.banco_luminarias
            opcoes_banco_str = [f"{l['Fabricante']} - {l['Modelo']} ({l['Lumens']} lm / {l['Potencia']} W)" for l in banco_ativo]
            opcoes_banco_str.append("⚙️ Inserir Manual / Personalizado")
            
            escolha_banco = st.selectbox("Selecionar Equipamento", opcoes_banco_str, key=f"lum_escolha_{amb_atual['id']}")

            if escolha_banco != "⚙️ Inserir Manual / Personalizado":
                idx_escolhido = opcoes_banco_str.index(escolha_banco)
                lum_sel = banco_ativo[idx_escolhido]
                fluxo_base, potencia_base = lum_sel["Lumens"], lum_sel["Potencia"]
                modelo_desc_relatorio = f"[Painel/Luminária] {lum_sel['Fabricante']} - {lum_sel['Modelo']}"
            else:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    fluxo_base = st.number_input("Fluxo Luminoso da Unidade (lm)", value=1920.0, step=50.0, key=f"fluxo_man_lum_{amb_atual['id']}")
                with col_m2:
                    potencia_base = st.number_input("Potência Unitária (W)", value=24.0, step=1.0, key=f"pot_man_lum_{amb_atual['id']}")
                modelo_desc_relatorio = "[Painel/Luminária] Personalizado"

            st.markdown("##### Geometria e Fatores")
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

            fluxo_lampada = fluxo_base
            potencia_lampada = potencia_base
            qtd_teorica = fluxo_req / fluxo_lampada if fluxo_lampada > 0 else 0
            qtd_min_sugerida = math.ceil(qtd_teorica)
            if qtd_min_sugerida < 1:
                qtd_min_sugerida = 1

            st.markdown("##### 🎛️ Configuração do Arranjo (Linhas e Colunas)")
            col_arr1, col_arr2 = st.columns(2)
            with col_arr1:
                linhas_man = st.number_input("Quantidade de Linhas", min_value=1, value=1, step=1, key=f"linhas_man_{amb_atual['id']}")
            with col_arr2:
                colunas_man = st.number_input("Quantidade de Colunas", min_value=1, value=2, step=1, key=f"colunas_man_{amb_atual['id']}")

            qtd_real = linhas_man * colunas_man

            if qtd_real < qtd_min_sugerida:
                st.warning(f"⚠️ O arranjo selecionado ({qtd_real} un) está abaixo do mínimo teórico calculado ({qtd_min_sugerida} un).")

            dist_c_entre = comp / colunas_man if colunas_man > 0 else comp
            dist_c_parede = dist_c_entre / 2.0
            dist_l_entre = larg / linhas_man if linhas_man > 0 else larg
            dist_l_parede = dist_l_entre / 2.0

            fluxo_instalado = qtd_real * fluxo_lampada
            pot_total = qtd_real * potencia_lampada
            
            lux_real = (fluxo_instalado * fator_u * fator_d) / area if area > 0 else 0
            dpi = pot_total / area if area > 0 else 0
            variacao_fluxo_pct = ((fluxo_instalado - fluxo_req) / fluxo_req) * 100 if fluxo_req > 0 else 0
            conforme = lux_real >= lux_req

            st.success(f"✨ **Conferência de Quantidade:** **{int(qtd_real)} unidades** adotadas no arranjo ({area:.1f} m²).")
            st.info(f"📏 **Espaçamentos:** C={dist_c_entre:.2f}m / L={dist_l_entre:.2f}m | **Afastamento da Parede:** C={dist_c_parede:.2f}m / L={dist_l_parede:.2f}m | **Lux Real:** {lux_real:.2f} lx")

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
                "fluxo_unidade_rel": fluxo_lampada,
                "pot_unidade_rel": potencia_lampada,
                "unidade_pot_desc": "Consumo Unitário (W)",
                "fator_u": fator_u,
                "fator_d": fator_d,
                "desc_utilizacao": "Ambiente residencial / Padrão",
                "desc_depreciacao": "Limpeza periódica / Padrão",
                "modelo_lum": modelo_desc_relatorio,
                "fluxo_instalado": fluxo_instalado,
                "qtd_teorica": qtd_teorica,
                "qtd_real_str": str(int(qtd_real)),
                "unidade_medida_qtd": "un",
                "arranjo_str": f"{linhas_man} Linhas x {colunas_man} Colunas",
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

with aba_fitas:
    st.markdown("### ✨ Projeto de Fitas LED Lineares")
    col_fita_1, col_fita_2 = st.columns(2)
    with col_fita_1:
        fita_comp = st.number_input("Comprimento Linear da Sanca / Perfil (m)", value=10.0, step=0.5, key="fita_comp_m")
        fita_lux_req = st.number_input("Iluminância Alvo (lx)", value=200.0, step=10.0, key="fita_lux_alvo")
    with col_fita_2:
        banco_fita_opcoes = [f"{f['Fabricante']} - {f['Modelo']} ({f['Lumens']} lm/m)" for f in st.session_state.banco_fitas]
        banco_fita_opcoes.append("⚙️ Personalizada")
        sel_fita_aba = st.selectbox("Escolher Fita LED", banco_fita_opcoes, key="sel_fita_aba_key")
        
        if "Personalizada" not in sel_fita_aba:
            idx_f = banco_fita_opcoes.index(sel_fita_aba)
            lm_metro = st.session_state.banco_fitas[idx_f]["Lumens"]
        else:
            lm_metro = st.number_input("Fluxo por Metro (lm/m)", value=900.0, step=50.0, key="fita_lm_man")

    metragem_calculada_fita = (fita_lux_req * fita_comp) / lm_metro if lm_metro > 0 else 0
    st.info(f"📏 **Metragem Teórica Calculada de Fita LED:** **{metragem_calculada_fita:.2f} metros lineares**.")

st.subheader("3. Emissão de Relatório Luminotécnico")

# Verifica se o usuário logado é admin ou assinante liberado para download
is_admin_or_subscriber = (user_info_atual.get("tipo") == "admin" or user_info_atual.get("assinante", False))

if not is_admin_or_subscriber:
    st.warning("🔒 **Recurso Exclusivo para Assinantes:** O período de teste permite realizar os cálculos na tela, mas a geração e o download dos relatórios oficiais (.docx e .pdf) exigem uma assinatura ativa. Vá na aba **'Assinar (R$ 19,90/mês)'** no topo da página para liberar!")
else:
    if st.button("📄 Gerar Relatório Luminotécnico (.docx)", use_container_width=True):
        dados_prof_dict = {
            "nome": prof_nome if prof_nome else "Não informado",
            "registro": prof_registro if prof_registro else "Não informado",
            "celular": prof_celular if prof_celular else "Não informado",
            "email": prof_email if prof_email else "Not informed"
        }
        
        logo_bytes = io.BytesIO(logo_upload.getvalue()) if logo_upload is not None else None
        arquivo_docx_bytes = gerar_docx_consolidado(cliente_dados_obj, dados_prof_dict, lista_calculos_ambientes, logo_file=logo_bytes)
        
        st.success("Relatório gerado com sucesso!")
        st.download_button(
            label="📥 Baixar Relatório em Word (.docx)",
            data=arquivo_docx_bytes,
            file_name=f"Relatorio_Luminotecnico_{cliente_dados_obj['Nome'].replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    # Opção segura e robusta para salvar em PDF via Impressão Nativa do Navegador
    st.markdown("""
        <div style="margin-top: 15px; text-align: center;">
            <button onclick="window.print()" style="background-color: #1A365D; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold; width: 100%;">
                🖨️ Salvar Relatório em PDF / Imprimir (Nativo)
            </button>
            <p style="font-size: 12px; color: gray; margin-top: 5px;">*Dica: Ao clicar, selecione "Salvar como PDF" na janela de impressão do seu navegador.</p>
        </div>
    """, unsafe_allow_html=True),
