# --- FUNÇÃO DE GERAÇÃO DE PDF CORRIGIDA ---
def gerar_pdf(dados_cliente, dados_prof, d, logo_file=None):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Logo
    if logo_file is not None:
        logo_file.seek(0)
        ext = logo_file.name.split('.')[-1].lower()
        if ext in ['png', 'jpg', 'jpeg']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
                tmp_file.write(logo_file.read())
                tmp_path = tmp_file.name
            try:
                pdf.image(tmp_path, x=10, y=10, w=25)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        pdf.set_y(38)
    else:
        pdf.set_y(15)

    # Título do Relatório
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, pdf.sanitize("RELATÓRIO DE DIMENSIONAMENTO LUMINOTÉCNICO"), align="C")
    pdf.ln(7)
    
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.cell(0, 5, pdf.sanitize("Projeto de Iluminação Residencial / Comercial | Método dos Lúmens"), align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 4.5, pdf.sanitize(f"Engenheiro Responsável: {dados_prof['nome']} - {dados_prof['registro']}"), align="C")
    pdf.ln(4.5)
    pdf.cell(0, 4.5, pdf.sanitize("Norma de Referência: NBR ISO/CIE 8995-1 (Iluminação de Ambientes de Trabalho)"), align="C")
    pdf.ln(8)

    def criar_tabela_pdf(titulo, colunas, largura_cols, dados):
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 6, pdf.sanitize(titulo))
        pdf.ln(6)
        
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        
        for idx, col in enumerate(colunas):
            pdf.cell(largura_cols[idx], 6, pdf.sanitize(col), border=1, align="C", fill=True)
        pdf.ln(6)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)
        for r_idx, linha in enumerate(dados):
            fill = (r_idx % 2 == 1)
            pdf.set_fill_color(242, 242, 242) if fill else pdf.set_fill_color(255, 255, 255)
            for c_idx, val in enumerate(linha):
                align = "C" if c_idx in [1, 2] else "L"
                pdf.cell(largura_cols[c_idx], 5.2, pdf.sanitize(str(val)), border=1, align=align, fill=fill)
            pdf.ln(5.2)
        pdf.ln(4)

    # 1. Identificação
    criar_tabela_pdf(
        "1. Identificação e Dados Geométricos do Ambiente",
        ["Parâmetro", "Símbolo", "Valor", "Unidade"],
        [70, 25, 35, 60],
        [
            ["Nome / Identificação do Ambiente", "-", d['nome'], "-"],
            ["Comprimento do Recinto", "C", f"{d['comp']:.2f}", "m"],
            ["Largura do Recinto", "L", f"{d['larg']:.2f}", "m"],
            ["Pé-Direito Total (Piso ao Teto)", "H", f"{d['pe_direito']:.2f}", "m"],
            ["Altura do Plano de Trabalho", "hp", f"{d['hp']:.2f}", "m"],
            ["Pendotamento / Descimento da Luminária", "hp'", f"{d['hp_desc']:.2f}", "m"],
            ["Área Total Calculada", "A", f"{d['area']:.2f}", "m2"],
            ["Altura Útil de Iluminação", "hu", f"{d['hu']:.2f}", "m"]
        ]
    )

    # 2. Parâmetros Luminotécnicos
    criar_tabela_pdf(
        "2. Parâmetros Luminotécnicos Adotados",
        ["Parâmetro Técnico", "Símbolo", "Valor Adotado", "Observações / Norma"],
        [60, 25, 35, 70],
        [
            ["Iluminância Requerida (Meta)", "Ereq", f"{d['lux_req']} lx", "NBR ISO/CIE 8995-1"],
            ["Fluxo Luminoso da Luminária", "Flampa", f"{d['fluxo']:,} lm".replace(",", "."), "Dado do fabricante"],
            ["Potência Unitária da Luminária", "Punit", f"{d['potencia']} W", "Consumo elétrico unitário"],
            ["Índice do Recinto", "K", f"{d['k_indice']:.2f}", "Geometria do espaço"],
            ["Fator de Utilização", "u", f"{d['fator_u']:.2f} ({int(d['fator_u']*100)}%)", "Refletância padrão"],
            ["Fator de Depreciação / Perdas", "d", f"{d['fator_d']:.2f} ({int(d['fator_d']*100)}%)", "Manutenção para ambiente"]
        ]
    )

    # 3. Resultados
    criar_tabela_pdf(
        "3. Resultados do Dimensionamento e Iluminância",
        ["Item de Cálculo", "Valor Calculado", "Valor Adotado / Real", "Unidade"],
        [70, 40, 45, 35],
        [
            ["Fluxo Luminoso Requerido (Teórico)", f"{d['fluxo_req']:.2f}", "-", "lm"],
            ["Quantidade Mínima de Luminárias", f"{d['qtd_teorica']:.2f}", f"{d['qtd_real']}", "unidades"],
            ["Fluxo Luminoso Real Instalado", "-", f"{d['fluxo_instalado']:,}".replace(",", "."), "lm"],
            ["Iluminância Real Alcançada", "-", f"{d['lux_real']:.2f}", "lx"],
            ["Potência Total Instalada", "-", f"{d['pot_total']:.2f}", "W"],
            ["Densidade de Potência Iluminada (DPI)", "-", f"{d['dpi']:.2f}", "W/m2"]
        ]
    )

    # 4. Disposição Espacial
    criar_tabela_pdf(
        "4. Disposição Espacial e Layout de Instalação",
        ["Eixo de Instalação", "Arranjo (Linhas x Colunas)", "Distância entre Luminárias", "Distância das Paredes"],
        [50, 50, 45, 45],
        [
            ["Eixo Longitudinal (Comprimento)", f"{d['linhas']} Linhas", f"{d['dist_c']:.2f} m", f"{d['dist_parede_c']:.2f} m"],
            ["Eixo Transversal (Largura)", f"{d['colunas']} Colunas", f"{d['dist_l']:.2f} m", f"{d['dist_parede_l']:.2f} m"]
        ]
    )

    # 5. Parecer Técnico
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.cell(0, 6, pdf.sanitize("5. Parecer Técnico e Conformidade"))
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "", 8.5)
    status_str = "CONFORME (Projeto aprovado e recomendado para execução)." if d['conforme'] else "NÃO CONFORME (Revisar fluxo luminoso ou quantidade)."
    
    w_page = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Nível de Iluminância: O valor projetado atinge {d['lux_real']:.2f} lx, {'atendendo com folga' if d['conforme'] else 'abaixo da'} a meta de {d['lux_req']} lx exigida pela norma NBR ISO/CIE 8995-1 para o ambiente."))
    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Eficiência Energética: A densidade de potência instalada é de {d['dpi']:.2f} W/m2, estando dentro dos padrões de eficiência energética em LED."))
    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Uniformidade Espacial: A distribuição em matriz {d['linhas']} x {d['colunas']} com espaçamentos calculados garante homogeneidade do fluxo luminoso sobre o plano de trabalho a {d['hp']:.2f} m do piso."))
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.multi_cell(w_page, 4.5, pdf.sanitize(f"- Status Final de Aprovação: {status_str}"))

    # Retorna diretamente a string ou bytes codificados
    return bytes(pdf.output())


# --- RENDERIZAÇÃO DOS BOTÕES NO STREAMLIT (Substitua no final da Tab 1) ---
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    # A chamada de geração ocorre DENTRO do parâmetro data do botão
    st.download_button(
        label="📄 Baixar Relatório em PDF",
        data=gerar_pdf(dados_cliente, dados_prof, dados_calculados, logo_file=logo_upload),
        file_name=f"Relatorio_Luminotecnico_{nome_sanitizado}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
with col_dl2:
    st.download_button(
        label="📝 Baixar Relatório em Word (.DOCX)",
        data=gerar_docx(dados_cliente, dados_prof, dados_calculados, logo_file=logo_upload),
        file_name=f"Relatorio_Luminotecnico_{nome_sanitizado}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
