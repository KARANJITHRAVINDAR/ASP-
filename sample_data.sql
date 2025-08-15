-- sample_data.sql
USE hospital_ai_dashboard;

INSERT INTO `predictions` 
(`patientId`, `patientName`, `admissionDate`, `age`, `admissionType`, `priorAdmissions`, `surgeryMethod`, `albumin`, `hemoglobin`, `hasSepsis`, `hasDelirium`, `hasMalignancy`, `hasDiabetes`, `hasCHF`, `hasCKD`, `hasCOPD`, `hasStroke`, `hasLiverDisease`, `predicted_los`, `riskScore`, `riskLevel`) 
VALUES
('MRN12345', 'John Smith', '2025-08-11', 72, 1, 3, 2, 3.1, 11.5, 1, 0, 0, 1, 1, 0, 1, 0, 0, 11, 85, 'High'),
('MRN67890', 'Maria Garcia', '2025-08-10', 55, 2, 0, 1, 4.2, 13.8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 8, 62, 'Moderate'),
('MRN54321', 'Emily White', '2025-08-12', 45, 2, 1, 1, 4.5, 14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 30, 'Low'),
('MRN98765', 'David Chen', '2025-08-09', 81, 1, 5, 2, 2.9, 10.1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 14, 98, 'High');