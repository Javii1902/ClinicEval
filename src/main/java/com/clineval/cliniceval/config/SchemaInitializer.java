package com.clineval.cliniceval.config;

import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;

public class SchemaInitializer {

    public static void initialize() {
        String createTableSql = """
                CREATE TABLE IF NOT EXISTS assessments (
                    id IDENTITY PRIMARY KEY,
                    clinic_name VARCHAR(255) NOT NULL,
                    q1_answer VARCHAR(10),
                    q2_answer VARCHAR(10),
                    q3_answer VARCHAR(10),
                    q4_answer VARCHAR(10),
                    q5_answer VARCHAR(10),
                    q6_answer VARCHAR(10),
                    q7_answer VARCHAR(10),
                    q8_answer VARCHAR(10),
                    q9_answer VARCHAR(10),
                    q10_answer VARCHAR(10),
                    q11_answer VARCHAR(10),
                    q12_answer VARCHAR(10),
                    q13_answer VARCHAR(10),
                    q14_answer VARCHAR(10),
                    q15_answer VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """;

        String addAssessmentDateSql = """
                ALTER TABLE assessments
                ADD COLUMN IF NOT EXISTS assessment_date DATE
                """;

        String fillAssessmentDateSql = """
                UPDATE assessments
                SET assessment_date = CURRENT_DATE
                WHERE assessment_date IS NULL
                """;

        String setAssessmentDateNotNullSql = """
                ALTER TABLE assessments
                ALTER COLUMN assessment_date SET NOT NULL
                """;

        String addNotesSql = """
                ALTER TABLE assessments
                ADD COLUMN IF NOT EXISTS notes CLOB
                """;

        try (Connection conn = DbManager.getConnection();
             Statement stmt = conn.createStatement()) {

            stmt.execute(createTableSql);
            stmt.execute(addAssessmentDateSql);
            stmt.execute(fillAssessmentDateSql);
            stmt.execute(setAssessmentDateNotNullSql);
            stmt.execute(addNotesSql);

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}