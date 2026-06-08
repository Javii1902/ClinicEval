package com.clineval.cliniceval;

import com.clineval.cliniceval.config.DbManager;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import javafx.scene.layout.HBox;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class ClinicPageController {

    @FXML
    private ComboBox<String> clinicComboBox;

    @FXML
    private Label loadedClinicLabel;

    @FXML
    private Label assessmentDateLabel;

    @FXML
    private Label complianceLabel;

    @FXML
    private TextArea notesArea;

    @FXML
    private TableView<ClinicRecord> clinicTable;

    @FXML
    private TableColumn<ClinicRecord, String> questionColumn;

    @FXML
    private TableColumn<ClinicRecord, String> answerColumn;

    private final ObservableList<ClinicRecord> records = FXCollections.observableArrayList();

    @FXML
    public void initialize() {
        clinicComboBox.setEditable(true);

        questionColumn.setCellValueFactory(data -> data.getValue().questionProperty());
        answerColumn.setCellValueFactory(data -> data.getValue().answerProperty());

        answerColumn.setCellFactory(col -> new TableCell<>() {
            private final RadioButton yesButton = new RadioButton("Yes");
            private final RadioButton noButton = new RadioButton("No");
            private final RadioButton naButton = new RadioButton("N/A");
            private final ToggleGroup toggleGroup = new ToggleGroup();
            private final HBox box = new HBox(16, yesButton, noButton, naButton);

            {
                yesButton.setToggleGroup(toggleGroup);
                noButton.setToggleGroup(toggleGroup);
                naButton.setToggleGroup(toggleGroup);

                yesButton.setOnAction(e -> updateAnswer("Yes"));
                noButton.setOnAction(e -> updateAnswer("No"));
                naButton.setOnAction(e -> updateAnswer("N/A"));
            }

            private void updateAnswer(String value) {
                ClinicRecord record = getTableView().getItems().get(getIndex());
                record.setAnswer(value);
                updateComplianceLabel();
            }

            @Override
            protected void updateItem(String item, boolean empty) {
                super.updateItem(item, empty);

                if (empty || getIndex() >= getTableView().getItems().size()) {
                    setGraphic(null);
                    setText(null);
                    return;
                }

                if ("Yes".equals(item)) {
                    toggleGroup.selectToggle(yesButton);
                } else if ("No".equals(item)) {
                    toggleGroup.selectToggle(noButton);
                } else if ("N/A".equals(item)) {
                    toggleGroup.selectToggle(naButton);
                } else {
                    toggleGroup.selectToggle(null);
                }

                setGraphic(box);
                setText(null);
            }
        });

        clinicTable.setItems(records);
        loadClinicNames();
    }

    @FXML
    private void loadClinic() {
        String clinicName = getSelectedClinicName();

        if (clinicName.isBlank()) {
            showError("Validation Error", "Please select or enter a clinic name.");
            return;
        }

        String sql = """
                SELECT *
                FROM assessments
                WHERE LOWER(clinic_name) = LOWER(?)
                  AND assessment_date = (
                      SELECT MAX(assessment_date)
                      FROM assessments
                      WHERE LOWER(clinic_name) = LOWER(?)
                  )
                ORDER BY id DESC
                LIMIT 1
                """;

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, clinicName);
            stmt.setString(2, clinicName);

            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    String actualClinicName = rs.getString("clinic_name");

                    loadedClinicLabel.setText(actualClinicName);
                    assessmentDateLabel.setText(String.valueOf(rs.getDate("assessment_date")));
                    notesArea.setText(rs.getString("notes") == null ? "" : rs.getString("notes"));
                    clinicComboBox.setValue(actualClinicName);

                    records.setAll(
                            new ClinicRecord("Question 1", valueOrBlank(rs.getString("q1_answer"))),
                            new ClinicRecord("Question 2", valueOrBlank(rs.getString("q2_answer"))),
                            new ClinicRecord("Question 3", valueOrBlank(rs.getString("q3_answer"))),
                            new ClinicRecord("Question 4", valueOrBlank(rs.getString("q4_answer"))),
                            new ClinicRecord("Question 5", valueOrBlank(rs.getString("q5_answer"))),
                            new ClinicRecord("Question 6", valueOrBlank(rs.getString("q6_answer"))),
                            new ClinicRecord("Question 7", valueOrBlank(rs.getString("q7_answer"))),
                            new ClinicRecord("Question 8", valueOrBlank(rs.getString("q8_answer"))),
                            new ClinicRecord("Question 9", valueOrBlank(rs.getString("q9_answer"))),
                            new ClinicRecord("Question 10", valueOrBlank(rs.getString("q10_answer"))),
                            new ClinicRecord("Question 11", valueOrBlank(rs.getString("q11_answer"))),
                            new ClinicRecord("Question 12", valueOrBlank(rs.getString("q12_answer"))),
                            new ClinicRecord("Question 13", valueOrBlank(rs.getString("q13_answer"))),
                            new ClinicRecord("Question 14", valueOrBlank(rs.getString("q14_answer"))),
                            new ClinicRecord("Question 15", valueOrBlank(rs.getString("q15_answer")))
                    );

                    updateComplianceLabel();
                    loadClinicNames();
                } else {
                    records.clear();
                    loadedClinicLabel.setText("-");
                    assessmentDateLabel.setText("-");
                    notesArea.clear();
                    complianceLabel.setText("Compliance: -");
                    showInfo("Not Found", "No assessment found for that clinic.");
                }
            }

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Database Error", "Could not load clinic data.");
        }
    }

    private void loadClinicNames() {
        String sql = """
                SELECT DISTINCT clinic_name
                FROM assessments
                WHERE clinic_name IS NOT NULL
                  AND TRIM(clinic_name) <> ''
                ORDER BY clinic_name
                """;

        ObservableList<String> clinicNames = FXCollections.observableArrayList();

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {

            while (rs.next()) {
                clinicNames.add(rs.getString("clinic_name"));
            }

            clinicComboBox.setItems(clinicNames);

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Database Error", "Could not load clinic list.");
        }
    }

    private String getSelectedClinicName() {
        String value = clinicComboBox.getValue();

        if (value == null || value.isBlank()) {
            value = clinicComboBox.getEditor().getText();
        }

        return value == null ? "" : value.trim();
    }

    private void updateComplianceLabel() {
        int yesCount = 0;
        int noCount = 0;

        for (ClinicRecord record : records) {
            String answer = record.getAnswer();
            if ("Yes".equalsIgnoreCase(answer)) {
                yesCount++;
            } else if ("No".equalsIgnoreCase(answer)) {
                noCount++;
            }
        }

        int denominator = yesCount + noCount;

        if (denominator == 0) {
            complianceLabel.setText("Compliance: 0.00%");
            return;
        }

        double compliance = (yesCount * 100.0) / denominator;
        complianceLabel.setText(String.format("Compliance: %.2f%%", compliance));
    }

    private String valueOrBlank(String value) {
        return value == null ? "" : value;
    }

    private void showInfo(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }

    private void showError(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }
}