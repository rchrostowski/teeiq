from datetime import datetime, timedelta
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

def _png_from_matplotlib(fig, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf

def _draw_table(c, x, y, rows, col_widths, header_fill=colors.HexColor("#eaf2ec")):
    row_h = 18
    for r, row in enumerate(rows):
        yy = y - r*row_h
        for i, cell in enumerate(row):
            xx = x + sum(col_widths[:i])
            if r == 0:  # header
                c.setFillColor(header_fill); c.rect(xx, yy-row_h, col_widths[i], row_h, stroke=0, fill=1)
                c.setFillColor(colors.black)
                c.rect(xx, yy-row_h, col_widths[i], row_h, stroke=1, fill=0)
                c.setFont("Helvetica-Bold", 9)
            else:
                c.rect(xx, yy-row_h, col_widths[i], row_h, stroke=1, fill=0)
                c.setFont("Helvetica", 9)
            c.drawString(xx+4, yy-row_h+5, str(cell))

def make_advanced_weekly_pdf(
    filename: str,
    kpis: dict,
    trend_df: pd.DataFrame,
    heatmap: np.ndarray,
    heatmap_ylabels: list,
    heatmap_xlabels: list,
    top_actions: list[list],
    notes: list[str] = None,
):
    c = canvas.Canvas(filename, pagesize=letter)

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 760, "TeeIQ – Weekly Revenue Report")
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.grey)
    c.drawString(72, 742, datetime.now().strftime("%B %d, %Y"))
    c.setFillColor(colors.black)

    # KPIs
    c.setFont("Helvetica-Bold", 14); c.drawString(72, 708, "Key Performance Indicators")
    y = 690; c.setFont("Helvetica", 12)
    for k, v in kpis.items():
        c.drawString(72, y, f"• {k}: {v}"); y -= 18

    # Trend chart
    fig1, ax1 = plt.subplots(figsize=(6, 2))
    ax1.plot(trend_df["date"], trend_df["util"]*100, marker="o")
    ax1.set_ylabel("Utilization (%)"); ax1.set_xlabel("Date")
    ax1.grid(True, alpha=0.3)
    img1 = _png_from_matplotlib(fig1); plt.close(fig1)
    c.drawImage(ImageReader(img1), 72, 520, width=460, height=150, preserveAspectRatio=True, mask='auto')

    # Heatmap chart
    fig2, ax2 = plt.subplots(figsize=(6, 2))
    im = ax2.imshow(heatmap, aspect="auto")
    ax2.set_yticks(range(len(heatmap_ylabels))); ax2.set_yticklabels(heatmap_ylabels)
    ax2.set_xticks(range(len(heatmap_xlabels))); ax2.set_xticklabels(heatmap_xlabels, rotation=0)
    ax2.set_title("Utilization Heatmap"); fig2.colorbar(im, ax=ax2, fraction=0.02, pad=0.02)
    img2 = _png_from_matplotlib(fig2); plt.close(fig2)
    c.drawImage(ImageReader(img2), 72, 350, width=460, height=140, preserveAspectRatio=True, mask='auto')

    # Notes
    if notes:
        c.setFont("Helvetica-Bold", 14); c.drawString(72, 320, "Highlights & Notes")
        c.setFont("Helvetica", 12); yy = 300
        for n in notes:
            c.drawString(72, yy, f"• {n}"); yy -= 16

    # Top Actions
    if top_actions:
        c.setFont("Helvetica-Bold", 14); c.drawString(72, 240, "Top Actionable Price Blocks")
        headers = ["Weekday","Hour","Exp Util","Avg $","New $","Est Lift $"]
        rows = [headers] + top_actions[:10]
        _draw_table(c, 72, 220, rows, [90,60,70,60,60,80])

    c.showPage(); c.save()

