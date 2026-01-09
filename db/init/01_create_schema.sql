-- Schema for Loan Approval System
-- Three tables: loan_applications (L), approvers_l1, approvers_l2

-- Main loan applications table
CREATE TABLE loan_applications (
    application_id INT NOT NULL PRIMARY KEY,
    applicant_name VARCHAR(200),
    loan_amount DECIMAL(15,2),
    application_date DATE,
    status VARCHAR(50),
    current_approver_id INT,
    approval_level INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- L1 Approvers table (first level approvers)
CREATE TABLE approvers_l1 (
    approver_id INT NOT NULL PRIMARY KEY,
    approver_name VARCHAR(200),
    department VARCHAR(100),
    max_approval_limit DECIMAL(15,2),
    active_flag CHAR(1) DEFAULT 'Y',
    region VARCHAR(50)
);

-- L2 Approvers table (second level approvers)
CREATE TABLE approvers_l2 (
    approver_id INT NOT NULL PRIMARY KEY,
    approver_name VARCHAR(200),
    department VARCHAR(100),
    max_approval_limit DECIMAL(15,2),
    active_flag CHAR(1) DEFAULT 'Y',
    region VARCHAR(50),
    seniority_level INT
);

-- Create indexes for better performance
CREATE INDEX idx_loan_status ON loan_applications(status);
CREATE INDEX idx_loan_level ON loan_applications(approval_level);
CREATE INDEX idx_loan_approver ON loan_applications(current_approver_id);
CREATE INDEX idx_l1_active ON approvers_l1(active_flag);
CREATE INDEX idx_l1_region ON approvers_l1(region);
CREATE INDEX idx_l2_active ON approvers_l2(active_flag);
CREATE INDEX idx_l2_region ON approvers_l2(region);

-- Grant permissions
GRANT ALL ON loan_applications TO PUBLIC;
GRANT ALL ON approvers_l1 TO PUBLIC;
GRANT ALL ON approvers_l2 TO PUBLIC;
