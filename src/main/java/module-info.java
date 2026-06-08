module com.clineval.cliniceval {
    requires javafx.controls;
    requires javafx.fxml;
    requires java.sql;
    requires java.prefs;

    requires org.apache.poi.poi;
    requires org.apache.poi.ooxml;
    requires org.apache.commons.compress;
    requires org.apache.commons.collections4;
    requires org.apache.xmlbeans;

    opens com.clineval.cliniceval to javafx.fxml;
    opens com.clineval.cliniceval.config to javafx.fxml;

    exports com.clineval.cliniceval;
    exports com.clineval.cliniceval.config;
}