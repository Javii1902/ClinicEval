package com.clineval.cliniceval;

import com.clineval.cliniceval.config.DbManager;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.geometry.Insets;
import javafx.scene.control.*;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Optional;
import java.util.prefs.BackingStoreException;
import java.util.prefs.Preferences;

public class ClinicPageController {

    private static final String PREF_SKIP_SAVE_CONFIRMATION = "skipClinicSaveConfirmation";

    @FXML
    private ComboBox<String> clinicComboBox;

    @FXML
    private ComboBox<AssessmentOption> assessmentDateComboBox;

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
    private final Preferences preferences = Preferences.userNodeForPackage(ClinicPageController.class);

    private Integer loadedAssessmentId;
    private boolean skipSaveConfirmation;

    @FXML
    public void initialize() {
        skipSaveConfirmation = preferences.getBoolean(PREF_SKIP_SAVE_CONFIRMATION, false);

        clinicComboBox.setEditable(true);
        assessmentDateComboBox.setEditable(false);

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
                if (getIndex() >= 0 && getIndex() < getTableView().getItems().size()) {
                    ClinicRecord record = getTableView().getItems().get(getIndex());
                    record.setAnswer(value);
                    updateComplianceLabel();
                }
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

        clinicComboBox.setOnAction(e -> loadAssessmentOptionsForClinic());

        assessmentDateComboBox.setOnAction(e -> {
            AssessmentOption selected = assessmentDateComboBox.getValue();
            if (selected != null) {
                loadAssessmentById(selected.getAssessmentId());
            }
        });
    }

    @FXML
    private void loadClinic() {
        String clinicName = getSelectedClinicName();

        if (clinicName.isBlank()) {
            showError("Validation Error", "Please select or enter a clinic name.");
            return;
        }

        AssessmentOption selectedOption = assessmentDateComboBox.getValue();
        if (selectedOption == null) {
            showError("Validation Error", "Please select an assessment instance.");
            return;
        }

        loadAssessmentById(selectedOption.getAssessmentId());
    }

    private void loadAssessmentOptionsForClinic() {
        String clinicName = getSelectedClinicName();

        Integer previouslySelectedId = null;
        AssessmentOption currentSelection = assessmentDateComboBox.getValue();
        if (currentSelection != null) {
            previouslySelectedId = currentSelection.getAssessmentId();
        }

        assessmentDateComboBox.getItems().clear();
        assessmentDateComboBox.setValue(null);

        if (clinicName.isBlank()) {
            return;
        }

        String sql = """
            SELECT id, assessment_date
            FROM assessments
            WHERE LOWER(clinic_name) = LOWER(?)
            ORDER BY assessment_date DESC, id DESC
            """;

        ObservableList<AssessmentOption> options = FXCollections.observableArrayList();

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, clinicName);

            try (ResultSet rs = stmt.executeQuery()) {
                int instanceNumber = 0;
                String previousDate = null;

                while (rs.next()) {
                    int assessmentId = rs.getInt("id");
                    String assessmentDate = String.valueOf(rs.getDate("assessment_date"));

                    if (!assessmentDate.equals(previousDate)) {
                        instanceNumber = 1;
                        previousDate = assessmentDate;
                    } else {
                        instanceNumber++;
                    }

                    String displayLabel = assessmentDate + " (Instance " + instanceNumber + ")";
                    options.add(new AssessmentOption(assessmentId, assessmentDate, displayLabel));
                }
            }

            assessmentDateComboBox.setItems(options);

            if (!options.isEmpty()) {
                boolean restored = false;

                if (previouslySelectedId != null) {
                    for (AssessmentOption option : options) {
                        if (option.getAssessmentId() == previouslySelectedId) {
                            assessmentDateComboBox.setValue(option);
                            restored = true;
                            break;
                        }
                    }
                }

                if (!restored) {
                    assessmentDateComboBox.setValue(options.get(0));
                }
            }

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Database Error", "Could not load assessment instances.");
        }
    }

    private void loadAssessmentById(int assessmentId) {
        String sql = """
                SELECT *
                FROM assessments
                WHERE id = ?
                """;

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setInt(1, assessmentId);

            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    loadedAssessmentId = rs.getInt("id");

                    String actualClinicName = rs.getString("clinic_name");
                    String actualAssessmentDate = String.valueOf(rs.getDate("assessment_date"));

                    loadedClinicLabel.setText(actualClinicName);
                    assessmentDateLabel.setText(actualAssessmentDate);
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

                    selectAssessmentOptionById(assessmentId);
                    updateComplianceLabel();
                } else {
                    clearClinicView();
                    showInfo("Not Found", "No assessment found for that selection.");
                }
            }

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Database Error", "Could not load clinic data.");
        }
    }

    private void selectAssessmentOptionById(int assessmentId) {
        for (AssessmentOption option : assessmentDateComboBox.getItems()) {
            if (option.getAssessmentId() == assessmentId) {
                assessmentDateComboBox.setValue(option);
                break;
            }
        }
    }

    @FXML
    private void saveChanges() {
        if (loadedAssessmentId == null) {
            showError("Save Error", "Please load a clinic before saving changes.");
            return;
        }

        if (!skipSaveConfirmation) {
            boolean confirmed = showSaveConfirmationDialog();
            if (!confirmed) {
                return;
            }
        }

        String updateSql = """
                UPDATE assessments
                SET q1_answer = ?,
                    q2_answer = ?,
                    q3_answer = ?,
                    q4_answer = ?,
                    q5_answer = ?,
                    q6_answer = ?,
                    q7_answer = ?,
                    q8_answer = ?,
                    q9_answer = ?,
                    q10_answer = ?,
                    q11_answer = ?,
                    q12_answer = ?,
                    q13_answer = ?,
                    q14_answer = ?,
                    q15_answer = ?,
                    notes = ?
                WHERE id = ?
                """;

        try (Connection conn = DbManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(updateSql)) {

            stmt.setString(1, getAnswerByIndex(0));
            stmt.setString(2, getAnswerByIndex(1));
            stmt.setString(3, getAnswerByIndex(2));
            stmt.setString(4, getAnswerByIndex(3));
            stmt.setString(5, getAnswerByIndex(4));
            stmt.setString(6, getAnswerByIndex(5));
            stmt.setString(7, getAnswerByIndex(6));
            stmt.setString(8, getAnswerByIndex(7));
            stmt.setString(9, getAnswerByIndex(8));
            stmt.setString(10, getAnswerByIndex(9));
            stmt.setString(11, getAnswerByIndex(10));
            stmt.setString(12, getAnswerByIndex(11));
            stmt.setString(13, getAnswerByIndex(12));
            stmt.setString(14, getAnswerByIndex(13));
            stmt.setString(15, getAnswerByIndex(14));
            stmt.setString(16, notesArea.getText() == null ? "" : notesArea.getText().trim());
            stmt.setInt(17, loadedAssessmentId);

            stmt.executeUpdate();
            showInfo("Saved", "Clinic changes were saved successfully.");

            loadAssessmentOptionsForClinic();
            selectAssessmentOptionById(loadedAssessmentId);
            loadAssessmentById(loadedAssessmentId);

        } catch (SQLException e) {
            e.printStackTrace();
            showError("Database Error", "Could not save clinic changes.");
        }
    }

    private boolean showSaveConfirmationDialog() {
        Alert alert = new Alert(Alert.AlertType.CONFIRMATION);
        alert.setTitle("Confirm Save");
        alert.setHeaderText("Save clinic changes?");
        alert.setContentText("Are you sure you want to save the changes made to this clinic assessment?");

        CheckBox dontShowAgainCheckBox = new CheckBox("Do not show this notification again");

        VBox content = new VBox(12);
        content.setPadding(new Insets(10, 0, 0, 0));
        content.getChildren().add(dontShowAgainCheckBox);

        alert.getDialogPane().setExpandableContent(content);
        alert.getDialogPane().setExpanded(true);

        Optional<ButtonType> result = alert.showAndWait();

        if (dontShowAgainCheckBox.isSelected()) {
            skipSaveConfirmation = true;
            preferences.putBoolean(PREF_SKIP_SAVE_CONFIRMATION, true);
            flushPreferences();
        }

        return result.isPresent() && result.get() == ButtonType.OK;
    }

    private void flushPreferences() {
        try {
            preferences.flush();
        } catch (BackingStoreException e) {
            e.printStackTrace();
        }
    }

    private String getAnswerByIndex(int index) {
        if (index < 0 || index >= records.size()) {
            return null;
        }

        String value = records.get(index).getAnswer();
        return (value == null || value.isBlank()) ? null : value;
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

    private void clearClinicView() {
        loadedAssessmentId = null;
        records.clear();
        loadedClinicLabel.setText("-");
        assessmentDateLabel.setText("-");
        notesArea.clear();
        complianceLabel.setText("Compliance: -");
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