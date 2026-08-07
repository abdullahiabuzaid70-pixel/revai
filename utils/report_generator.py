"""
PDF Report Generator - creates professional multi-section Leakage Report
Uses fpdf2 for PDF generation

Note: fpdf2 built-in fonts (Helvetica) use latin-1 encoding.
All special Unicode characters must be replaced with ASCII equivalents.
"""
from fpdf import FPDF
from datetime import datetime
import os


def clean_text(text):
    """Replace Unicode characters with ASCII-safe equivalents for fpdf2."""
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        '\u2014': '-',
        '\u2013': '-',
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u20a6': 'NGN',
        '\u2026': '...',
        '\u00a0': ' ',
        '\u2022': '*',
        '\u2192': '->',
        '\u2190': '<-',
        '\u2713': 'OK',
        '\u2717': 'X',
        '\u2714': 'OK',
        '\u2716': 'X',
    }
    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)
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
        footer_text = f"RevAI Leakage Report - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | CONFIDENTIAL | Findings are automated and should be reviewed by a qualified accountant."
        self.cell(0, 5, clean_text(footer_text), align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(15, 23, 42)
        self.cell(0, 7, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def colored_bar(self, r, g, b, text, text_color=(255, 255, 255), font_size=10, height=8):
        self.set_fill_color(r, g, b)
        self.set_text_color(*text_color)
        self.set_font('Helvetica', 'B', font_size)
        self.cell(0, height, clean_text(text), align='L', fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(15, 23, 42)

    def divider(self):
        self.set_draw_color(229, 231, 235)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)


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
    Generate a professional multi-section PDF Leakage Report.
    """
    pdf = LeakageReportPDF()

    # === PAGE 1: EXECUTIVE SUMMARY ===
    pdf.add_page()

    # Dark header bar
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 14, clean_text("RevAI - Financial Leakage Report"), align='C', fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Company info
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 5, clean_text(f"Prepared for: {company_name}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, clean_text(f"Audit Period: {audit_period}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, clean_text(f"Date: {datetime.now().strftime('%d %B %Y')}"), new_x="LMARGIN", new_y="NEXT")

    report_id = f"REV-{datetime.now().strftime('%Y%m%d')}-{os.urandom(2).hex().upper()}"
    pdf.cell(0, 5, f"Report ID: {report_id}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.divider()

    # Total leakage banner
    pdf.set_fill_color(220, 38, 38)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 26)
    pdf.cell(0, 16, clean_text(f"TOTAL LEAKAGE: NGN {total_leakage:,.2f}"), align='C', fill=True, new_x="LMARGIN", new_y="NEXT")

    if total_revenue > 0:
        pct = (total_leakage / total_revenue) * 100
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(220, 38, 38)
        pdf.cell(0, 6, f"{pct:.1f}% of audited revenue", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.divider()

    # Detection breakdown with colored severity bars
    pdf.section_title("DETECTION BREAKDOWN")

    for i, det in enumerate(detection_summaries, 1):
        amount = det['amount']
        if amount >= 1000000:
            color_r, color_g, color_b = 220, 38, 38
            label = "CRITICAL"
        elif amount >= 100000:
            color_r, color_g, color_b = 234, 88, 12
            label = "HIGH"
        elif amount > 0:
            color_r, color_g, color_b = 202, 138, 4
            label = "MEDIUM"
        else:
            color_r, color_g, color_b = 22, 163, 74
            label = "CLEAN"

        # Category name
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, clean_text(f"{i}. {det['name']}  [{label}]"), new_x="LMARGIN", new_y="NEXT")

        # Amount and count
        pdf.set_font('Helvetica', '', 9)
        if amount > 0:
            pdf.set_text_color(color_r, color_g, color_b)
            pdf.cell(80, 5, f"  NGN {amount:,.2f}")
        else:
            pdf.set_text_color(22, 163, 74)
            pdf.cell(80, 5, "  No issues detected")

        pdf.set_text_color(107, 114, 128)
        pdf.cell(0, 5, f"  {det['count']} flagged items")
        pdf.ln(5)

        # Detail
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(107, 114, 128)
        pdf.multi_cell(0, 4, clean_text(f"  {det.get('detail', '')}"))
        pdf.ln(2)

    pdf.ln(2)
    pdf.divider()

    # Top 3 actions
    pdf.section_title("TOP 3 IMMEDIATE ACTIONS")

    for i, action in enumerate(top_actions, 1):
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, clean_text(f"{i}. {action['action']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(0, 4, f"   Expected recovery: NGN {action['amount']:,.2f}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.ln(2)

    # AI summary
    pdf.section_title("AI EXECUTIVE SUMMARY")
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(0, 5, clean_text(ai_summary))
    pdf.ln(3)

    pdf.divider()

    # Next steps
    pdf.section_title("NEXT STEPS")
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(55, 65, 81)
    pdf.cell(0, 5, "1. Schedule a 30-minute walkthrough call to review each finding in detail.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "2. Prioritize recovery of duplicate payments (fastest recovery).", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "3. Initiate remittance of outstanding VAT/WHT to avoid compounding penalties.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "4. Investigate ghost vendors/employees and freeze associated payments.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Contact
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, "Contact: Abdullahi Abuzaid | RevAI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 4, "WhatsApp: +234 800 000 0000", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, "Email: hello@revai.ng", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Confidentiality notice
    pdf.set_fill_color(248, 250, 252)
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(0, 4, clean_text("CONFIDENTIAL: This report contains automated findings generated by RevAI. All findings should be independently verified by a qualified accountant or auditor before any action is taken. RevAI is not liable for decisions made based on these automated findings."))
    pdf.ln(3)

    # Disclaimer at bottom
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 4, "Generated by RevAI - AI Revenue & Fraud Detection for African Companies", align='C', new_x="LMARGIN", new_y="NEXT")

    # Generate filename
    if output_path is None:
        safe_name = company_name.replace(' ', '_').replace('/', '_')
        output_path = f"RevAI_Leakage_Report_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

    pdf.output(output_path)
    return output_path
