package com.clineval.cliniceval;

import javafx.beans.property.SimpleStringProperty;
import javafx.beans.property.StringProperty;

public class DashboardClinicRow {

    private final StringProperty clinicName = new SimpleStringProperty();
    private final StringProperty compliancePercentage = new SimpleStringProperty();
    private final StringProperty yesCount = new SimpleStringProperty();
    private final StringProperty noCount = new SimpleStringProperty();
    private final StringProperty naCount = new SimpleStringProperty();

    public DashboardClinicRow(String clinicName, String compliancePercentage, String yesCount, String noCount, String naCount) {
        this.clinicName.set(clinicName);
        this.compliancePercentage.set(compliancePercentage);
        this.yesCount.set(yesCount);
        this.noCount.set(noCount);
        this.naCount.set(naCount);
    }

    public StringProperty clinicNameProperty() {
        return clinicName;
    }

    public StringProperty compliancePercentageProperty() {
        return compliancePercentage;
    }

    public StringProperty yesCountProperty() {
        return yesCount;
    }

    public StringProperty noCountProperty() {
        return noCount;
    }

    public StringProperty naCountProperty() {
        return naCount;
    }

    public String getClinicName() {
        return clinicName.get();
    }

    public String getCompliancePercentage() {
        return compliancePercentage.get();
    }

    public String getYesCount() {
        return yesCount.get();
    }

    public String getNoCount() {
        return noCount.get();
    }

    public String getNaCount() {
        return naCount.get();
    }
}