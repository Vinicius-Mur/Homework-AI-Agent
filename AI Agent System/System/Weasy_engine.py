import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

def setup_fonts():
    """Tenta carregar as fontes profissionais. Se falhar, usa as fontes padrão do sistema."""
    font_regular, font_bold, font_title = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Bold'
    
    if os.path.exists('/content/fonts/Carlito-Regular.ttf'):
        pdfmetrics.registerFont(TTFont('Carlito', '/content/fonts/Carlito-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Carlito-Bold', '/content/fonts/Carlito-Bold.ttf'))
        font_regular, font_bold = 'Carlito', 'Carlito-Bold'
        
    if os.path.exists('/content/fonts/Poppins-Bold.ttf'):
        pdfmetrics.registerFont(TTFont('Poppins-Bold', '/content/fonts/Poppins-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Poppins-Medium', '/content/fonts/Poppins-Medium.ttf'))
        font_title = 'Poppins-Bold'
        
    return font_regular, font_bold, font_title

def build_advanced_pdf(json_data: dict, output_path: str):
    font_regular, font_bold, font_title = setup_fonts()
    
    # Paleta de Cores Exata do Design System
    INK = colors.HexColor("#1E2A38")
    MUTED = colors.HexColor("#5B6776")
    BLUE_TINT = colors.HexColor("#E8F1FB")
    BLUE_MAIN = colors.HexColor("#2B6CB0")
    YELLOW_TINT = colors.HexColor("#FFF6D6")
    YELLOW_MAIN = colors.HexColor("#F2B600")
    GREEN_TINT = colors.HexColor("#E4F5EC")
    GREEN_MAIN = colors.HexColor("#2F9E6B")

    # Configuração da Página A4 com as Margens do Design System
    doc = BaseDocTemplate(output_path, pagesize=A4, 
                          leftMargin=18*mm, rightMargin=18*mm, 
                          topMargin=24*mm, bottomMargin=20*mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([PageTemplate(id='First', frames=frame)])
    
    # Estilos Tipográficos
    styles = {
        'Title': ParagraphStyle('Title', fontName=font_title, fontSize=22, leading=28, textColor=INK, spaceAfter=10),
        'Subtitle': ParagraphStyle('Subtitle', fontName=font_regular, fontSize=11, leading=16, textColor=MUTED, spaceAfter=15),
        'H2': ParagraphStyle('H2', fontName=font_title, fontSize=14, leading=18, textColor=INK, spaceAfter=10, spaceBefore=15),
        'Body': ParagraphStyle('Body', fontName=font_regular, fontSize=12, leading=18, textColor=INK),
        'BodyBold': ParagraphStyle('BodyBold', fontName=font_bold, fontSize=12, leading=18, textColor=INK),
        'Teacher': ParagraphStyle('Teacher', fontName=font_regular, fontSize=10, leading=14, textColor=MUTED),
        'Label': ParagraphStyle('Label', fontName=font_title, fontSize=9, textColor=colors.white)
    }
    
    story = []
    
    # 1. Cabeçalho Frontal
    story.append(Paragraph(json_data.get('lesson_title', 'Lesson').upper(), styles['Title']))
    story.append(Paragraph(f"<b>LEVEL:</b> {json_data.get('cefr_level', '')} | <b>FOCUS:</b> {json_data.get('focus_summary', '')}", styles['Subtitle']))
    
    # 2. Teacher Rail (Faixa Cinza)
    teacher_text = f"<b>TEACHER NOTES:</b> {json_data.get('teacher_lead_in', '')}"
    t_rail = Table([[Paragraph(teacher_text, styles['Teacher'])]], colWidths=[doc.width])
    t_rail.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F3F5F8")),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_rail)
    story.append(Spacer(1, 15))
    
    # 3. Bloco Azul: Comprehensible Input
    story.append(Paragraph("01 COMPREHENSIBLE INPUT", styles['H2']))
    input_html = json_data.get('comprehensible_input_text', '').replace('\n', '<br/>')
    t_input = Table([[Paragraph(input_html, styles['Body'])]], colWidths=[doc.width])
    t_input.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE_TINT),
        ('LINEBEFORE', (0,0), (0,-1), 4, BLUE_MAIN),
        ('PADDING', (0,0), (-1,-1), 14),
    ]))
    story.append(t_input)
    story.append(Spacer(1, 15))
    
    # 4. Bloco Amarelo: Word Bank
    if json_data.get('word_bank'):
        story.append(Paragraph("WORD BANK", styles['H2']))
        wb_data = []
        for wb in json_data.get('word_bank', []):
            wb_data.append(Paragraph(f"<b>{wb.get('word')}</b>: {wb.get('meaning_or_false_friend')}", styles['Body']))
            wb_data.append(Spacer(1, 4))
            
        t_wb = Table([[wb_data]], colWidths=[doc.width])
        t_wb.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), YELLOW_TINT),
            ('LINEBEFORE', (0,0), (0,-1), 4, YELLOW_MAIN),
            ('PADDING', (0,0), (-1,-1), 14),
        ]))
        story.append(t_wb)
        story.append(Spacer(1, 15))
    
    # 5. Bloco Verde: Shadowing
    if json_data.get('shadowing_guide'):
        story.append(Paragraph("02 SHADOWING", styles['H2']))
        sh_data = []
        for idx, sh in enumerate(json_data.get('shadowing_guide', []), 1):
            sh_data.append(Paragraph(f"<b>{idx}. {sh.get('sentence')}</b>", styles['BodyBold']))
            sh_data.append(Paragraph(f"<i>Tip: {sh.get('tips')}</i>", styles['Teacher']))
            sh_data.append(Spacer(1, 6))
            
        t_sh = Table([[sh_data]], colWidths=[doc.width])
        t_sh.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GREEN_TINT),
            ('LINEBEFORE', (0,0), (0,-1), 4, GREEN_MAIN),
            ('PADDING', (0,0), (-1,-1), 14),
        ]))
        story.append(t_sh)
        story.append(Spacer(1, 15))
    
    # 6. TBLT Mission
    mission = json_data.get('tblt_mission', {})
    if mission:
        story.append(Paragraph("03 TASK-BASED LEARNING (TBLT)", styles['H2']))
        
        # Outcome bar escura
        t_mission_title = Table([[Paragraph(f"MISSION: {mission.get('title', '').upper()}", styles['Label'])]], colWidths=[doc.width])
        t_mission_title.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), INK),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_mission_title)
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Role & Problem:</b> {mission.get('role_problem', '')}", styles['Body']))
        story.append(Spacer(1, 8))
        
        for step in mission.get('steps', []):
            story.append(Paragraph(f"• {step}", styles['Body']))
            story.append(Spacer(1, 4))
        
    doc.build(story)
    print(f"✨ PDF avançado guardado com sucesso em: {output_path}")