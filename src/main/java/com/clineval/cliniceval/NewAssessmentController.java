package com.clineval.cliniceval;

import com.clineval.cliniceval.config.DbManager;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import javafx.scene.control.ToggleGroup;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;

public class NewAssessmentController {

    @FXML
    private ComboBox<String> clinicComboBox;

    @FXML
    private DatePicker assessmentDatePicker;

    @FXML
    private RadioButton q1YesRadio;
    @FXML
    private RadioButton q1NoRadio;
    @FXML
    private RadioButton q1NaRadio;
    @FXML
    private TextArea q1CommentArea;

    @FXML
    private RadioButton q2YesRadio;
    @FXML
    private RadioButton q2NoRadio;
    @FXML
    private RadioButton q2NaRadio;
    @FXML
    private TextArea q2CommentArea;

    @FXML
    private RadioButton q3YesRadio;
    @FXML
    private RadioButton q3NoRadio;
    @FXML
    private RadioButton q3NaRadio;
    @FXML
    private TextArea q3CommentArea;

    @FXML
    private RadioButton q4YesRadio;
    @FXML
    private RadioButton q4NoRadio;
    @FXML
    private RadioButton q4NaRadio;
    @FXML
    private TextArea q4CommentArea;

    @FXML
    private RadioButton q5YesRadio;
    @FXML
    private RadioButton q5NoRadio;
    @FXML
    private RadioButton q5NaRadio;
    @FXML
    private TextArea q5CommentArea;

    @FXML
    private RadioButton q6YesRadio;
    @FXML
    private RadioButton q6NoRadio;
    @FXML
    private RadioButton q6NaRadio;
    @FXML
    private TextArea q6CommentArea;

    @FXML
    private RadioButton q7YesRadio;
    @FXML
    private RadioButton q7NoRadio;
    @FXML
    private RadioButton q7NaRadio;
    @FXML
    private TextArea q7CommentArea;

    @FXML
    private RadioButton q8YesRadio;
    @FXML
    private RadioButton q8NoRadio;
    @FXML
    private RadioButton q8NaRadio;
    @FXML
    private TextArea q8CommentArea;

    @FXML
    private RadioButton q9YesRadio;
    @FXML
    private RadioButton q9NoRadio;
    @FXML
    private RadioButton q9NaRadio;
    @FXML
    private TextArea q9CommentArea;

    @FXML
    private RadioButton q10YesRadio;
    @FXML
    private RadioButton q10NoRadio;
    @FXML
    private RadioButton q10NaRadio;
    @FXML
    private TextArea q10CommentArea;

    @FXML
    private RadioButton q11YesRadio;
    @FXML
    private RadioButton q11NoRadio;
    @FXML
    private RadioButton q11NaRadio;
    @FXML
    private TextArea q11CommentArea;

    @FXML
    private RadioButton q12YesRadio;
    @FXML
    private RadioButton q12NoRadio;
    @FXML
    private RadioButton q12NaRadio;
    @FXML
    private TextArea q12CommentArea;

    @FXML
    private RadioButton q13YesRadio;
    @FXML
    private RadioButton q13NoRadio;
    @FXML
    private RadioButton q13NaRadio;
    @FXML
    private TextArea q13CommentArea;

    @FXML
    private RadioButton q14YesRadio;
    @FXML
    private RadioButton q14NoRadio;
    @FXML
    private RadioButton q14NaRadio;
    @FXML
    private TextArea q14CommentArea;

    @FXML
    private RadioButton q15YesRadio;
    @FXML
    private RadioButton q15NoRadio;
    @FXML
    private RadioButton q15NaRadio;
    @FXML
    private TextArea q15CommentArea;

    @FXML
    private TextArea overallCommentsArea;

    private ToggleGroup q1Group;
    private ToggleGroup q2Group;
    private ToggleGroup q3Group;
    private ToggleGroup q4Group;
    private ToggleGroup q5Group;
    private ToggleGroup q6Group;
    private ToggleGroup q7Group;
    private ToggleGroup q8Group;
    private ToggleGroup q9Group;
    private ToggleGroup q10Group;
    private ToggleGroup q11Group;
    private ToggleGroup q12Group;
    private ToggleGroup q13Group;
    private ToggleGroup q14Group;
    private ToggleGroup q15Group;

    @FXML
    public void initialize() {
        clinicComboBox.setEditable(true);
        loadClinicNames();

        q1Group = createToggleGroup(q1YesRadio, q1NoRadio, q1NaRadio);
        q2Group = createToggleGroup(q2YesRadio, q2NoRadio, q2NaRadio);
        q3Group = createToggleGroup(q3YesRadio, q3NoRadio, q3NaRadio);
        q4Group = createToggleGroup(q4YesRadio, q4NoRadio, q4NaRadio);
        q5Group = createToggleGroup(q5YesRadio, q5NoRadio, q5NaRadio);
        q6Group = createToggleGroup(q6YesRadio, q6NoRadio, q6NaRadio);
        q7Group = createToggleGroup(q7YesRadio, q7NoRadio, q7NaRadio);
        q8Group = createToggleGroup(q8YesRadio, q8NoRadio, q8NaRadio);
        q9Group = createToggleGroup(q9YesRadio, q9NoRadio, q9NaRadio);
        q10Group = createToggleGroup(q10YesRadio, q10NoRadio, q10NaRadio);
        q11Group = createToggleGroup(q11YesRadio, q11NoRadio, q11NaRadio);
        q12Group = createToggleGroup(q12YesRadio, q12NoRadio, q12NaRadio);
        q13Group = createToggleGroup(q13YesRadio, q13NoRadio, q13NaRadio);
        q14Group = createToggleGroup(q14YesRadio, q14NoRadio, q14NaRadio);
        q15Group = createToggleGroup(q15YesRadio, q15NoRadio, q15NaRadio);

        assessmentDatePicker.setValue(LocalDate.now());
    }

    private ToggleGroup createToggleGroup(RadioButton yes, RadioButton no, RadioButton na) {
        ToggleGroup group = new ToggleGroup();
        yes.setToggleGroup(group);
        no.setToggleGroup(group);
        na.setToggleGroup(group);
        return group;
    }

    @FXML
    private void saveAssessment() {
        String clinicName = getSelectedClinicName();
        LocalDate assessmentDate = assessmentDatePicker.getValue();

        if (clinicName.isBlank()) {
            showError("Validation Error", "Please select or enter a clinic name.");
            return;
        }

        if (assessmentDate == null) {
            showError("Validation Error", "Please select an assessment date.");
            return;
        }

        String insertSql = """
                INSERT INTO assessments (
                    clinic_name,
                    assessment_date,
                    q1_answer, q2_answer, q3_answer, q4_answer, q5_answer,
                    q6_answer, q7_answer, q8_answer, q9_answer, q10_answer,
                    q11_answer, q12_answer, q13_answer, q14_answer, q15_answer,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """;

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(insertSql)) {

            stmt.setString(1, clinicName);
            stmt.setDate(2, java.sql.Date.valueOf(assessmentDate));

            stmt.setString(3, getSelectedAnswer(q1Group));
            stmt.setString(4, getSelectedAnswer(q2Group));
            stmt.setString(5, getSelectedAnswer(q3Group));
            stmt.setString(6, getSelectedAnswer(q4Group));
            stmt.setString(7, getSelectedAnswer(q5Group));
            stmt.setString(8, getSelectedAnswer(q6Group));
            stmt.setString(9, getSelectedAnswer(q7Group));
            stmt.setString(10, getSelectedAnswer(q8Group));
            stmt.setString(11, getSelectedAnswer(q9Group));
            stmt.setString(12, getSelectedAnswer(q10Group));
            stmt.setString(13, getSelectedAnswer(q11Group));
            stmt.setString(14, getSelectedAnswer(q12Group));
            stmt.setString(15, getSelectedAnswer(q13Group));
            stmt.setString(16, getSelectedAnswer(q14Group));
            stmt.setString(17, getSelectedAnswer(q15Group));
            stmt.setString(18, overallCommentsArea.getText() == null ? "" : overallCommentsArea.getText().trim());

            stmt.executeUpdate();

            showInfo("Saved", "A new assessment instance was saved successfully.");
            loadClinicNames();
            clearForm();

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Database Error", "Could not save the assessment.");
        }
    }

    @FXML
    private void clearForm() {
        clinicComboBox.setValue(null);
        clinicComboBox.getEditor().clear();
        assessmentDatePicker.setValue(LocalDate.now());

        clearToggleGroup(q1Group);
        clearToggleGroup(q2Group);
        clearToggleGroup(q3Group);
        clearToggleGroup(q4Group);
        clearToggleGroup(q5Group);
        clearToggleGroup(q6Group);
        clearToggleGroup(q7Group);
        clearToggleGroup(q8Group);
        clearToggleGroup(q9Group);
        clearToggleGroup(q10Group);
        clearToggleGroup(q11Group);
        clearToggleGroup(q12Group);
        clearToggleGroup(q13Group);
        clearToggleGroup(q14Group);
        clearToggleGroup(q15Group);

        q1CommentArea.clear();
        q2CommentArea.clear();
        q3CommentArea.clear();
        q4CommentArea.clear();
        q5CommentArea.clear();
        q6CommentArea.clear();
        q7CommentArea.clear();
        q8CommentArea.clear();
        q9CommentArea.clear();
        q10CommentArea.clear();
        q11CommentArea.clear();
        q12CommentArea.clear();
        q13CommentArea.clear();
        q14CommentArea.clear();
        q15CommentArea.clear();
        overallCommentsArea.clear();
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
            showError("Database Error", "Could not load clinic names.");
        }
    }

    private String getSelectedClinicName() {
        String value = clinicComboBox.getValue();

        if (value == null || value.isBlank()) {
            value = clinicComboBox.getEditor().getText();
        }

        return value == null ? "" : value.trim();
    }

    private String getSelectedAnswer(ToggleGroup group) {
        if (group == null || group.getSelectedToggle() == null) {
            return null;
        }

        RadioButton selected = (RadioButton) group.getSelectedToggle();
        return selected.getText();
    }

    private void clearToggleGroup(ToggleGroup group) {
        if (group != null) {
            group.selectToggle(null);
        }
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