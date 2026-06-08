package com.clineval.cliniceval;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Node;
import javafx.scene.control.Alert;
import javafx.scene.layout.StackPane;

import java.io.IOException;
import java.net.URL;

public class MainLayoutController {

    @FXML
    private StackPane contentArea;

    @FXML
    public void initialize() {
        showHome();
    }

    @FXML
    private void showHome() {
        loadCenterView("/com/clineval/cliniceval/fxml/WelcomeContent.fxml");
    }

    @FXML
    private void showNewAssessment() {
        loadCenterView("/com/clineval/cliniceval/fxml/NewAssessment.fxml");
    }

    @FXML
    private void showClinics() {
        loadCenterView("/com/clineval/cliniceval/fxml/ClinicPage.fxml");
    }

    @FXML
    private void showDashboard() {
        loadCenterView("/com/clineval/cliniceval/fxml/DashboardPage.fxml");
    }

    private void loadCenterView(String fxmlPath) {
        try {
            URL resource = App.class.getResource(fxmlPath);

            if (resource == null) {
                showError("Navigation Error", "Could not find view: " + fxmlPath);
                return;
            }

            FXMLLoader loader = new FXMLLoader(resource);
            Node view = loader.load();
            contentArea.getChildren().setAll(view);

        } catch (IOException e) {
            e.printStackTrace();
            showError("Navigation Error", "Could not load view: " + fxmlPath);
        }
    }

    private void showError(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }
}