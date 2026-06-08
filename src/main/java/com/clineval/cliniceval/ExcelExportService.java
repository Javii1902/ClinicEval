package com.clineval.cliniceval;

import com.clineval.cliniceval.config.DbManager;
import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.FillPatternType;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ExcelExportService {

    private static final String LATEST_ASSESSMENTS_SQL = """
            SELECT a.*
            FROM assessments a
            INNER JOIN (
                SELECT clinic_name, MAX(assessment_date) AS latest_date
                FROM assessments
                GROUP BY clinic_name
            ) latest
                ON a.clinic_name = latest.clinic_name
               AND a.assessment_date = latest.latest_date
            WHERE a.id = (
                SELECT MAX(a2.id)
                FROM assessments a2
                WHERE a2.clinic_name = a.clinic_name
                  AND a2.assessment_date = a.assessment_date
            )
            ORDER BY a.clinic_name
            """;

    public static void exportLatestAssessmentsWorkbook(
            File file,
            String overallCompliance,
            String compliantClinics,
            String nonCompliantClinics,
            List<DashboardClinicRow> clinicRows,
            List<DashboardQuestionRow> questionRows
    ) throws SQLException, IOException {

        try (Workbook workbook = new XSSFWorkbook()) {
            CellStyle headerStyle = createHeaderStyle(workbook);
            CellStyle sectionStyle = createSectionStyle(workbook);

            createDashboardSheet(
                    workbook,
                    headerStyle,
                    sectionStyle,
                    overallCompliance,
                    compliantClinics,
                    nonCompliantClinics,
                    clinicRows,
                    questionRows
            );

            createClinicSheets(workbook, headerStyle, sectionStyle);

            try (FileOutputStream out = new FileOutputStream(file)) {
                workbook.write(out);
            }
        }
    }

    private static void createDashboardSheet(
            Workbook workbook,
            CellStyle headerStyle,
            CellStyle sectionStyle,
            String overallCompliance,
            String compliantClinics,
            String nonCompliantClinics,
            List<DashboardClinicRow> clinicRows,
            List<DashboardQuestionRow> questionRows
    ) {
        Sheet sheet = workbook.createSheet("Dashboard");
        int rowIndex = 0;

        Row titleRow = sheet.createRow(rowIndex++);
        createCell(titleRow, 0, "Dashboard Summary", sectionStyle);

        Row summaryHeader = sheet.createRow(rowIndex++);
        createCell(summaryHeader, 0, "Metric", headerStyle);
        createCell(summaryHeader, 1, "Value", headerStyle);

        Row overallRow = sheet.createRow(rowIndex++);
        createCell(overallRow, 0, "Overall Compliance", null);
        createCell(overallRow, 1, overallCompliance, null);

        Row compliantRow = sheet.createRow(rowIndex++);
        createCell(compliantRow, 0, "Compliant Clinics", null);
        createCell(compliantRow, 1, compliantClinics, null);

        Row nonCompliantRow = sheet.createRow(rowIndex++);
        createCell(nonCompliantRow, 0, "Non-Compliant Clinics", null);
        createCell(nonCompliantRow, 1, nonCompliantClinics, null);

        rowIndex++;

        Row clinicSectionRow = sheet.createRow(rowIndex++);
        createCell(clinicSectionRow, 0, "Clinic Compliance Table", sectionStyle);

        Row clinicHeader = sheet.createRow(rowIndex++);
        createCell(clinicHeader, 0, "Clinic Name", headerStyle);
        createCell(clinicHeader, 1, "Compliance Percentage", headerStyle);
        createCell(clinicHeader, 2, "Yes", headerStyle);
        createCell(clinicHeader, 3, "No", headerStyle);
        createCell(clinicHeader, 4, "N/A", headerStyle);

        for (DashboardClinicRow row : clinicRows) {
            Row dataRow = sheet.createRow(rowIndex++);
            createCell(dataRow, 0, row.getClinicName(), null);
            createCell(dataRow, 1, row.getCompliancePercentage(), null);
            createCell(dataRow, 2, row.getYesCount(), null);
            createCell(dataRow, 3, row.getNoCount(), null);
            createCell(dataRow, 4, row.getNaCount(), null);
        }

        rowIndex++;

        Row questionSectionRow = sheet.createRow(rowIndex++);
        createCell(questionSectionRow, 0, "Question Compliance Table", sectionStyle);

        Row questionHeader = sheet.createRow(rowIndex++);
        createCell(questionHeader, 0, "Question", headerStyle);
        createCell(questionHeader, 1, "Compliance Percentage", headerStyle);
        createCell(questionHeader, 2, "Yes", headerStyle);
        createCell(questionHeader, 3, "No", headerStyle);
        createCell(questionHeader, 4, "N/A", headerStyle);

        for (DashboardQuestionRow row : questionRows) {
            Row dataRow = sheet.createRow(rowIndex++);
            createCell(dataRow, 0, row.getQuestion(), null);
            createCell(dataRow, 1, row.getCompliancePercentage(), null);
            createCell(dataRow, 2, row.getYesCount(), null);
            createCell(dataRow, 3, row.getNoCount(), null);
            createCell(dataRow, 4, row.getNaCount(), null);
        }

        autoSizeColumns(sheet, 5);
    }

    private static void createClinicSheets(Workbook workbook, CellStyle headerStyle, CellStyle sectionStyle)
            throws SQLException {

        Map<String, Integer> sheetNameCounts = new HashMap<>();

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(LATEST_ASSESSMENTS_SQL);
             ResultSet rs = stmt.executeQuery()) {

            while (rs.next()) {
                String clinicName = safeString(rs.getString("clinic_name"));
                String sheetName = buildUniqueSheetName(clinicName, sheetNameCounts);

                Sheet sheet = workbook.createSheet(sheetName);
                int rowIndex = 0;

                Row titleRow = sheet.createRow(rowIndex++);
                createCell(titleRow, 0, clinicName, sectionStyle);

                Row infoHeader = sheet.createRow(rowIndex++);
                createCell(infoHeader, 0, "Field", headerStyle);
                createCell(infoHeader, 1, "Value", headerStyle);

                Row clinicRow = sheet.createRow(rowIndex++);
                createCell(clinicRow, 0, "Clinic Name", null);
                createCell(clinicRow, 1, clinicName, null);

                Row dateRow = sheet.createRow(rowIndex++);
                createCell(dateRow, 0, "Assessment Date", null);
                createCell(dateRow, 1, String.valueOf(rs.getDate("assessment_date")), null);

                int yesCount = 0;
                int noCount = 0;
                int naCount = 0;

                for (int i = 1; i <= 15; i++) {
                    String answer = safeString(rs.getString("q" + i + "_answer"));
                    if ("Yes".equalsIgnoreCase(answer)) {
                        yesCount++;
                    } else if ("No".equalsIgnoreCase(answer)) {
                        noCount++;
                    } else if ("N/A".equalsIgnoreCase(answer)) {
                        naCount++;
                    }
                }

                int denominator = yesCount + noCount;
                String compliance = denominator == 0
                        ? "N/A"
                        : String.format("%.2f%%", (yesCount * 100.0) / denominator);

                Row complianceRow = sheet.createRow(rowIndex++);
                createCell(complianceRow, 0, "Compliance Percentage", null);
                createCell(complianceRow, 1, compliance, null);

                Row yesRow = sheet.createRow(rowIndex++);
                createCell(yesRow, 0, "Yes Count", null);
                createCell(yesRow, 1, String.valueOf(yesCount), null);

                Row noRow = sheet.createRow(rowIndex++);
                createCell(noRow, 0, "No Count", null);
                createCell(noRow, 1, String.valueOf(noCount), null);

                Row naRow = sheet.createRow(rowIndex++);
                createCell(naRow, 0, "N/A Count", null);
                createCell(naRow, 1, String.valueOf(naCount), null);

                rowIndex++;

                Row tableSection = sheet.createRow(rowIndex++);
                createCell(tableSection, 0, "Assessment Responses", sectionStyle);

                Row responseHeader = sheet.createRow(rowIndex++);
                createCell(responseHeader, 0, "Question", headerStyle);
                createCell(responseHeader, 1, "Answer", headerStyle);

                for (int i = 1; i <= 15; i++) {
                    Row responseRow = sheet.createRow(rowIndex++);
                    createCell(responseRow, 0, "Question " + i, null);
                    createCell(responseRow, 1, safeString(rs.getString("q" + i + "_answer")), null);
                }

                rowIndex++;

                Row notesSection = sheet.createRow(rowIndex++);
                createCell(notesSection, 0, "Overall Comments", sectionStyle);

                Row notesHeader = sheet.createRow(rowIndex++);
                createCell(notesHeader, 0, "Notes", headerStyle);

                Row notesRow = sheet.createRow(rowIndex++);
                createCell(notesRow, 0, getNotesValue(rs), null);

                autoSizeColumns(sheet, 2);
            }
        }
    }

    private static String getNotesValue(ResultSet rs) {
        try {
            return safeString(rs.getString("notes"));
        } catch (SQLException e) {
            return "";
        }
    }

    private static String buildUniqueSheetName(String clinicName, Map<String, Integer> sheetNameCounts) {
        String base = sanitizeSheetName(clinicName);
        int count = sheetNameCounts.getOrDefault(base, 0);

        if (count == 0) {
            sheetNameCounts.put(base, 1);
            return base;
        }

        String candidate;
        do {
            count++;
            String suffix = " (" + count + ")";
            String shortenedBase = base;
            int maxBaseLength = 31 - suffix.length();
            if (shortenedBase.length() > maxBaseLength) {
                shortenedBase = shortenedBase.substring(0, maxBaseLength);
            }
            candidate = shortenedBase + suffix;
        } while (sheetNameCounts.containsKey(candidate));

        sheetNameCounts.put(base, count);
        sheetNameCounts.put(candidate, 1);
        return candidate;
    }

    private static String sanitizeSheetName(String name) {
        if (name == null || name.isBlank()) {
            return "Clinic";
        }

        String sanitized = name.replaceAll("[\\\\/*?:\\[\\]]", "_").trim();
        if (sanitized.length() > 31) {
            sanitized = sanitized.substring(0, 31);
        }
        if (sanitized.isBlank()) {
            sanitized = "Clinic";
        }
        return sanitized;
    }

    private static CellStyle createHeaderStyle(Workbook workbook) {
        Font font = workbook.createFont();
        font.setBold(true);

        CellStyle style = workbook.createCellStyle();
        style.setFont(font);
        style.setFillForegroundColor(IndexedColors.GREY_25_PERCENT.getIndex());
        style.setFillPattern(FillPatternType.SOLID_FOREGROUND);
        setAllBorders(style);
        return style;
    }

    private static CellStyle createSectionStyle(Workbook workbook) {
        Font font = workbook.createFont();
        font.setBold(true);
        font.setFontHeightInPoints((short) 12);

        CellStyle style = workbook.createCellStyle();
        style.setFont(font);
        return style;
    }

    private static void setAllBorders(CellStyle style) {
        style.setBorderTop(BorderStyle.THIN);
        style.setBorderBottom(BorderStyle.THIN);
        style.setBorderLeft(BorderStyle.THIN);
        style.setBorderRight(BorderStyle.THIN);
    }

    private static void createCell(Row row, int columnIndex, String value, CellStyle style) {
        Cell cell = row.createCell(columnIndex);
        cell.setCellValue(value == null ? "" : value);
        if (style != null) {
            cell.setCellStyle(style);
        }
    }

    private static void autoSizeColumns(Sheet sheet, int columnCount) {
        for (int i = 0; i < columnCount; i++) {
            sheet.autoSizeColumn(i);
        }
    }

    private static String safeString(String value) {
        return value == null ? "" : value;
    }
}