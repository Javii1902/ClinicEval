module com.clineval.cliniceval {
    requires javafx.controls;
    requires javafx.fxml;
    requires java.sql;
    requires com.h2database;

    opens com.clineval.cliniceval to javafx.fxml;
    exports com.clineval.cliniceval;

    exports com.clineval.cliniceval.config;
}