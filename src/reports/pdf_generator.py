import io
from datetime import datetime
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 20)
        self.set_text_color(4, 75, 132)
        self.cell(0, 10, "Reobote Consórcios", 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.set_text_color(128)
        self.cell(0, 10, "Transformar desejos, reais, em realidade.", 0, 1, 'C')
        self.set_line_width(0.5)
        self.set_draw_color(4, 75, 132)
        self.line(10, 35, 200, 35)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_creative_pdf_to_buffer(cliente_nome, consultor_nome, dados):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 14)
    
    # Função auxiliar para sanitizar texto para o FPDF
    def sanitize_text(text):
        return str(text or "").encode('latin-1', 'replace').decode('latin-1')

    pdf.cell(0, 10, f"Olá, {sanitize_text(cliente_nome)}!", 0, 1)
    pdf.set_font("Arial", "", 12)
    
    intro_text = "Conforme nossa conversa, preparei uma simulação de consórcio personalizada para você. Abaixo estão os detalhes dos valores:"
    pdf.multi_cell(0, 8, sanitize_text(intro_text))
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(4, 75, 132)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 10, "Descrição", 1, 0, "C", 1)
    pdf.cell(95, 10, "Valor", 1, 1, "C", 1)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    
    fill = False
    for i, (chave, valor) in enumerate(dados.items()):
        pdf.set_fill_color(240, 240, 240)
        
        safe_chave = sanitize_text(chave)
        safe_valor = sanitize_text(valor)
        
        if i == 0:
            pdf.set_font("Arial", "B", 12)
        else:
            pdf.set_font("Arial", "", 12)
            
        pdf.cell(95, 10, safe_chave, 1, 0, 'L', fill)
        pdf.cell(95, 10, safe_valor, 1, 1, 'R', fill)
        fill = not fill
        
    pdf.ln(15)

    # Seção de marketing
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(4, 75, 132)
    pdf.cell(0, 10, "A Escolha Certa para a Sua Conquista", 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font("Arial", "I", 11)
    pdf.set_text_color(0, 0, 0)
    
    phrase1 = '"Consórcio é a Escolha Clara e Econômica para Alcançar Seus Sonhos!"'
    pdf.multi_cell(0, 8, sanitize_text(phrase1), 0, 'C')
    pdf.ln(3)

    phrase2 = '"Nosso grande diferencial está no pós-venda: nossa venda só termina quando você adquire o seu bem."'
    pdf.multi_cell(0, 8, sanitize_text(phrase2), 0, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 11)
    
    closing_text = f"Estou à disposição para esclarecer qualquer dúvida e ajudar você a realizar seu sonho!\n\nAtenciosamente,\n{sanitize_text(consultor_nome)}"
    pdf.multi_cell(0, 8, closing_text)
    
    pdf.ln(5)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 10, f"Simulação gerada em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", 0, 1)
    
    # A biblioteca fpdf lida com a escrita em buffer diretamente
    return bytes(pdf.output(dest='S'))