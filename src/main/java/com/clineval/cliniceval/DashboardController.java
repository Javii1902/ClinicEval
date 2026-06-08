package com.clineval.cliniceval;

import com.clineval.cliniceval.config.DbManager;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.scene.chart.BarChart;
import javafx.scene.chart.XYChart;
import javafx.scene.control.Alert;
import javafx.scene.control.Label;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.stage.FileChooser;
import javafx.stage.Window;

import java.io.File;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class DashboardController {

    private static final double COMPLIANT_THRESHOLD = 70.0;

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

    @FXML
    private Label overallComplianceLabel;

    @FXML
    private Label compliantClinicsLabel;

    @FXML
    private Label nonCompliantClinicsLabel;

    @FXML
    private BarChart<String, Number> clinicStatusChart;

    @FXML
    private TableView<DashboardClinicRow> clinicComplianceTable;

    @FXML
    private TableColumn<DashboardClinicRow, String> clinicNameColumn;

    @FXML
    private TableColumn<DashboardClinicRow, String> clinicComplianceColumn;

    @FXML
    private TableColumn<DashboardClinicRow, String> clinicYesCountColumn;

    @FXML
    private TableColumn<DashboardClinicRow, String> clinicNoCountColumn;

    @FXML
    private TableColumn<DashboardClinicRow, String> clinicNaCountColumn;

    @FXML
    private TableView<DashboardQuestionRow> questionComplianceTable;

    @FXML
    private TableColumn<DashboardQuestionRow, String> questionColumn;

    @FXML
    private TableColumn<DashboardQuestionRow, String> questionComplianceColumn;

    @FXML
    private TableColumn<DashboardQuestionRow, String> yesCountColumn;

    @FXML
    private TableColumn<DashboardQuestionRow, String> noCountColumn;

    @FXML
    private TableColumn<DashboardQuestionRow, String> naCountColumn;

    private final ObservableList<DashboardClinicRow> clinicRows = FXCollections.observableArrayList();
    private final ObservableList<DashboardQuestionRow> questionRows = FXCollections.observableArrayList();

    @FXML
    public void initialize() {
        clinicNameColumn.setCellValueFactory(data -> data.getValue().clinicNameProperty());
        clinicComplianceColumn.setCellValueFactory(data -> data.getValue().compliancePercentageProperty());
        clinicYesCountColumn.setCellValueFactory(data -> data.getValue().yesCountProperty());
        clinicNoCountColumn.setCellValueFactory(data -> data.getValue().noCountProperty());
        clinicNaCountColumn.setCellValueFactory(data -> data.getValue().naCountProperty());

        questionColumn.setCellValueFactory(data -> data.getValue().questionProperty());
        questionComplianceColumn.setCellValueFactory(data -> data.getValue().compliancePercentageProperty());
        yesCountColumn.setCellValueFactory(data -> data.getValue().yesCountProperty());
        noCountColumn.setCellValueFactory(data -> data.getValue().noCountProperty());
        naCountColumn.setCellValueFactory(data -> data.getValue().naCountProperty());

        clinicComplianceTable.setItems(clinicRows);
        questionComplianceTable.setItems(questionRows);

        loadDashboard();
    }

    private void loadDashboard() {
        loadOverallCompliance();
        loadClinicCompliance();
        loadQuestionCompliance();
    }

    private void loadOverallCompliance() {
        int yesCount = 0;
        int noCount = 0;

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(LATEST_ASSESSMENTS_SQL);
             ResultSet rs = stmt.executeQuery()) {

            while (rs.next()) {
                for (int i = 1; i <= 15; i++) {
                    String answer = rs.getString("q" + i + "_answer");
                    if ("Yes".equalsIgnoreCase(answer)) {
                        yesCount++;
                    } else if ("No".equalsIgnoreCase(answer)) {
                        noCount++;
                    }
                }
            }

            int denominator = yesCount + noCount;
            double compliance = denominator == 0 ? 0.0 : (yesCount * 100.0) / denominator;
            overallComplianceLabel.setText(String.format("%.2f%%", compliance));

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Dashboard Error", "Could not load overall compliance.");
        }
    }

    private void loadClinicCompliance() {
        clinicRows.clear();
        clinicStatusChart.getData().clear();

        int compliantCount = 0;
        int nonCompliantCount = 0;

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(LATEST_ASSESSMENTS_SQL);
             ResultSet rs = stmt.executeQuery()) {

            while (rs.next()) {
                String clinicName = rs.getString("clinic_name");

                int yesCount = 0;
                int noCount = 0;
                int naCount = 0;

                for (int i = 1; i <= 15; i++) {
                    String answer = rs.getString("q" + i + "_answer");
                    if ("Yes".equalsIgnoreCase(answer)) {
                        yesCount++;
                    } else if ("No".equalsIgnoreCase(answer)) {
                        noCount++;
                    } else if ("N/A".equalsIgnoreCase(answer)) {
                        naCount++;
                    }
                }

                int denominator = yesCount + noCount;
                double compliance = denominator == 0 ? 0.0 : (yesCount * 100.0) / denominator;

                if (denominator > 0) {
                    if (compliance > COMPLIANT_THRESHOLD) {
                        compliantCount++;
                    } else {
                        nonCompliantCount++;
                    }
                }

                clinicRows.add(new DashboardClinicRow(
                        clinicName,
                        denominator == 0 ? "N/A" : String.format("%.2f%%", compliance),
                        String.valueOf(yesCount),
                        String.valueOf(noCount),
                        String.valueOf(naCount)
                ));
            }

            compliantClinicsLabel.setText(String.valueOf(compliantCount));
            nonCompliantClinicsLabel.setText(String.valueOf(nonCompliantCount));

            XYChart.Series<String, Number> series = new XYChart.Series<>();
            series.setName("Clinic Count");
            series.getData().add(new XYChart.Data<>("Compliant", compliantCount));
            series.getData().add(new XYChart.Data<>("Non-Compliant", nonCompliantCount));
            clinicStatusChart.getData().add(series);

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Dashboard Error", "Could not load clinic compliance data.");
        }
    }

    private void loadQuestionCompliance() {
        int[] yesCounts = new int[15];
        int[] noCounts = new int[15];
        int[] naCounts = new int[15];

        questionRows.clear();

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(LATEST_ASSESSMENTS_SQL);
             ResultSet rs = stmt.executeQuery()) {

            while (rs.next()) {
                for (int i = 1; i <= 15; i++) {
                    String answer = rs.getString("q" + i + "_answer");
                    if ("Yes".equalsIgnoreCase(answer)) {
                        yesCounts[i - 1]++;
                    } else if ("No".equalsIgnoreCase(answer)) {
                        noCounts[i - 1]++;
                    } else if ("N/A".equalsIgnoreCase(answer)) {
                        naCounts[i - 1]++;
                    }
                }
            }

            for (int i = 0; i < 15; i++) {
                int denominator = yesCounts[i] + noCounts[i];
                String complianceDisplay = denominator == 0
                        ? "N/A"
                        : String.format("%.2f%%", (yesCounts[i] * 100.0) / denominator);

                questionRows.add(new DashboardQuestionRow(
                        "Question " + (i + 1),
                        complianceDisplay,
                        String.valueOf(yesCounts[i]),
                        String.valueOf(noCounts[i]),
                        String.valueOf(naCounts[i])
                ));
            }

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Dashboard Error", "Could not load question compliance data.");
        }
    }

    @FXML
    private void handleExportToExcel(ActionEvent event) {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Save Excel Export");
        fileChooser.setInitialFileName("clinic_assessment_export.xlsx");
        fileChooser.getExtensionFilters().add(
                new FileChooser.ExtensionFilter("Excel Workbook (*.xlsx)", "*.xlsx")
        );

        Window window = clinicComplianceTable.getScene() != null ? clinicComplianceTable.getScene().getWindow() : null;
        File file = fileChooser.showSaveDialog(window);

        if (file == null) {
            return;
        }

        try {
            ExcelExportService.exportLatestAssessmentsWorkbook(
                    file,
                    overallComplianceLabel.getText(),
                    compliantClinicsLabel.getText(),
                    nonCompliantClinicsLabel.getText(),
                    clinicRows,
                    questionRows
            );

            Alert alert = new Alert(Alert.AlertType.INFORMATION);
            alert.setTitle("Export Complete");
            alert.setHeaderText(null);
            alert.setContentText("Excel export saved successfully.");
            alert.showAndWait();

        } catch (Exception e) {
            e.printStackTrace();
            showException("Export Error", "Could not export Excel workbook.", e);
        }
    }

    private void showError(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }

    private void showException(String title, String header, Exception exception) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle(title);
        alert.setHeaderText(header);
        alert.setContentText(exception.getClass().getSimpleName() + ": " + exception.getMessage());

        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);
        exception.printStackTrace(pw);

        javafx.scene.control.TextArea textArea = new javafx.scene.control.TextArea(sw.toString());
        textArea.setEditable(false);
        textArea.setWrapText(false);
        textArea.setMaxWidth(Double.MAX_VALUE);
        textArea.setMaxHeight(Double.MAX_VALUE);

        javafx.scene.layout.GridPane.setVgrow(textArea, javafx.scene.layout.Priority.ALWAYS);
        javafx.scene.layout.GridPane.setHgrow(textArea, javafx.scene.layout.Priority.ALWAYS);

        javafx.scene.layout.GridPane expandableContent = new javafx.scene.layout.GridPane();
        expandableContent.setMaxWidth(Double.MAX_VALUE);
        expandableContent.add(new javafx.scene.control.Label("Stack trace:"), 0, 0);
        expandableContent.add(textArea, 0, 1);

        alert.getDialogPane().setExpandableContent(expandableContent);
        alert.showAndWait();
    }
}