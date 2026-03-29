"""
pdf_generator.py
Genera un PDF con la lista dei match per il Learning Agreement.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import datetime


# Palette colori
BLUE_DARK  = colors.HexColor("#1e3a5f")
BLUE_MID   = colors.HexColor("#2563eb")
BLUE_LIGHT = colors.HexColor("#dbeafe")
GOLD       = colors.HexColor("#f59e0b")
GRAY_LIGHT = colors.HexColor("#f1f5f9")
GRAY_TEXT  = colors.HexColor("#475569")
WHITE      = colors.white


def generate_pdf(matches: list[dict], university_home: str,
                 university_abroad: str, output_path: str) -> str:
    """
    Genera un PDF con i match trovati.
    Restituisce il path del file creato.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Titolo ──────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        fontSize=22,
        textColor=BLUE_DARK,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontSize=11,
        textColor=GRAY_TEXT,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    label_style = ParagraphStyle(
        "Label",
        fontSize=9,
        textColor=GRAY_TEXT,
        fontName="Helvetica",
    )
    body_style = ParagraphStyle(
        "Body",
        fontSize=9,
        textColor=colors.black,
        fontName="Helvetica",
        leading=13,
    )
    section_style = ParagraphStyle(
        "Section",
        fontSize=11,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        backColor=BLUE_DARK,
        leftIndent=6,
        spaceAfter=0,
        spaceBefore=0,
    )

    story.append(Paragraph("🎓 Erasmus Learning Agreement", title_style))
    story.append(Paragraph("Proposta di Corsi Sovrapponibili", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=12))

    # ── Info header ──────────────────────────────────────────────────────────
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    info_data = [
        [Paragraph("<b>Università di Casa</b>", label_style),
         Paragraph(university_home, body_style)],
        [Paragraph("<b>Università Estera</b>", label_style),
         Paragraph(university_abroad, body_style)],
        [Paragraph("<b>Data generazione</b>", label_style),
         Paragraph(now, body_style)],
        [Paragraph("<b>Totale match trovati</b>", label_style),
         Paragraph(str(len(matches)), body_style)],
    ]
    info_table = Table(info_data, colWidths=[4.5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_LIGHT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [GRAY_LIGHT, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 18))

    # ── Avviso ───────────────────────────────────────────────────────────────
    warning_style = ParagraphStyle(
        "Warning",
        fontSize=8,
        textColor=colors.HexColor("#92400e"),
        fontName="Helvetica-Oblique",
        backColor=colors.HexColor("#fef3c7"),
        borderColor=GOLD,
        borderWidth=0.5,
        borderPadding=6,
        leading=12,
    )
    story.append(Paragraph(
        "⚠️  Questa è una proposta generata da intelligenza artificiale. "
        "Verificare sempre i match con il proprio coordinatore Erasmus e con "
        "i responsabili dei corsi prima di inviare il Learning Agreement ufficiale.",
        warning_style
    ))
    story.append(Spacer(1, 18))

    # ── Tabella match ────────────────────────────────────────────────────────
    if not matches:
        story.append(Paragraph(
            "Nessun match trovato con la soglia di similarità impostata.",
            body_style
        ))
    else:
        # Intestazione
        header_style = ParagraphStyle(
            "Header", fontSize=8, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER
        )
        cell_style = ParagraphStyle(
            "Cell", fontSize=8, fontName="Helvetica", leading=11
        )
        small_center = ParagraphStyle(
            "SmallCenter", fontSize=8, fontName="Helvetica",
            alignment=TA_CENTER, leading=11
        )
        moti_style = ParagraphStyle(
            "Moti", fontSize=7.5, fontName="Helvetica-Oblique",
            textColor=GRAY_TEXT, leading=11
        )

        col_widths = [4.5*cm, 4.5*cm, 1.5*cm, 1.5*cm, 1.8*cm, 3.0*cm]
        table_data = [[
            Paragraph("Corso (casa)", header_style),
            Paragraph("Corso (estero)", header_style),
            Paragraph("CFU casa", header_style),
            Paragraph("CFU estero", header_style),
            Paragraph("Match %", header_style),
            Paragraph("Motivazione", header_style),
        ]]

        for i, m in enumerate(matches):
            sim = m.get("similarita", 0)
            # Colore badge similarità
            if sim >= 80:
                badge_color = colors.HexColor("#16a34a")
            elif sim >= 65:
                badge_color = colors.HexColor("#ca8a04")
            else:
                badge_color = colors.HexColor("#dc2626")

            badge_style = ParagraphStyle(
                f"Badge{i}", fontSize=9, fontName="Helvetica-Bold",
                textColor=badge_color, alignment=TA_CENTER
            )

            table_data.append([
                Paragraph(m.get("corso_casa", ""), cell_style),
                Paragraph(m.get("corso_estero", ""), cell_style),
                Paragraph(str(m.get("crediti_casa", 0)), small_center),
                Paragraph(str(m.get("crediti_estero", 0)), small_center),
                Paragraph(f"{sim}%", badge_style),
                Paragraph(m.get("motivazione", ""), moti_style),
            ])

        match_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        row_count = len(table_data)
        match_table.setStyle(TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            # Righe alternate
            *[("BACKGROUND", (0, i), (-1, i), BLUE_LIGHT if i % 2 == 0 else WHITE)
              for i in range(1, row_count)],
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ]))
        story.append(match_table)

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    footer_style = ParagraphStyle(
        "Footer", fontSize=7.5, textColor=GRAY_TEXT,
        fontName="Helvetica", alignment=TA_CENTER
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Generato da Erasmus LA Helper · I match sono suggerimenti automatici, non approvazioni ufficiali",
        footer_style
    ))

    doc.build(story)
    return output_path
