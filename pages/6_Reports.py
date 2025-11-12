from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def _table(c, x, y, rows, col_widths):
    """Very simple table renderer."""
    row_h = 18
    for r, row in enumerate(rows):
        yy = y - r*row_h
        for i, cell in enumerate(row):
            xx = x + sum(col_widths[:i])
            c.rect(xx, yy-row_h, col_widths[i], row_h, stroke=1, fill=0)
            c.setFont("Helvetica", 9)
            c.drawString(xx+4, yy-row_h+5, str(cell))

def make_weekly_pdf(kpis: dict, filename: str, highlights: list[str]=None, top_blocks: list[list]=None):
    """
    kpis: dict like {"Utilization":"67%","Booked":"1,234", ...}
    highlights: bullet points (strings)
    top_blocks: list of [weekday, hour, expected_util%, old_price, new_price, est_lift$]
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 760, "TeeIQ – Weekly Revenue Report")
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.grey)
    c.drawString(72, 742, datetime.now().strftime("%B %d, %Y"))
    c.setFillColor(colors.black)

    # KPIs
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 708, "Key Performance Indicators")
    y = 690
    c.setFont("Helvetica", 12)
    for k, v in kpis.items():
        c.drawString(72, y, f"• {k}: {v}")
        y -= 18

    # Highlights
    if highlights:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y-10, "Highlights & Notes")
        c.setFont("Helvetica", 12); y -= 30
        for h in highlights:
            c.drawString(72, y, f"• {h}"); y -= 16

    # Top low-fill blocks / price actions
    if top_blocks:
        c.setFont("Helvetica-Bold", 14); y -= 10
        c.drawString(72, y, "Top Actionable Price Blocks")
        y -= 22
        headers = ["Weekday","Hour","Exp Util","Old $","New $","Est Lift $"]
        rows = [headers] + top_blocks[:10]
        _table(c, 72, y, rows, [90, 60, 70, 60, 60, 80])
        y -= (len(rows)+1)*18

    c.showPage(); c.save()
    pdf = buf.getvalue(); buf.close()
    with open(filename, "wb") as f:
        f.write(pdf)
    return pdf
