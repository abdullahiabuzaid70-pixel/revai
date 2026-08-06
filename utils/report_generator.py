"""
PDF Report Generator - creates the 1-page Leakage Report
Uses fpdf2 for PDF generation

Note: fpdf2 built-in fonts (Helvetica) use latin-1 encoding.
All special Unicode characters must be replaced with ASCII equivalents:
- Em dash (--) -> hyphen (-)
- Naira sign -> NGN prefix
- Curly quotes -> straight quotes
"""
from fpdf import FPDF
from datetime import datetime
import os
import re


def clean_text(text):
    """Replace Unicode characters with ASCII-safe equivalents for fpdf2."""
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        '\u2014': '-',   # em dash
        '\u2013': '-',   # en dash
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u20a6': 'NGN', # naira sign
        '\u2026': '...', # ellipsis
        '\u2013': '-',   # en dash
        '\u00a0': ' ',   # non-breaking space
        '\u2022': '*',   # bullet
        '\u2192': '->',  # right arrow
        '\u2190': '<-',  # left arrow
        '\u2713': 'OK', # check mark
        '\u2717': 'X',  # cross mark
        '\u2714': 'OK', # heavy check
        '\u2716': 'X',  # heavy cross
    }
    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)
    # Remove any remaining non-latin-1 characters
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text


class LeakageReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        pass
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(107, 114, 128)
        footer_text = f"RevAI Leakage Report - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Findings are automated and should be reviewed by a qualified accountant."
        self.cell(0, 5, clean_text(footer_text), align='C')
    
    def section_title(self, title):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(15, 23, 42)
        self.cell(0, 6, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)


def generate_report(
    company_name,
    audit_period,
    total_leakage,
    total_revenue,
    detection_summaries,
    top_actions,
    ai_summary,
    output_path=None
):
    """
    Generate the 1-page PDF Leakage Report.
    """
    pdf = LeakageReportPDF()
    pdf.add_page()
    
    # === HEADER ===
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, clean_text("RevAI - Financial Leakage Report"), new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 5, clean_text(f"Prepared for: {company_name}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, clean_text(f"Audit Period: {audit_period}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, clean_text(f"Date: {datetime.now().strftime('%d %B %Y')}"), new_x="LMARGIN", new_y="NEXT")
    
    report_id = f"REV-{datetime.now().strftime('%Y%m%d')}-{os.urandom(2).hex().upper()}"
    pdf.cell(0, 5, f"Report ID: {report_id}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # Divider
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # === TOTAL LEAKAGE BANNER ===
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 22)
    banner_text = f"TOTAL LEAKAGE: NGN {total_leakage:,.2f}"
    pdf.cell(0, 12, clean_text(banner_text), align='C', fill=True, new_x="LMARGIN", new_y="NEXT")
    
    if total_revenue > 0:
        pct = (total_leakage / total_revenue) * 100
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(0, 5, f"{pct:.1f}% of audited revenue", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # Divider
    pdf.set_draw_color(229, 231, 235)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # === DETECTION BREAKDOWN ===
    pdf.section_title("DETECTION BREAKDOWN")
    
    for i, det in enumerate(detection_summaries, 1):
        if det['amount'] >= 1000000:
            color = (220, 38, 38)
        elif det['amount'] >= 100000:
            color = (234, 88, 12)
        elif det['amount'] > 0:
            color = (202, 138, 4)
        else:
            color = (22, 163, 74)
        
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, clean_text(f"{i}. {det['name']}"), new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*color)
        if det['amount'] > 0:
            pdf.cell(60, 4, f"  NGN {det['amount']:,.2f}")
        else:
            pdf.set_text_color(22, 163, 74)
            pdf.cell(60, 4, "  No issues detected")
        
        pdf.set_text_color(107, 114, 128)
        pdf.cell(0, 4, f"  {det['count']} flagged items")
        pdf.ln(4)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(0, 4, clean_text(f"  {det['detail']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    
    pdf.ln(2)
    
    # === TOP 3 ACTIONS ===
    pdf.section_title("TOP 3 IMMEDIATE ACTIONS")
    
    for i, action in enumerate(top_actions, 1):
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, clean_text(f"{i}. {action['action']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(0, 4, f"   Expected recovery: NGN {action['amount']:,.2f}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    
    pdf.ln(2)
    
    # === AI EXECUTIVE SUMMARY ===
    pdf.section_title("AI EXECUTIVE SUMMARY")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(0, 4, clean_text(ai_summary))
    pdf.ln(2)
    
    # === NEXT STEPS ===
    pdf.section_title("NEXT STEPS")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(55, 65, 81)
    pdf.cell(0, 4, "Schedule a 30-minute walkthrough call to review each finding in detail.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, "Contact: Abdullahi Abuzaid | RevAI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 4, "WhatsApp: +234 800 000 0000", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, "Email: abdullahi@revai.ng", new_x="LMARGIN", new_y="NEXT")
    
    # Generate filename
    if output_path is None:
        safe_name = company_name.replace(' ', '_').replace('/', '_')
        output_path = f"RevAI_Leakage_Report_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    pdf.output(output_path)
    return output_path
