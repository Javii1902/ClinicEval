package com.clineval.cliniceval;

public class AssessmentOption {

    private final int assessmentId;
    private final String assessmentDate;
    private final String displayLabel;

    public AssessmentOption(int assessmentId, String assessmentDate, String displayLabel) {
        this.assessmentId = assessmentId;
        this.assessmentDate = assessmentDate;
        this.displayLabel = displayLabel;
    }

    public int getAssessmentId() {
        return assessmentId;
    }

    public String getAssessmentDate() {
        return assessmentDate;
    }

    public String getDisplayLabel() {
        return displayLabel;
    }

    @Override
    public String toString() {
        return displayLabel;
    }
}