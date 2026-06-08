package com.clineval.cliniceval;

import com.clineval.cliniceval.config.DbManager;
import javafx.fxml.FXML;
import javafx.scene.control.Alert;
import javafx.scene.control.DatePicker;
import javafx.scene.control.RadioButton;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.control.Toggle;
import javafx.scene.control.ToggleGroup;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.LocalDate;

public class NewAssessmentController {

    @FXML
    private TextField clinicNameField;

    @FXML
    private DatePicker assessmentDatePicker;

    @FXML
    private TextArea notesArea;

    @FXML
    private ToggleGroup q1Group;
    @FXML
    private ToggleGroup q2Group;
    @FXML
    private ToggleGroup q3Group;
    @FXML
    private ToggleGroup q4Group;
    @FXML
    private ToggleGroup q5Group;
    @FXML
    private ToggleGroup q6Group;
    @FXML
    private ToggleGroup q7Group;
    @FXML
    private ToggleGroup q8Group;
    @FXML
    private ToggleGroup q9Group;
    @FXML
    private ToggleGroup q10Group;
    @FXML
    private ToggleGroup q11Group;
    @FXML
    private ToggleGroup q12Group;
    @FXML
    private ToggleGroup q13Group;
    @FXML
    private ToggleGroup q14Group;
    @FXML
    private ToggleGroup q15Group;

    @FXML
    public void initialize() {
        assessmentDatePicker.setValue(LocalDate.now());
    }

    @FXML
    private void saveAssessment() {
        String clinicName = clinicNameField.getText() == null ? "" : clinicNameField.getText().trim();
        LocalDate assessmentDate = assessmentDatePicker.getValue();
        String notes = notesArea.getText() == null ? "" : notesArea.getText().trim();

        if (clinicName.isBlank()) {
            showError("Validation Error", "Clinic name is required.");
            return;
        }

        if (assessmentDate == null) {
            showError("Validation Error", "Assessment date is required.");
            return;
        }

        String q1 = getSelectedAnswer(q1Group);
        String q2 = getSelectedAnswer(q2Group);
        String q3 = getSelectedAnswer(q3Group);
        String q4 = getSelectedAnswer(q4Group);
        String q5 = getSelectedAnswer(q5Group);
        String q6 = getSelectedAnswer(q6Group);
        String q7 = getSelectedAnswer(q7Group);
        String q8 = getSelectedAnswer(q8Group);
        String q9 = getSelectedAnswer(q9Group);
        String q10 = getSelectedAnswer(q10Group);
        String q11 = getSelectedAnswer(q11Group);
        String q12 = getSelectedAnswer(q12Group);
        String q13 = getSelectedAnswer(q13Group);
        String q14 = getSelectedAnswer(q14Group);
        String q15 = getSelectedAnswer(q15Group);

        String sql = """
                INSERT INTO assessments (
                    clinic_name,
                    assessment_date,
                    q1_answer, q2_answer, q3_answer, q4_answer, q5_answer,
                    q6_answer, q7_answer, q8_answer, q9_answer, q10_answer,
                    q11_answer, q12_answer, q13_answer, q14_answer, q15_answer,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """;

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, clinicName);
            stmt.setDate(2, Date.valueOf(assessmentDate));
            stmt.setString(3, q1);
            stmt.setString(4, q2);
            stmt.setString(5, q3);
            stmt.setString(6, q4);
            stmt.setString(7, q5);
            stmt.setString(8, q6);
            stmt.setString(9, q7);
            stmt.setString(10, q8);
            stmt.setString(11, q9);
            stmt.setString(12, q10);
            stmt.setString(13, q11);
            stmt.setString(14, q12);
            stmt.setString(15, q13);
            stmt.setString(16, q14);
            stmt.setString(17, q15);
            stmt.setString(18, notes);

            stmt.executeUpdate();

            showInfo("Success", "Assessment saved successfully.");
            clearForm();

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Database Error", "Could not save assessment.");
        }
    }

    private String getSelectedAnswer(ToggleGroup group) {
        if (group == null) {
            return null;
        }

        Toggle selected = group.getSelectedToggle();
        if (selected == null) {
            return null;
        }

        return ((RadioButton) selected).getText();
    }

    private void clearForm() {
        clinicNameField.clear();
        assessmentDatePicker.setValue(LocalDate.now());
        notesArea.clear();

        q1Group.selectToggle(null);
        q2Group.selectToggle(null);
        q3Group.selectToggle(null);
        q4Group.selectToggle(null);
        q5Group.selectToggle(null);
        q6Group.selectToggle(null);
        q7Group.selectToggle(null);
        q8Group.selectToggle(null);
        q9Group.selectToggle(null);
        q10Group.selectToggle(null);
        q11Group.selectToggle(null);
        q12Group.selectToggle(null);
        q13Group.selectToggle(null);
        q14Group.selectToggle(null);
        q15Group.selectToggle(null);
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