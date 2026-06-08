package com.clineval.cliniceval;

import javafx.beans.property.SimpleStringProperty;
import javafx.beans.property.StringProperty;

public class ClinicRecord {

    private final StringProperty question = new SimpleStringProperty();
    private final StringProperty answer = new SimpleStringProperty();

    public ClinicRecord(String question, String answer) {
        this.question.set(question);
        this.answer.set(answer);
    }

    public String getQuestion() {
        return question.get();
    }

    public void setQuestion(String value) {
        question.set(value);
    }

    public StringProperty questionProperty() {
        return question;
    }

    public String getAnswer() {
        return answer.get();
    }

    public void setAnswer(String value) {
        answer.set(value);
    }

    public StringProperty answerProperty() {
        return answer;
    }
}