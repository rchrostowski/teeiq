from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def make_weekly_pdf(metrics: dict, filename: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 740, "TeeIQ – Weekly Revenue Report")
    c.setFont("Helvetica", 12)
    y = 700
    for k, v in metrics.items():
        c.drawString(72, y, f"{k}: {v}")
        y -= 20
    c.showPage(); c.save()
    pdf = buf.getvalue(); buf.close()
    with open(filename, "wb") as f:
        f.write(pdf)
    return pdf
