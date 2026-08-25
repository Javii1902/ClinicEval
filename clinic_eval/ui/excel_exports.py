import math

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.utils import get_column_letter

from ..validators import classify_answer

DEFAULT_ROW_HEIGHT_PT = 15

TEST_CHART_COLORS = [
    "4E79A7", "F28E2B", "E15759", "76B7B2", "59A14F",
    "EDC948", "B07AA1", "FF9DA7", "9C755F", "BAB0AC",
    "1F77B4", "FF7F0E",
]


def estimate_chart_row_span(height_cm):
    height_px = height_cm * 96 / 2.54
    row_height_px = DEFAULT_ROW_HEIGHT_PT * 96 / 72
    return math.ceil(height_px / row_height_px)


def determine_legend_columns(count):
    if count <= 8:
        return 2
    if count <= 16:
        return 3
    return 4


def sanitize_sheet_name(name, fallback="Sheet"):
    invalid = ["\\", "/", "*", "[", "]", ":", "?"]
    clean = (name or "").strip() or fallback
    for ch in invalid:
        clean = clean.replace(ch, "-")
    return clean[:31]


def calculate_percentage(yes_count, no_count, stl_count=0):
    denominator = yes_count + no_count + stl_count
    if denominator == 0:
        return None
    return (yes_count / denominator) * 100


def format_percentage(percentage):
    if percentage is None:
        return "N/A"
    return f"{percentage:.2f}%"


def build_filter_summary_text(year_value, month_value, clinics, regions, specialties):
    def fmt(label, values, all_label):
        if not values:
            return f"{label}: None"
        return f"{label}: {all_label if values == '__ALL__' else ', '.join(values)}"

    year_text = f"Year: {year_value or 'All'}"
    month_text = f"Month: {month_value or 'All'}"
    clinic_text = fmt("Clinics", clinics, "All Clinics")
    region_text = fmt("Regions", regions, "All Regions")
    specialty_text = fmt("Specialties", specialties, "All Specialties")
    return " | ".join([year_text, month_text, clinic_text, region_text, specialty_text])


def estimate_row_height(values, base_height=18, chars_per_line=18, min_lines=1):
    max_lines = min_lines
    for value in values:
        if value is None:
            continue
        text = str(value)
        explicit_lines = text.count("\n") + 1
        wrapped_lines = max(
            1,
            (len(text) // chars_per_line) + (1 if len(text) % chars_per_line else 0),
        )
        max_lines = max(max_lines, explicit_lines, wrapped_lines)
    return max(base_height, max_lines * 15)


def apply_wrapped_alignment(cell, horizontal="left", vertical="top"):
    cell.alignment = Alignment(horizontal=horizontal, vertical=vertical, wrap_text=True)


def get_excel_styles():
    thin = Side(style="thin", color="000000")
    medium = Side(style="medium", color="000000")
    return {
        "thin_border": Border(left=thin, right=thin, top=thin, bottom=thin),
        "medium_border": Border(left=medium, right=medium, top=medium, bottom=medium),
        "title_font": Font(bold=True, size=14),
        "section_font": Font(bold=True, size=11),
        "header_font": Font(bold=True, size=10),
        "normal_font": Font(size=10),
        "kpi_font": Font(bold=True, size=16),
        "title_fill": PatternFill(
            fill_type="solid", start_color="FFFFFF", end_color="FFFFFF"
        ),
        "header_fill": PatternFill(
            fill_type="solid", start_color="F2F2F2", end_color="F2F2F2"
        ),
        "criteria_fill": PatternFill(
            fill_type="solid", start_color="D9E1F2", end_color="D9E1F2"
        ),
        "item_fill": PatternFill(
            fill_type="solid", start_color="9999FF", end_color="9999FF"
        ),
        "white_fill": PatternFill(
            fill_type="solid", start_color="FFFFFF", end_color="FFFFFF"
        ),
        "kpi_fill": PatternFill(
            fill_type="solid", start_color="DCE6F1", end_color="DCE6F1"
        ),
        "accent_fill": PatternFill(
            fill_type="solid", start_color="B4C6E7", end_color="B4C6E7"
        ),
        "green_fill": PatternFill(
            fill_type="solid", start_color="E2F0D9", end_color="E2F0D9"
        ),
        "red_fill": PatternFill(
            fill_type="solid", start_color="FCE4D6", end_color="FCE4D6"
        ),
        "amber_fill": PatternFill(
            fill_type="solid", start_color="FFF2CC", end_color="FFF2CC"
        ),
    }


def build_comment_text(selected_detail, number):
    # The "Comments" column shows the template comment only. Manual
    # Comments are the Custom Comments and are shown in their own column
    # (see get_custom_comment) - they should not be duplicated in here.
    template_value = (selected_detail.get(f"q{number}_template_comment") or "").strip()
    if template_value:
        return template_value

    # Fallback for very old records saved before comments were split into
    # separate template/manual/custom columns.
    manual_value = (selected_detail.get(f"q{number}_manual_comment") or "").strip()
    custom_value = (selected_detail.get(f"q{number}_custom_comment") or "").strip()
    if not manual_value and not custom_value:
        legacy_value = (selected_detail.get(f"q{number}_comment") or "").strip()
        if legacy_value:
            return legacy_value

    return ""


def get_custom_comment(selected_detail, number):
    for key in (
        f"q{number}_custom_comment",
        f"q{number}_manual_comment",
        f"q{number}_comment_custom",
        f"q{number}_customcomments",
        f"q{number}_custom_comments",
    ):
        value = (selected_detail.get(key) or "").strip()
        if value:
            return value
    return ""


def write_dashboard_sheet(
    ws,
    dataset,
    questions,
    year_value="All",
    month_value="All",
    selected_clinics=None,
    selected_regions=None,
    selected_specialties=None,
    timeline_dataset=None,
):
    styles = get_excel_styles()
    selected_clinics = selected_clinics or []
    selected_regions = selected_regions or []
    selected_specialties = selected_specialties or []

    overall_compliance = calculate_percentage(
        dataset["overall_yes"],
        dataset["overall_no"],
        dataset["overall_stl"],
    )

    ws.title = "Dashboard"
    ws.sheet_view.showGridLines = False

    widths = {
        "A": 16,
        "B": 16,
        "C": 16,
        "D": 16,
        "E": 28,
        "F": 12,
        "G": 16,
        "H": 16,
        "I": 16,
        "J": 14,
        "K": 14,
        "L": 14,
        "M": 14,
        "N": 14,
        "O": 14,
        "P": 14,
        "Q": 14,
        "R": 14,
        "S": 14,
        "T": 14,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 34
    for r in range(4, 7):
        ws.row_dimensions[r].height = 24

    ws.merge_cells("A1:H1")
    ws["A1"] = "Compliance Dashboard"
    ws["A1"].font = styles["title_font"]
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws["A1"].border = styles["medium_border"]

    ws.merge_cells("A2:O2")
    ws["A2"] = build_filter_summary_text(
        year_value=year_value,
        month_value=month_value,
        clinics=selected_clinics if selected_clinics else "__ALL__",
        regions=selected_regions if selected_regions else "__ALL__",
        specialties=selected_specialties if selected_specialties else "__ALL__",
    )
    ws["A2"].font = styles["normal_font"]
    ws["A2"].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws["A2"].border = styles["thin_border"]

    kpis = [
        ("Total Assessments", dataset["total_assessment_count"]),
        ("Total Clinics", len(dataset["clinic_rows"])),
        ("Overall Compliance", format_percentage(overall_compliance)),
        ("Compliant Clinics", dataset["compliant_clinics"]),
        ("Non-Compliant Clinics", dataset["non_compliant_clinics"]),
    ]

    start_col = 1
    for i, (label, value) in enumerate(kpis):
        col = start_col + (i * 3)
        ws.merge_cells(start_row=4, start_column=col, end_row=4, end_column=col + 1)
        ws.merge_cells(start_row=5, start_column=col, end_row=6, end_column=col + 1)

        label_cell = ws.cell(row=4, column=col, value=label)
        label_cell.font = styles["header_font"]
        label_cell.fill = styles["kpi_fill"]
        label_cell.alignment = Alignment(horizontal="center", vertical="center")
        label_cell.border = styles["medium_border"]

        value_cell = ws.cell(row=5, column=col, value=value)
        value_cell.font = styles["kpi_font"]
        value_cell.fill = styles["white_fill"]
        value_cell.alignment = Alignment(horizontal="center", vertical="center")
        value_cell.border = styles["medium_border"]

        for r in range(5, 7):
            for c in range(col, col + 2):
                ws.cell(row=r, column=c).border = styles["medium_border"]

    # Timeline section sits right under the KPI row, above the tables and
    # the bar/pie charts that follow them.
    charts_start_row = 8
    timeline_points = [
        p for p in (timeline_dataset or {}).get("points", []) if p.get("average") is not None
    ]

    if timeline_points:
        section_row = charts_start_row
        ws.merge_cells(start_row=section_row, start_column=1, end_row=section_row, end_column=8)
        title_cell = ws.cell(row=section_row, column=1, value="Compliance Timeline")
        title_cell.font = styles["section_font"]
        title_cell.alignment = Alignment(horizontal="left", vertical="center")
        title_cell.border = styles["medium_border"]

        timeline_table_row = section_row + 1
        timeline_headers = ["Assessment #", "Avg Compliance %", "Clinics"]
        for col_idx, header in enumerate(timeline_headers, start=1):
            cell = ws.cell(row=timeline_table_row, column=col_idx, value=header)
            cell.font = styles["header_font"]
            cell.fill = styles["header_fill"]
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = styles["medium_border"]

        for i, point in enumerate(timeline_points, start=1):
            row = timeline_table_row + i
            values = [point["label"], round(point["average"], 2), point["clinic_count"]]
            for col_idx, value in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = styles["normal_font"]
                cell.border = styles["thin_border"]
                cell.alignment = Alignment(horizontal="center", vertical="center")

        timeline_chart = LineChart()
        timeline_chart.title = "Compliance Timeline (by Assessment #)"
        timeline_chart.y_axis.title = "Compliance %"
        timeline_chart.x_axis.title = "Assessment #"
        timeline_chart.height = 7.8
        timeline_chart.width = 17
        timeline_chart.legend = None

        timeline_data = Reference(
            ws,
            min_col=2,
            min_row=timeline_table_row,
            max_row=timeline_table_row + len(timeline_points),
        )
        timeline_cats = Reference(
            ws,
            min_col=1,
            min_row=timeline_table_row + 1,
            max_row=timeline_table_row + len(timeline_points),
        )
        timeline_chart.add_data(timeline_data, titles_from_data=True)
        timeline_chart.set_categories(timeline_cats)

        if timeline_chart.series:
            series = timeline_chart.series[0]
            series.marker.symbol = "circle"
            series.graphicalProperties.line.solidFill = "999999"
            series.smooth = False

        timeline_chart.dLbls = DataLabelList()
        timeline_chart.dLbls.showVal = True
        timeline_chart.dLbls.showLegendKey = False
        timeline_chart.dLbls.showCatName = False

        ws.add_chart(timeline_chart, f"E{timeline_table_row}")

        # Detail matrix: each included clinic's own compliance at each
        # assessment number, matching the breakdown shown in the app's
        # timeline tooltip (blank where a clinic never reached that visit).
        clinic_names = sorted(
            {c["clinic_name"] for point in timeline_points for c in point["clinics"]},
            key=lambda name: (name or "").lower(),
        )
        clinic_matrix = {name: {} for name in clinic_names}
        for seq_index, point in enumerate(timeline_points, start=1):
            for c in point["clinics"]:
                clinic_matrix[c["clinic_name"]][seq_index] = {
                    "compliance": c["compliance"],
                    "date": c["date"],
                }

        chart_bottom_row = timeline_table_row + estimate_chart_row_span(timeline_chart.height)
        table_bottom_row = timeline_table_row + len(timeline_points)
        detail_row = max(chart_bottom_row, table_bottom_row) + 2

        ws.merge_cells(start_row=detail_row, start_column=1, end_row=detail_row, end_column=8)
        detail_title_cell = ws.cell(row=detail_row, column=1, value="Timeline Detail by Clinic")
        detail_title_cell.font = styles["section_font"]
        detail_title_cell.alignment = Alignment(horizontal="left", vertical="center")
        detail_title_cell.border = styles["medium_border"]

        detail_header_row = detail_row + 1
        detail_headers = ["Clinic"] + [f"Assessment {i}" for i in range(1, len(timeline_points) + 1)]
        for col_idx, header in enumerate(detail_headers, start=1):
            cell = ws.cell(row=detail_header_row, column=col_idx, value=header)
            cell.font = styles["header_font"]
            cell.fill = styles["header_fill"]
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = styles["medium_border"]

        # Wide enough for "100.00% (2026-01-01)" without truncating - the
        # matrix columns start beyond the "widths" dict set up earlier, so
        # they'd otherwise be left at Excel's default (too narrow) width.
        for col_idx in range(2, 2 + len(timeline_points)):
            ws.column_dimensions[get_column_letter(col_idx)].width = 22

        for row_offset, clinic_name in enumerate(clinic_names, start=1):
            row = detail_header_row + row_offset
            name_cell = ws.cell(row=row, column=1, value=clinic_name)
            name_cell.font = styles["normal_font"]
            name_cell.border = styles["thin_border"]
            apply_wrapped_alignment(name_cell, horizontal="left", vertical="center")

            for seq_index in range(1, len(timeline_points) + 1):
                entry = clinic_matrix[clinic_name].get(seq_index)
                if entry is not None:
                    cell_value = f"{format_percentage(entry['compliance'])} ({entry['date']})"
                else:
                    cell_value = ""

                cell = ws.cell(row=row, column=1 + seq_index, value=cell_value)
                cell.font = styles["normal_font"]
                cell.border = styles["thin_border"]
                cell.alignment = Alignment(horizontal="center", vertical="center")

        charts_start_row = detail_header_row + len(clinic_names) + 2

    # Tables come first, both charts stacked below them afterward - matching
    # the clinic checklist sheet's "table first, chart below" layout rather
    # than floating charts beside the tables.
    clinic_table_row = charts_start_row
    ws.merge_cells(
        start_row=clinic_table_row,
        start_column=1,
        end_row=clinic_table_row,
        end_column=8,
    )
    ws.cell(row=clinic_table_row, column=1, value="Clinic Compliance Table")
    ws.cell(row=clinic_table_row, column=1).font = styles["section_font"]
    ws.cell(row=clinic_table_row, column=1).alignment = Alignment(
        horizontal="left", vertical="center"
    )
    ws.cell(row=clinic_table_row, column=1).border = styles["medium_border"]

    clinic_headers = [
        "Clinic Name",
        "Region",
        "Specialty",
        "Compliance %",
        "Yes",
        "No",
        "STL",
        "NA",
    ]
    for col_idx, header in enumerate(clinic_headers, start=1):
        cell = ws.cell(row=clinic_table_row + 1, column=col_idx, value=header)
        cell.font = styles["header_font"]
        cell.fill = styles["header_fill"]
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = styles["medium_border"]

    current_row = clinic_table_row + 2
    for (
        clinic_name,
        region,
        specialty,
        compliance,
        yes_count,
        no_count,
        stl_count,
        na_count,
        _source_row,
    ) in dataset["clinic_rows"]:
        values = [
            clinic_name,
            region,
            specialty,
            format_percentage(compliance),
            yes_count,
            no_count,
            stl_count,
            na_count,
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=current_row, column=col_idx, value=value)
            cell.font = styles["normal_font"]
            cell.border = styles["thin_border"]
            if col_idx in (1, 2, 3):
                apply_wrapped_alignment(cell, horizontal="left", vertical="top")
            else:
                apply_wrapped_alignment(cell, horizontal="center", vertical="center")
        ws.row_dimensions[current_row].height = estimate_row_height(
            [clinic_name, region, specialty],
            base_height=18,
            chars_per_line=16,
        )
        current_row += 1

    question_table_row = current_row + 2
    ws.merge_cells(
        start_row=question_table_row,
        start_column=1,
        end_row=question_table_row,
        end_column=6,
    )
    ws.cell(row=question_table_row, column=1, value="Question Compliance Table")
    ws.cell(row=question_table_row, column=1).font = styles["section_font"]
    ws.cell(row=question_table_row, column=1).alignment = Alignment(
            horizontal="left", vertical="center"
    )
    ws.cell(row=question_table_row, column=1).border = styles["medium_border"]

    question_headers = ["Question", "Compliance %", "Yes", "No", "STL", "NA"]
    for col_idx, header in enumerate(question_headers, start=1):
        cell = ws.cell(row=question_table_row + 1, column=col_idx, value=header)
        cell.font = styles["header_font"]
        cell.fill = styles["header_fill"]
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = styles["medium_border"]

    current_row = question_table_row + 2
    for idx, question in enumerate(questions):
        stats = dataset["question_stats"][idx]
        compliance = calculate_percentage(stats["yes"], stats["no"], stats["stl"])
        values = [
            question,
            format_percentage(compliance),
            stats["yes"],
            stats["no"],
            stats["stl"],
            stats["na"],
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=current_row, column=col_idx, value=value)
            cell.font = styles["normal_font"]
            cell.border = styles["thin_border"]
            if col_idx == 1:
                apply_wrapped_alignment(cell, horizontal="left", vertical="top")
            else:
                apply_wrapped_alignment(cell, horizontal="center", vertical="center")
        ws.row_dimensions[current_row].height = estimate_row_height(
            [question], base_height=20, chars_per_line=40
        )
        current_row += 1

    # Compact numeric backing table for the bar chart (index/count only -
    # test names live in the legend below the chart, matching the app's own
    # dashboard tab: numbered bars on top, a color-keyed legend underneath).
    # It's placed off in unused columns, out of the normal viewing area, but
    # deliberately left *unhidden* - marking these columns hidden and relying
    # on plotVisOnly=False previously produced a blank chart in Excel Online.
    test_start_row = current_row + 2
    data_col = 30
    count_col = 31
    ws.cell(row=test_start_row, column=data_col, value="#")
    ws.cell(row=test_start_row, column=count_col, value="Count")

    sorted_tests = sorted(
        dataset["test_counts"].items(),
        key=lambda item: (-item[1], item[0].lower()),
    )
    for idx, (test_name, count) in enumerate(sorted_tests, start=1):
        row = test_start_row + idx
        index_cell = ws.cell(row=row, column=data_col, value=idx)
        count_cell = ws.cell(row=row, column=count_col, value=count)
        index_cell.alignment = Alignment(horizontal="center", vertical="center")
        count_cell.alignment = Alignment(horizontal="center", vertical="center")

    if sorted_tests:
        bar = BarChart()
        bar.type = "bar"
        bar.style = 2
        bar.title = "Machines by Test Across Clinics"
        bar.y_axis.title = "Count"
        # The color legend below the chart already identifies each bar, so
        # the "#" category axis (and its numbers running down the chart) is
        # redundant - drop it entirely. Also correct the value axis position
        # (openpyxl defaults both axes to the same side, which Excel renders
        # as a stray extra "Count" bar at the bottom of the chart).
        bar.x_axis.delete = True
        bar.y_axis.axPos = "b"
        bar.height = max(10, min(18, len(sorted_tests) * 0.55))
        bar.width = 17
        bar.gapWidth = 50
        bar.overlap = 0
        bar.legend = None

        # Single series driven directly by the visible index/count table -
        # a plain category/value bar chart renders reliably everywhere,
        # unlike the previous one-series-per-test construction, which
        # produced a blank chart in Excel Online.
        bar_data = Reference(
            ws,
            min_col=count_col,
            min_row=test_start_row,
            max_row=test_start_row + len(sorted_tests),
        )
        bar_cats = Reference(
            ws,
            min_col=data_col,
            min_row=test_start_row + 1,
            max_row=test_start_row + len(sorted_tests),
        )
        bar.add_data(bar_data, titles_from_data=True)
        bar.set_categories(bar_cats)

        if len(bar.series) > 0:
            series = bar.series[0]
            series.data_points = [DataPoint(idx=i) for i in range(len(sorted_tests))]
            for i, data_point in enumerate(series.data_points):
                color = TEST_CHART_COLORS[i % len(TEST_CHART_COLORS)]
                data_point.graphicalProperties.solidFill = color
                data_point.graphicalProperties.line.solidFill = color

        bar.dLbls = DataLabelList()
        bar.dLbls.showVal = True
        bar.dLbls.showLegendKey = False
        bar.dLbls.showCatName = False
        bar.dLbls.showSerName = False

        # Anchored below the tables (not beside the now off-screen index/
        # count backing table), with the pie chart stacked beneath it.
        bar_anchor_row = test_start_row
        ws.add_chart(bar, f"A{bar_anchor_row}")
        chart_bottom_row = bar_anchor_row + estimate_chart_row_span(bar.height)

        # Legend: a swatch + "# - Test Name (Count)" entry per test, laid
        # out across multiple columns below the chart - mirroring the
        # dashboard tab's own bar chart legend.
        legend_columns = determine_legend_columns(len(sorted_tests))
        legend_start_row = chart_bottom_row + 2
        group_width = 3

        for i, (test_name, count) in enumerate(sorted_tests):
            col_group = i % legend_columns
            row_offset = i // legend_columns
            row = legend_start_row + row_offset
            swatch_col = 1 + col_group * group_width
            label_col_start = swatch_col + 1
            label_col_end = swatch_col + group_width - 1
            color = TEST_CHART_COLORS[i % len(TEST_CHART_COLORS)]

            swatch_cell = ws.cell(row=row, column=swatch_col, value="")
            swatch_cell.fill = PatternFill(
                fill_type="solid", start_color=color, end_color=color
            )
            swatch_cell.border = styles["thin_border"]

            ws.merge_cells(
                start_row=row,
                start_column=label_col_start,
                end_row=row,
                end_column=label_col_end,
            )
            label_cell = ws.cell(
                row=row,
                column=label_col_start,
                value=f"{i + 1} - {test_name} ({count})",
            )
            label_cell.font = styles["normal_font"]
            apply_wrapped_alignment(label_cell, horizontal="left", vertical="center")

            ws.row_dimensions[row].height = max(
                ws.row_dimensions[row].height or 0,
                estimate_row_height([test_name], base_height=18, chars_per_line=28),
            )

        legend_row_count = math.ceil(len(sorted_tests) / legend_columns)
        bar_bottom_row = legend_start_row + legend_row_count
    else:
        bar_bottom_row = test_start_row

    # Pie chart stacked below the bar chart/legend (not beside it), keeping
    # everything in a single column so the sheet reads top-to-bottom.
    pie_section_row = bar_bottom_row + 2
    status_col = 32
    status_count_col = 33
    ws.cell(row=pie_section_row, column=status_col, value="Status")
    ws.cell(row=pie_section_row, column=status_count_col, value="Count")
    ws.cell(row=pie_section_row + 1, column=status_col, value="Compliant")
    ws.cell(row=pie_section_row + 1, column=status_count_col, value=dataset["compliant_clinics"])
    ws.cell(row=pie_section_row + 2, column=status_col, value="Non-Compliant")
    ws.cell(row=pie_section_row + 2, column=status_count_col, value=dataset["non_compliant_clinics"])

    pie = PieChart()
    pie.title = "Clinic Compliance Status"
    pie.height = 7.8
    pie.width = 6.6
    pie.legend.position = "r"
    pie.legend.overlay = False
    pie.varyColors = False

    pie_labels = Reference(ws, min_col=status_col, min_row=pie_section_row + 1, max_row=pie_section_row + 2)
    pie_data = Reference(ws, min_col=status_count_col, min_row=pie_section_row, max_row=pie_section_row + 2)
    pie.add_data(pie_data, titles_from_data=True)
    pie.set_categories(pie_labels)

    pie.dLbls = DataLabelList()
    pie.dLbls.showVal = True
    pie.dLbls.showPercent = False
    pie.dLbls.showLegendKey = False
    pie.dLbls.showCatName = False

    if len(pie.series) > 0:
        series = pie.series[0]
        series.data_points = [DataPoint(idx=0), DataPoint(idx=1)]
        series.data_points[0].graphicalProperties.solidFill = "4F81BD"
        series.data_points[0].graphicalProperties.line.solidFill = "4F81BD"
        series.data_points[1].graphicalProperties.solidFill = "C0504D"
        series.data_points[1].graphicalProperties.line.solidFill = "C0504D"

    ws.add_chart(pie, f"A{pie_section_row}")


def write_clinic_sheet(ws, selected_detail, assessment_items, sheet_title=None):
    styles = get_excel_styles()
    if sheet_title:
        ws.title = sanitize_sheet_name(sheet_title, "Clinic")
    ws.sheet_view.showGridLines = False

    thin_border = styles["thin_border"]
    medium_border = styles["medium_border"]
    title_font = styles["title_font"]
    header_font = styles["header_font"]
    normal_font = styles["normal_font"]
    title_fill = styles["title_fill"]
    header_fill = styles["header_fill"]
    criteria_fill = styles["criteria_fill"]
    item_fill = styles["item_fill"]
    white_fill = styles["white_fill"]
    amber_fill = styles["amber_fill"]

    ws.merge_cells("A1:H1")
    ws["A1"] = "HMPO Clinic Point-of-Care Testing Checklist"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws["A1"].fill = title_fill
    ws["A1"].border = medium_border

    headers = [
        "Criteria Description",
        "Item no.",
        "YES",
        "NO",
        "STL",
        "N/A",
        "COMMENTS",
        "CUSTOM COMMENTS",
    ]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = medium_border

    ws.column_dimensions["A"].width = 95
    ws.column_dimensions["B"].width = 9
    ws.column_dimensions["C"].width = 9
    ws.column_dimensions["D"].width = 9
    ws.column_dimensions["E"].width = 9
    ws.column_dimensions["F"].width = 9
    ws.column_dimensions["G"].width = 44
    ws.column_dimensions["H"].width = 34
    ws.column_dimensions["I"].width = 4
    ws.column_dimensions["J"].width = 20
    ws.column_dimensions["K"].width = 12
    ws.column_dimensions["L"].width = 12
    ws.column_dimensions["M"].width = 12
    ws.column_dimensions["N"].width = 12
    ws.column_dimensions["O"].width = 12

    classification_column_map = {"yes": 3, "no": 4, "stl": 5, "na": 6}
    category_no_counts = {}
    category_stl_counts = {}
    yes_count = no_count = stl_count = na_count = 0

    start_row = 3
    for idx, item in enumerate(assessment_items, start=0):
        row_num = start_row + idx
        category = item["category"]
        number = item["number"]

        answer = (selected_detail.get(f"q{number}_answer") or "").strip()
        classification = classify_answer(answer)
        comment_text = build_comment_text(selected_detail, number)
        custom_comment = get_custom_comment(selected_detail, number)

        criteria_cell = ws.cell(row=row_num, column=1, value=item["text"])
        criteria_cell.font = normal_font
        criteria_cell.fill = criteria_fill
        criteria_cell.border = thin_border
        apply_wrapped_alignment(criteria_cell, horizontal="left", vertical="top")

        item_cell = ws.cell(row=row_num, column=2, value=number)
        item_cell.font = normal_font
        item_cell.fill = item_fill
        item_cell.alignment = Alignment(horizontal="center", vertical="center")
        item_cell.border = thin_border

        for col in range(3, 7):
            answer_cell = ws.cell(row=row_num, column=col, value="")
            answer_cell.font = normal_font
            answer_cell.fill = white_fill
            answer_cell.alignment = Alignment(horizontal="center", vertical="center")
            answer_cell.border = thin_border

        ws.cell(row=row_num, column=classification_column_map[classification], value="x")

        comment_cell = ws.cell(row=row_num, column=7, value=comment_text)
        comment_cell.font = normal_font
        comment_cell.fill = white_fill
        comment_cell.border = thin_border
        apply_wrapped_alignment(comment_cell, horizontal="left", vertical="top")

        custom_comment_cell = ws.cell(row=row_num, column=8, value=custom_comment)
        custom_comment_cell.font = normal_font
        custom_comment_cell.fill = white_fill
        custom_comment_cell.border = thin_border
        apply_wrapped_alignment(custom_comment_cell, horizontal="left", vertical="top")

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

        ws.row_dimensions[row_num].height = estimate_row_height(
            [item["text"], comment_text, custom_comment],
            base_height=28,
            chars_per_line=60,
            min_lines=1,
        )

    display_category_map = {
        "CLIA CERTIFICATION": "CLIA Certification",
        "WORKFLOW & TESTING PROCEDURES": "Workflow and Testing",
        "OBSERVATION/INTERVIEW": "Observation/Interview",
    }
    ordered_categories = [
        "CLIA CERTIFICATION",
        "WORKFLOW & TESTING PROCEDURES",
        "OBSERVATION/INTERVIEW",
    ]

    summary_label_row = start_row + len(assessment_items) + 1
    summary_value_row = summary_label_row + 1
    compliance = calculate_percentage(yes_count, no_count, stl_count)
    summary_cols = {
        1: "Item:",
        2: "Out of",
        3: "Yes",
        4: "No",
        5: "STL",
        6: "N/A",
        7: "Compliance %",
    }
    summary_values = {
        1: yes_count,
        2: len(assessment_items) - na_count,
        3: yes_count,
        4: no_count,
        5: stl_count,
        6: na_count,
        7: format_percentage(compliance),
    }

    for col_idx, label in summary_cols.items():
        cell = ws.cell(row=summary_label_row, column=col_idx, value=label)
        cell.font = header_font
        cell.fill = amber_fill
        cell.border = medium_border
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for col_idx, value in summary_values.items():
        cell = ws.cell(row=summary_value_row, column=col_idx, value=value)
        cell.font = normal_font
        cell.fill = amber_fill
        cell.border = medium_border
        cell.alignment = Alignment(horizontal="center", vertical="center")

    details_start_row = summary_value_row + 1
    detail_pairs = [
        ("Clinic:", selected_detail.get("clinic_name") or ""),
        ("Date:", selected_detail.get("assessment_date") or ""),
        ("Region:", selected_detail.get("region") or ""),
        ("Specialty:", selected_detail.get("specialty") or ""),
    ]
    for idx, (label, value) in enumerate(detail_pairs):
        r = details_start_row + idx
        ws.cell(row=r, column=1, value=label).font = header_font
        ws.cell(row=r, column=1).border = thin_border
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
        merged_cell = ws.cell(row=r, column=2, value=value)
        merged_cell.border = thin_border
        merged_cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        for c in range(2, 9):
            ws.cell(row=r, column=c).border = thin_border
        ws.row_dimensions[r].height = estimate_row_height(
            [label, value], base_height=20, chars_per_line=70
        )

    max_row = details_start_row + len(detail_pairs) - 1
    for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=8):
        for cell in row:
            if cell.row == 1:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif cell.column in (2, 3, 4, 5, 6):
                cell.alignment = Alignment(
                    horizontal="center", vertical="center", wrap_text=True
                )
            else:
                cell.alignment = Alignment(vertical="center", wrap_text=True)

    # Findings table + chart sit below everything else (not beside the item
    # table) so they read as a summary section instead of floating content
    # off to the side of the checklist.
    findings_header_row = max_row + 2
    ws.cell(row=findings_header_row, column=1, value="Category").font = header_font
    ws.cell(row=findings_header_row, column=2, value="Findings").font = header_font
    ws.cell(row=findings_header_row, column=3, value="Stop the Line").font = header_font
    for c in range(1, 4):
        cell = ws.cell(row=findings_header_row, column=c)
        cell.fill = header_fill
        cell.border = medium_border
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )

    findings_data_start = findings_header_row + 1
    for idx, category in enumerate(ordered_categories, start=0):
        r = findings_data_start + idx
        ws.cell(row=r, column=1, value=display_category_map.get(category, category))
        ws.cell(row=r, column=2, value=category_no_counts.get(category, 0))
        ws.cell(row=r, column=3, value=category_stl_counts.get(category, 0))
        for c in range(1, 4):
            ws.cell(row=r, column=c).border = thin_border
            ws.cell(row=r, column=c).alignment = Alignment(
                horizontal="center", vertical="center", wrap_text=True
            )
        ws.cell(row=r, column=1).alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )

    chart = BarChart()
    chart.type = "col"
    chart.style = 2
    chart.title = "Point of Care Visit Results"
    chart.width = 19.5
    chart.height = 11.5
    chart.gapWidth = 170
    chart.overlap = 0
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.x_axis.title = None
    chart.y_axis.title = "Count"
    chart.y_axis.scaling.min = 0
    chart.y_axis.majorUnit = 1

    data = Reference(
        ws,
        min_col=2,
        max_col=3,
        min_row=findings_header_row,
        max_row=findings_data_start + len(ordered_categories) - 1,
    )
    categories = Reference(
        ws,
        min_col=1,
        min_row=findings_data_start,
        max_row=findings_data_start + len(ordered_categories) - 1,
    )
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.legend.position = "r"
    chart.legend.overlay = False

    if len(chart.series) > 0:
        chart.series[0].graphicalProperties.solidFill = "ED7D31"
        chart.series[0].graphicalProperties.line.solidFill = "ED7D31"
    if len(chart.series) > 1:
        chart.series[1].graphicalProperties.solidFill = "C00000"
        chart.series[1].graphicalProperties.line.solidFill = "C00000"

    chart_anchor_row = findings_data_start + len(ordered_categories) + 2
    ws.add_chart(chart, f"A{chart_anchor_row}")


def build_detail_from_dashboard_row(source_row, assessment_items):
    detail = {
        "id": source_row[0],
        "clinic_name": source_row[1] or "",
        "region": source_row[2] or "",
        "specialty": source_row[3] or "",
        "assessment_date": source_row[4] or "",
        "tests_performed": source_row[5] or "",
        "notes": source_row[6] or "",
    }

    for idx, item in enumerate(assessment_items):
        number = item["number"]
        base_index = 7 + (idx * 3)

        answer = source_row[base_index] or ""
        template_comment = source_row[base_index + 1] or ""
        custom_comment = source_row[base_index + 2] or ""

        manual_comment = custom_comment or ""
        combined_comment = template_comment or ""

        detail[f"q{number}_answer"] = answer
        detail[f"q{number}_template_comment"] = template_comment
        detail[f"q{number}_custom_comment"] = custom_comment
        detail[f"q{number}_manual_comment"] = manual_comment
        detail[f"q{number}_comment"] = combined_comment

    return detail


def export_clinic_workbook(
    file_path,
    selected_detail,
    assessment_items,
    clinic_name=None,
    sheet_title="Clinic Checklist",
):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title

    detail = dict(selected_detail or {})
    if clinic_name and not detail.get("clinic_name"):
        detail["clinic_name"] = clinic_name

    write_clinic_sheet(ws, detail, assessment_items, sheet_title=sheet_title)
    wb.save(file_path)