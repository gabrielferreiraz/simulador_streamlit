"""
Módulo para a geração de relatórios de simulação em formato PDF.

Utiliza a biblioteca FPDF para criar documentos personalizados com os resultados
da simulação, prontos para serem compartilhados com os clientes.
"""
import logging
from datetime import datetime
from typing import Dict, Optional, Union

from fpdf import FPDF
from src.utils.style_utils import sanitize_text_for_pdf

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

class PDF(FPDF):
    """
    Classe FPDF personalizada para definir um cabeçalho e rodapé padrão para os relatórios.
    """
    def header(self):
        """Define o cabeçalho do documento PDF."""
        try:
            self.set_font('Arial', 'B', 20)
            self.set_text_color(4, 75, 132)  # Azul Servopa
            self.cell(0, 10, "Reobote Consórcios", 0, 1, 'C')
            self.set_font('Arial', 'I', 12)
            self.set_text_color(128)
            self.cell(0, 10, "Transformar desejos, reais, em realidade.", 0, 1, 'C')
            self.set_line_width(0.5)
            self.set_draw_color(4, 75, 132)
            self.line(10, 35, 200, 35)
            self.ln(15)
        except Exception as e:
            logger.error(f"Erro ao gerar o cabeçalho do PDF: {e}", exc_info=True)
            # Se o cabeçalho falhar, não interrompe a geração do resto do PDF

    def footer(self):
        """Define o rodapé do documento PDF."""
        try:
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        except Exception as e:
            logger.error(f"Erro ao gerar o rodapé do PDF: {e}", exc_info=True)
            # Se o rodapé falhar, não interrompe a geração

def create_creative_pdf_to_buffer(
    cliente_nome: str,
    consultor_nome: str,
    dados: Dict[str, Union[str, int, float]]
) -> Optional[bytes]:
    """
    Cria um relatório de simulação em PDF e o retorna como um buffer de bytes.

    Args:
        cliente_nome (str): O nome do cliente para o qual a simulação foi feita.
        consultor_nome (str): O nome do consultor que gerou a simulação.
        dados (Dict[str, Union[str, int, float]]): Um dicionário com os dados da simulação
                                                   (e.g., {"Crédito Disponível": "R$ 100.000,00"}).

    Returns:
        Optional[bytes]: Um buffer de bytes contendo o PDF gerado, ou None se ocorrer um erro.
    """
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", "", 14)

        # --- Seção de Saudação e Introdução ---
        pdf.cell(0, 10, sanitize_text_for_pdf(f"Olá, {cliente_nome}!"), 0, 1)
        pdf.set_font("Arial", "", 12)
        intro_text = "Conforme nossa conversa, preparei uma simulação de consórcio personalizada para você. Abaixo estão os detalhes dos valores:"
        pdf.multi_cell(0, 8, sanitize_text_for_pdf(intro_text))
        pdf.ln(10)

        # --- Tabela de Resultados ---
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(4, 75, 132)  # Azul Servopa
        pdf.set_text_color(255, 255, 255)
        pdf.cell(95, 10, "Descrição", 1, 0, "C", 1)
        pdf.cell(95, 10, "Valor", 1, 1, "C", 1)
        pdf.set_text_color(0, 0, 0)
        
        fill = False
        for i, (chave, valor) in enumerate(dados.items()):
            pdf.set_fill_color(240, 240, 240)
            
            # Sanitiza todas as entradas de texto para prevenir erros de encoding
            safe_chave = sanitize_text_for_pdf(chave)
            safe_valor = sanitize_text_for_pdf(str(valor))
            
            pdf.set_font("Arial", "B" if i == 0 else "", 12)
            pdf.cell(95, 10, safe_chave, 1, 0, 'L', fill)
            pdf.cell(95, 10, safe_valor, 1, 1, 'R', fill)
            fill = not fill
            
        pdf.ln(15)

        # --- Seção de Marketing e Fechamento ---
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(4, 75, 132)
        pdf.cell(0, 10, "A Escolha Certa para a Sua Conquista", 0, 1, 'C')
        pdf.ln(5)

        pdf.set_font("Arial", "I", 11)
        pdf.set_text_color(0, 0, 0)
        
        phrase1 = '"Consórcio é a Escolha Clara e Econômica para Alcançar Seus Sonhos!"'
        pdf.multi_cell(0, 8, sanitize_text_for_pdf(phrase1), 0, 'C')
        pdf.ln(3)

        phrase2 = '"Nosso grande diferencial está no pós-venda: nossa venda só termina quando você adquire o seu bem."'
        pdf.multi_cell(0, 8, sanitize_text_for_pdf(phrase2), 0, 'C')
        pdf.ln(10)
        
        pdf.set_font("Arial", "", 11)
        closing_text = f"Estou à disposição para esclarecer qualquer dúvida e ajudar você a realizar seu sonho!\n\nAtenciosamente,\n{sanitize_text_for_pdf(consultor_nome)}"
        pdf.multi_cell(0, 8, closing_text)
        
        pdf.ln(5)
        pdf.set_font("Arial", "I", 9)
        pdf.cell(0, 10, f"Simulação gerada em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", 0, 1)
        
        # Retorna o PDF como um buffer de bytes
        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        logger.critical(f"Falha crítica ao gerar o PDF para o cliente '{cliente_nome}'. Erro: {e}", exc_info=True)
        return None
