from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def gerar_pdf_projeto(dados_projeto):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Cabeçalho / Rodapé / Marca d'água simulada
    c.drawString(100, 750, "RELATÓRIO TÉCNICO - DIMENSIONAMENTO LUMINOTÉCNICO")
    c.drawString(100, 735, f"Cliente: {dados_projeto.get('cliente', 'Não informado')}")
    c.line(100, 725, 500, 725)
    
    # Conteúdo dinâmico
    y = 690
    for chave, valor in dados_projeto.items():
        c.drawString(100, y, f"{chave}: {valor}")
        y -= 20
        
    # Rodapé profissional
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(100, 40, "Gerado por Sistema de Dimensionamento Profissional | Todos os direitos reservados.")
    
    c.save()
    buffer.seek(0)
    return buffer

# Botão no Streamlit para download do PDF
# pdf_file = gerar_pdf_projeto(st.session_state)
# st.download_button("Baixar Laudo em PDF", data=pdf_file, file_name="laudo_luminotecnico.pdf", mime="application/pdf")
