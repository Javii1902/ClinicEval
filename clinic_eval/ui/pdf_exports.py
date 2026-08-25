from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import Legend

from .excel_exports import (
    build_comment_text,
    get_custom_comment,
    calculate_percentage,
    format_percentage,
    build_filter_summary_text,
    TEST_CHART_COLORS,
)
from ..validators import classify_answer

# Mirrors the fill colors in excel_exports.get_excel_styles() so the PDF
# reads as the same document as the Excel clinic sheet.
TITLE_FILL = colors.HexColor("#FFFFFF")
HEADER_FILL = colors.HexColor("#F2F2F2")
CRITERIA_FILL = colors.HexColor("#D9E1F2")
ITEM_FILL = colors.HexColor("#9999FF")
WHITE_FILL = colors.HexColor("#FFFFFF")
AMBER_FILL = colors.HexColor("#FFF2CC")
NO_COLOR = colors.HexColor("#ED7D31")
STL_COLOR = colors.HexColor("#C00000")
KPI_FILL = colors.HexColor("#DCE6F1")
COMPLIANT_COLOR = colors.HexColor("#4F81BD")
NON_COMPLIANT_COLOR = colors.HexColor("#C0504D")

DISPLAY_CATEGORY_MAP = {
    "CLIA CERTIFICATION": "CLIA Certification",
    "WORKFLOW & TESTING PROCEDURES": "Workflow and Testing",
    "OBSERVATION/INTERVIEW": "Observation/Interview",
}
ORDERED_CATEGORIES = [
    "CLIA CERTIFICATION",
    "WORKFLOW & TESTING PROCEDURES",
    "OBSERVATION/INTERVIEW",
]


def build_findings_chart(category_no_counts, category_stl_counts):
    categories = [DISPLAY_CATEGORY_MAP.get(c, c) for c in ORDERED_CATEGORIES]
    no_values = [category_no_counts.get(c, 0) for c in ORDERED_CATEGORIES]
    stl_values = [category_stl_counts.get(c, 0) for c in ORDERED_CATEGORIES]
    max_value = max([1] + no_values + stl_values)

    drawing = Drawing(480, 220)
    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 30
    chart.width = 320
    chart.height = 160
    chart.data = [no_values, stl_values]
    chart.categoryAxis.categoryNames = categories
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max_value
    chart.valueAxis.valueStep = max(1, round(max_value / 5) or 1)
    chart.bars[0].fillColor = NO_COLOR
    chart.bars[1].fillColor = STL_COLOR
    chart.barLabels.nudge = 7
    chart.barLabelFormat = lambda v: "" if v == 0 else str(int(v))
    chart.bars.strokeColor = None
    chart.groupSpacing = 15

    legend = Legend()
    legend.x = 390
    legend.y = 150
    legend.fontSize = 8
    legend.colorNamePairs = [(NO_COLOR, "No"), (STL_COLOR, "Stop the Line")]
    drawing.add(legend)
    drawing.add(chart)
    return drawing


def export_clinic_pdf(file_path, selected_detail, assessment_items, clinic_name=None):
    detail = dict(selected_detail or {})
    if clinic_name and not detail.get("clinic_name"):
        detail["clinic_name"] = clinic_name

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10)
    header_style = ParagraphStyle(
        "header", parent=styles["Normal"], fontSize=8, leading=10,
        alignment=1, fontName="Helvetica-Bold",
    )
    title_style = ParagraphStyle(
        "title", parent=styles["Title"], fontSize=16, alignment=1,
    )

    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(letter),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    story = []

    title_table = Table([[Paragraph("HMPO Clinic Point-of-Care Testing Checklist", title_style)]],
                         colWidths=[9.8 * inch])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TITLE_FILL),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 10))

    header_row = ["Criteria Description", "Item no.", "YES", "NO", "STL", "N/A", "COMMENTS", "CUSTOM COMMENTS"]
    table_data = [[Paragraph(h, header_style) for h in header_row]]

    yes_count = no_count = stl_count = na_count = 0
    category_no_counts = {}
    category_stl_counts = {}

    for item in assessment_items:
        number = item["number"]
        category = item["category"]
        answer = (detail.get(f"q{number}_answer") or "").strip()
        classification = classify_answer(answer)
        comment_text = build_comment_text(detail, number)
        custom_comment = get_custom_comment(detail, number)

        if classification == "yes":
            yes_count += 1
        elif classification == "no":
            no_count += 1
            category_no_counts[category] = category_no_counts.get(category, 0) + 1
        elif classification == "stl":
            stl_count += 1
            category_stl_counts[category] = category_stl_counts.get(category, 0) + 1
        else:
            na_count += 1

        answer_marks = ["x" if classification == option else "" for option in ("yes", "no", "stl", "na")]

        table_data.append([
            Paragraph(item["text"], cell_style),
            Paragraph(str(number), cell_style),
            Paragraph(answer_marks[0], cell_style),
            Paragraph(answer_marks[1], cell_style),
            Paragraph(answer_marks[2], cell_style),
            Paragraph(answer_marks[3], cell_style),
            Paragraph(comment_text or "", cell_style),
            Paragraph(custom_comment or "", cell_style),
        ])

    col_widths = [3.6 * inch, 0.4 * inch, 0.4 * inch, 0.4 * inch, 0.4 * inch, 0.4 * inch, 2.15 * inch, 2.15 * inch]
    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (5, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (0, -1), CRITERIA_FILL),
        ("BACKGROUND", (1, 1), (1, -1), ITEM_FILL),
        ("BACKGROUND", (2, 1), (5, -1), WHITE_FILL),
        ("BACKGROUND", (6, 1), (7, -1), WHITE_FILL),
    ]
    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)
    story.append(Spacer(1, 14))

    compliance = calculate_percentage(yes_count, no_count, stl_count)
    summary_header = ["Item:", "Out of", "Yes", "No", "STL", "N/A", "Compliance %"]
    summary_values = [
        yes_count,
        len(assessment_items) - na_count,
        yes_count,
        no_count,
        stl_count,
        na_count,
        format_percentage(compliance),
    ]
    summary_data = [
        [Paragraph(h, header_style) for h in summary_header],
        [Paragraph(str(v), cell_style) for v in summary_values],
    ]
    summary_table = Table(summary_data, colWidths=[1.1 * inch] * 7, hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AMBER_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    findings_title_style = ParagraphStyle("findings_title", parent=styles["Heading3"], fontSize=11)
    story.append(Paragraph("Point of Care Visit Results", findings_title_style))
    story.append(Spacer(1, 6))
    story.append(build_findings_chart(category_no_counts, category_stl_counts))
    story.append(Spacer(1, 10))

    detail_pairs = [
        ("Clinic:", detail.get("clinic_name") or ""),
        ("Date:", detail.get("assessment_date") or ""),
        ("Region:", detail.get("region") or ""),
        ("Specialty:", detail.get("specialty") or ""),
    ]
    detail_data = [
        [Paragraph(f"<b>{label}</b>", cell_style), Paragraph(str(value), cell_style)]
        for label, value in detail_pairs
    ]
    detail_table = Table(detail_data, colWidths=[1.0 * inch, 8.0 * inch], hAlign="LEFT")
    detail_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(detail_table)

    doc.build(story)


def build_kpi_table(dataset, overall_compliance, header_style):
    kpis = [
        ("Total Assessments", dataset["total_assessment_count"]),
        ("Total Clinics", len(dataset["clinic_rows"])),
        ("Overall Compliance", format_percentage(overall_compliance)),
        ("Compliant Clinics", dataset["compliant_clinics"]),
        ("Non-Compliant Clinics", dataset["non_compliant_clinics"]),
    ]
    value_style = ParagraphStyle(
        "kpi_value", fontSize=14, alignment=1, fontName="Helvetica-Bold", leading=18,
    )
    header_row = [Paragraph(label, header_style) for label, _ in kpis]
    value_row = [Paragraph(str(value), value_style) for _, value in kpis]

    table = Table([header_row, value_row], colWidths=[1.9 * inch] * 5, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), KPI_FILL),
        ("BACKGROUND", (0, 1), (-1, 1), WHITE_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 1), (-1, 1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    return table


def build_timeline_drawing(points):
    width, height = 500, 230
    drawing = Drawing(width, height)

    chart = LinePlot()
    chart.x = 55
    chart.y = 35
    chart.width = 400
    chart.height = 160
    xs = list(range(1, len(points) + 1))
    chart.data = [[(x, point["average"]) for x, point in zip(xs, points)]]
    chart.lines[0].strokeColor = colors.HexColor("#4E79A7")
    chart.lines[0].strokeWidth = 2

    chart.xValueAxis.valueMin = 1
    chart.xValueAxis.valueMax = max(xs) if len(xs) > 1 else 2
    chart.xValueAxis.valueSteps = xs
    chart.xValueAxis.labelTextFormat = lambda v: f"#{int(v)}"
    chart.xValueAxis.labels.fontSize = 8

    chart.yValueAxis.valueMin = 0
    chart.yValueAxis.valueMax = 100
    chart.yValueAxis.valueStep = 20
    chart.yValueAxis.labelTextFormat = "%d%%"
    chart.yValueAxis.labels.fontSize = 8

    drawing.add(chart)
    return drawing


def build_machines_bar_drawing(sorted_tests):
    row_height = 14
    top_pad, bottom_pad = 30, 30
    height = top_pad + bottom_pad + max(1, len(sorted_tests)) * row_height
    width = 700

    drawing = Drawing(width, height)
    chart = HorizontalBarChart()
    chart.x = 220
    chart.y = bottom_pad
    chart.width = width - 260
    chart.height = height - top_pad - bottom_pad
    chart.data = [[count for _, count in sorted_tests]]
    chart.categoryAxis.categoryNames = [name for name, _ in sorted_tests]
    chart.categoryAxis.labels.fontSize = 6
    chart.valueAxis.valueMin = 0
    chart.barLabels.fontSize = 6
    chart.barLabelFormat = "%d"
    chart.barLabels.nudge = 6
    chart.bars.strokeColor = None
    chart.groupSpacing = 4

    for i in range(len(sorted_tests)):
        color = colors.HexColor(f"#{TEST_CHART_COLORS[i % len(TEST_CHART_COLORS)]}")
        chart.bars[(0, i)].fillColor = color

    drawing.add(chart)
    return drawing


def build_compliance_pie_drawing(compliant, non_compliant):
    drawing = Drawing(320, 180)
    pie = Pie()
    pie.x = 60
    pie.y = 20
    pie.width = 140
    pie.height = 140
    pie.data = [compliant, non_compliant]
    pie.labels = [f"Compliant ({compliant})", f"Non-Compliant ({non_compliant})"]
    pie.slices[0].fillColor = COMPLIANT_COLOR
    pie.slices[1].fillColor = NON_COMPLIANT_COLOR
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1
    pie.simpleLabels = False
    pie.sideLabels = True
    drawing.add(pie)
    return drawing


def export_dashboard_pdf(
    file_path,
    dataset,
    questions,
    year_value="All",
    month_value="All",
    selected_clinics=None,
    selected_regions=None,
    selected_specialties=None,
    timeline_dataset=None,
):
    selected_clinics = selected_clinics or []
    selected_regions = selected_regions or []
    selected_specialties = selected_specialties or []

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10)
    header_style = ParagraphStyle(
        "header", parent=styles["Normal"], fontSize=8, leading=10,
        alignment=1, fontName="Helvetica-Bold",
    )
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=16, alignment=1)
    section_style = ParagraphStyle("section", parent=styles["Heading3"], fontSize=12)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(letter),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    story = []

    title_table = Table([[Paragraph("Compliance Dashboard", title_style)]], colWidths=[9.8 * inch])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TITLE_FILL),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 4))

    filter_text = build_filter_summary_text(
        year_value=year_value,
        month_value=month_value,
        clinics=selected_clinics if selected_clinics else "__ALL__",
        regions=selected_regions if selected_regions else "__ALL__",
        specialties=selected_specialties if selected_specialties else "__ALL__",
    )
    story.append(Paragraph(filter_text, cell_style))
    story.append(Spacer(1, 12))

    overall_compliance = calculate_percentage(
        dataset["overall_yes"], dataset["overall_no"], dataset["overall_stl"],
    )
    story.append(build_kpi_table(dataset, overall_compliance, header_style))
    story.append(Spacer(1, 16))

    timeline_points = [
        p for p in (timeline_dataset or {}).get("points", []) if p.get("average") is not None
    ]
    if timeline_points:
        story.append(Paragraph("Compliance Timeline (by Assessment #)", section_style))
        story.append(Spacer(1, 6))
        story.append(build_timeline_drawing(timeline_points))
        story.append(Spacer(1, 6))

        timeline_header = ["Assessment #", "Avg Compliance %", "Clinics"]
        timeline_data = [[Paragraph(h, header_style) for h in timeline_header]]
        for point in timeline_points:
            timeline_data.append([
                Paragraph(point["label"], cell_style),
                Paragraph(f"{point['average']:.2f}%", cell_style),
                Paragraph(str(point["clinic_count"]), cell_style),
            ])
        timeline_table = Table(timeline_data, colWidths=[1.8 * inch, 1.8 * inch, 1.2 * inch], hAlign="LEFT")
        timeline_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(timeline_table)
        story.append(PageBreak())

    sorted_tests = sorted(dataset.get("test_counts", {}).items(), key=lambda item: (-item[1], item[0].lower()))
    if sorted_tests:
        story.append(Paragraph("Machines by Test Across Clinics", section_style))
        story.append(Spacer(1, 6))
        story.append(build_machines_bar_drawing(sorted_tests))
        story.append(PageBreak())

    story.append(Paragraph("Clinic Compliance Status", section_style))
    story.append(Spacer(1, 6))
    story.append(build_compliance_pie_drawing(dataset["compliant_clinics"], dataset["non_compliant_clinics"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Clinic Compliance Table", section_style))
    story.append(Spacer(1, 6))
    clinic_header = ["Clinic Name", "Region", "Specialty", "Compliance %", "Yes", "No", "STL", "NA"]
    clinic_data = [[Paragraph(h, header_style) for h in clinic_header]]
    for clinic_name, region, specialty, compliance, yes_count, no_count, stl_count, na_count, _source_row in dataset["clinic_rows"]:
        clinic_data.append([
            Paragraph(clinic_name or "", cell_style),
            Paragraph(region or "", cell_style),
            Paragraph(specialty or "", cell_style),
            Paragraph(format_percentage(compliance), cell_style),
            Paragraph(str(yes_count), cell_style),
            Paragraph(str(no_count), cell_style),
            Paragraph(str(stl_count), cell_style),
            Paragraph(str(na_count), cell_style),
        ])
    clinic_col_widths = [2.2 * inch, 1.3 * inch, 1.6 * inch, 1.1 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch]
    clinic_table = Table(clinic_data, colWidths=clinic_col_widths, repeatRows=1, hAlign="LEFT")
    clinic_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(clinic_table)
    story.append(PageBreak())

    story.append(Paragraph("Question Compliance Table", section_style))
    story.append(Spacer(1, 6))
    question_header = ["Question", "Compliance %", "Yes", "No", "STL", "NA"]
    question_data = [[Paragraph(h, header_style) for h in question_header]]
    for idx, question in enumerate(questions):
        stats = dataset["question_stats"][idx]
        compliance = calculate_percentage(stats["yes"], stats["no"], stats["stl"])
        question_data.append([
            Paragraph(question, cell_style),
            Paragraph(format_percentage(compliance), cell_style),
            Paragraph(str(stats["yes"]), cell_style),
            Paragraph(str(stats["no"]), cell_style),
            Paragraph(str(stats["stl"]), cell_style),
            Paragraph(str(stats["na"]), cell_style),
        ])
    question_col_widths = [5.5 * inch, 1.2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch]
    question_table = Table(question_data, colWidths=question_col_widths, repeatRows=1, hAlign="LEFT")
    question_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(question_table)

    doc.build(story)
