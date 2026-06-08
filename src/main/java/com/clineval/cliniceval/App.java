package com.clineval.cliniceval;

import com.clineval.cliniceval.config.SchemaInitializer;
import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Scene;
import javafx.stage.Stage;

import java.net.URL;

public class App extends Application {

    @Override
    public void start(Stage stage) throws Exception {
        SchemaInitializer.initialize();

        URL fxmlUrl = App.class.getResource("/com/clineval/cliniceval/fxml/MainLayout.fxml");
        URL cssUrl = App.class.getResource("/com/clineval/cliniceval/css/main.css");

        if (fxmlUrl == null) {
            throw new IllegalStateException("Cannot find FXML file: /com/clineval/cliniceval/fxml/MainLayout.fxml");
        }

        if (cssUrl == null) {
            throw new IllegalStateException("Cannot find CSS file: /com/clineval/cliniceval/css/main.css");
        }

        FXMLLoader loader = new FXMLLoader(fxmlUrl);
        Scene scene = new Scene(loader.load(), 1100, 700);
        scene.getStylesheets().add(cssUrl.toExternalForm());

        stage.setTitle("Clinic Evaluation");
        stage.setMinWidth(1000);
        stage.setMinHeight(650);
        stage.setScene(scene);
        stage.show();
    }
}