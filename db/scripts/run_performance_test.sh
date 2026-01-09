#!/bin/bash
# Script to run inside DB2 container to execute queries and measure performance

echo "=============================================="
echo "DB2 Query Performance Comparison"
echo "=============================================="
echo ""

# Connect to database
db2 connect to LOANDB

echo ""
echo "Creating schema and tables..."
echo ""

# Create tables
db2 << EOF
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
)
EOF

db2 << EOF
CREATE TABLE approvers_l1 (
    approver_id INT NOT NULL PRIMARY KEY,
    approver_name VARCHAR(200),
    department VARCHAR(100),
    max_approval_limit DECIMAL(15,2),
    active_flag CHAR(1) DEFAULT 'Y',
    region VARCHAR(50)
)
EOF

db2 << EOF
CREATE TABLE approvers_l2 (
    approver_id INT NOT NULL PRIMARY KEY,
    approver_name VARCHAR(200),
    department VARCHAR(100),
    max_approval_limit DECIMAL(15,2),
    active_flag CHAR(1) DEFAULT 'Y',
    region VARCHAR(50),
    seniority_level INT
)
EOF

# Create indexes
db2 "CREATE INDEX idx_loan_status ON loan_applications(status)"
db2 "CREATE INDEX idx_loan_level ON loan_applications(approval_level)"
db2 "CREATE INDEX idx_loan_approver ON loan_applications(current_approver_id)"
db2 "CREATE INDEX idx_l1_active ON approvers_l1(active_flag)"
db2 "CREATE INDEX idx_l1_region ON approvers_l1(region)"
db2 "CREATE INDEX idx_l2_active ON approvers_l2(active_flag)"
db2 "CREATE INDEX idx_l2_region ON approvers_l2(region)"

echo ""
echo "Populating test data (simplified - 10,000 records per table)..."
echo ""

# Populate approvers_l1
for i in {1..10000}
do
    db2 "INSERT INTO approvers_l1 VALUES ($i, 'Approver L1 $i', 'Finance', 500000, 'Y', 'North')"
    if [ $((i % 1000)) -eq 0 ]; then
        echo "Inserted $i L1 approvers..."
        db2 commit
    fi
done
db2 commit

# Populate approvers_l2
for i in {1..10000}
do
    db2 "INSERT INTO approvers_l2 VALUES ($i, 'Approver L2 $i', 'Finance', 2500000, 'Y', 'North', 2)"
    if [ $((i % 1000)) -eq 0 ]; then
        echo "Inserted $i L2 approvers..."
        db2 commit
    fi
done
db2 commit

# Populate loan_applications
for i in {1..10000}
do
    approver=$((RANDOM % 10000 + 1))
    amount=$((RANDOM % 1000000 + 10000))
    db2 "INSERT INTO loan_applications VALUES ($i, 'Applicant $i', $amount, CURRENT_DATE, 'PENDING', $approver, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    if [ $((i % 1000)) -eq 0 ]; then
        echo "Inserted $i loan applications..."
        db2 commit
    fi
done
db2 commit

echo ""
echo "Data population complete!"
echo ""
db2 "SELECT COUNT(*) as loan_count FROM loan_applications"
db2 "SELECT COUNT(*) as l1_count FROM approvers_l1"
db2 "SELECT COUNT(*) as l2_count FROM approvers_l2"

echo ""
echo "=============================================="
echo "TEST 1: UPDATE with Subquery (INNER JOIN)"
echo "=============================================="
echo ""

# Run UPDATE query with timing
START_TIME=$(date +%s%N)

db2 << EOF
UPDATE loan_applications L
SET 
    current_approver_id = (
        SELECT L2.approver_id
        FROM approvers_l1 L1
        INNER JOIN approvers_l2 L2 
            ON L1.department = L2.department 
            AND L1.region = L2.region
        WHERE L1.active_flag = 'Y' 
            AND L2.active_flag = 'Y'
            AND L2.max_approval_limit >= L.loan_amount
            AND L1.approver_id = L.current_approver_id
        FETCH FIRST 1 ROW ONLY
    ),
    updated_at = CURRENT_TIMESTAMP
WHERE L.status = 'PENDING'
    AND L.approval_level = 1
    AND EXISTS (
        SELECT 1
        FROM approvers_l1 L1
        INNER JOIN approvers_l2 L2 
            ON L1.department = L2.department 
            AND L1.region = L2.region
        WHERE L1.active_flag = 'Y' 
            AND L2.active_flag = 'Y'
            AND L2.max_approval_limit >= L.loan_amount
            AND L1.approver_id = L.current_approver_id
    )
EOF

db2 commit

END_TIME=$(date +%s%N)
ELAPSED_UPDATE=$((($END_TIME - $START_TIME) / 1000000))

echo ""
echo "UPDATE Query Duration: ${ELAPSED_UPDATE} milliseconds"
echo ""

# Reset data for second test
echo "Resetting data for next test..."
db2 << EOF
UPDATE loan_applications
SET 
    status = 'PENDING',
    approval_level = 1,
    current_approver_id = (
        SELECT approver_id 
        FROM approvers_l1 
        WHERE active_flag = 'Y' 
        FETCH FIRST 1 ROW ONLY
    )
WHERE application_id % 10 = 0
EOF
db2 commit

echo ""
echo "=============================================="
echo "TEST 2: MERGE Statement"
echo "=============================================="
echo ""

# Run MERGE query with timing
START_TIME=$(date +%s%N)

db2 << EOF
MERGE INTO loan_applications AS L
USING (
    SELECT 
        L1.approver_id as l1_approver_id,
        L2.approver_id as l2_approver_id,
        L1.department,
        L1.region,
        L2.max_approval_limit
    FROM approvers_l1 L1
    INNER JOIN approvers_l2 L2 
        ON L1.department = L2.department 
        AND L1.region = L2.region
    WHERE L1.active_flag = 'Y' 
        AND L2.active_flag = 'Y'
) AS approvers
ON L.current_approver_id = approvers.l1_approver_id
    AND L.loan_amount <= approvers.max_approval_limit
    AND L.status = 'PENDING'
    AND L.approval_level = 1
WHEN MATCHED THEN
    UPDATE SET 
        current_approver_id = approvers.l2_approver_id,
        updated_at = CURRENT_TIMESTAMP
EOF

db2 commit

END_TIME=$(date +%s%N)
ELAPSED_MERGE=$((($END_TIME - $START_TIME) / 1000000))

echo ""
echo "MERGE Query Duration: ${ELAPSED_MERGE} milliseconds"
echo ""

echo "=============================================="
echo "PERFORMANCE COMPARISON RESULTS"
echo "=============================================="
echo ""
echo "UPDATE with Subquery: ${ELAPSED_UPDATE} ms"
echo "MERGE Statement:      ${ELAPSED_MERGE} ms"
echo ""

if [ $ELAPSED_UPDATE -gt $ELAPSED_MERGE ]; then
    DIFF=$((ELAPSED_UPDATE - ELAPSED_MERGE))
    PERCENT=$((100 * DIFF / ELAPSED_UPDATE))
    echo "WINNER: MERGE is FASTER by ${DIFF} ms (${PERCENT}% faster)"
else
    DIFF=$((ELAPSED_MERGE - ELAPSED_UPDATE))
    PERCENT=$((100 * DIFF / ELAPSED_MERGE))
    echo "WINNER: UPDATE is FASTER by ${DIFF} ms (${PERCENT}% faster)"
fi

echo ""
echo "=============================================="

db2 disconnect
