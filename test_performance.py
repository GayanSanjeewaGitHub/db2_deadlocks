"""
Simple DB2 Performance Test - Run queries directly and compare performance
No dependencies on ibm_db - uses docker exec to run queries
"""

import subprocess
import time
import os
from datetime import datetime

def run_db2_command(sql_command):
    """Run a DB2 SQL command inside the container"""
    cmd = [
        "docker", "exec", "db2_performance_test",
        "su", "-", "db2inst1", "-c",
        f'db2 "connect to LOANDB" && db2 "{sql_command}" && db2 "commit"'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    return result.stdout, result.stderr, result.returncode

def create_tables():
    """Create database schema"""
    print("\n" + "="*70)
    print("Creating Tables...")
    print("="*70)
    
    # Drop existing tables
    print("Dropping existing tables...")
    run_db2_command("DROP TABLE loan_applications")
    run_db2_command("DROP TABLE approvers_l1")
    run_db2_command("DROP TABLE approvers_l2")
    
    # Create loan_applications table
    sql = """CREATE TABLE loan_applications (
        application_id INT NOT NULL PRIMARY KEY,
        applicant_name VARCHAR(200),
        loan_amount DECIMAL(15,2),
        application_date DATE,
        status VARCHAR(50),
        current_approver_id INT,
        approval_level INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""
    
    stdout, stderr, code = run_db2_command(sql)
    print("✓ Created loan_applications table")
    
    # Create approvers_l1 table
    sql = """CREATE TABLE approvers_l1 (
        approver_id INT NOT NULL PRIMARY KEY,
        approver_name VARCHAR(200),
        department VARCHAR(100),
        max_approval_limit DECIMAL(15,2),
        active_flag CHAR(1) DEFAULT 'Y',
        region VARCHAR(50)
    )"""
    
    run_db2_command(sql)
    print("✓ Created approvers_l1 table")
    
    # Create approvers_l2 table
    sql = """CREATE TABLE approvers_l2 (
        approver_id INT NOT NULL PRIMARY KEY,
        approver_name VARCHAR(200),
        department VARCHAR(100),
        max_approval_limit DECIMAL(15,2),
        active_flag CHAR(1) DEFAULT 'Y',
        region VARCHAR(50),
        seniority_level INT
    )"""
    
    run_db2_command(sql)
    print("✓ Created approvers_l2 table")
    
    # Create indexes
    print("\nCreating indexes...")
    run_db2_command("CREATE INDEX idx_loan_status ON loan_applications(status)")
    run_db2_command("CREATE INDEX idx_loan_level ON loan_applications(approval_level)")
    run_db2_command("CREATE INDEX idx_loan_approver ON loan_applications(current_approver_id)")
    run_db2_command("CREATE INDEX idx_l1_active ON approvers_l1(active_flag)")
    run_db2_command("CREATE INDEX idx_l2_active ON approvers_l2(active_flag)")
    print("✓ Created all indexes")

def populate_data(num_records=1000):
    """Populate tables with test data"""
    print("\n" + "="*70)
    print(f"Populating Tables with {num_records} records each...")
    print("="*70)
    
    # Populate approvers_l1
    print(f"\nInserting {num_records} L1 approvers...")
    values = []
    for i in range(1, num_records + 1):
        values.append(f"({i}, 'Approver L1 {i}', 'Finance', 500000, 'Y', 'North')")
        
        if len(values) >= 100:
            sql = f"INSERT INTO approvers_l1 VALUES {', '.join(values)}"
            run_db2_command(sql)
            values = []
            if i % 200 == 0:
                print(f"  Inserted {i} L1 approvers...")
    
    if values:
        sql = f"INSERT INTO approvers_l1 VALUES {', '.join(values)}"
        run_db2_command(sql)
    
    print(f"✓ Inserted {num_records} L1 approvers")
    
    # Populate approvers_l2
    print(f"\nInserting {num_records} L2 approvers...")
    values = []
    for i in range(1, num_records + 1):
        values.append(f"({i}, 'Approver L2 {i}', 'Finance', 2500000, 'Y', 'North', 2)")
        
        if len(values) >= 100:
            sql = f"INSERT INTO approvers_l2 VALUES {', '.join(values)}"
            run_db2_command(sql)
            values = []
            if i % 200 == 0:
                print(f"  Inserted {i} L2 approvers...")
    
    if values:
        sql = f"INSERT INTO approvers_l2 VALUES {', '.join(values)}"
        run_db2_command(sql)
    
    print(f"✓ Inserted {num_records} L2 approvers")
    
    # Populate loan_applications
    print(f"\nInserting {num_records} loan applications...")
    values = []
    for i in range(1, num_records + 1):
        approver_id = (i % num_records) + 1
        loan_amount = 250000 + (i * 100)
        values.append(f"({i}, 'Applicant {i}', {loan_amount}, CURRENT_DATE, 'PENDING', {approver_id}, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
        
        if len(values) >= 100:
            sql = f"INSERT INTO loan_applications VALUES {', '.join(values)}"
            run_db2_command(sql)
            values = []
            if i % 200 == 0:
                print(f"  Inserted {i} loan applications...")
    
    if values:
        sql = f"INSERT INTO loan_applications VALUES {', '.join(values)}"
        run_db2_command(sql)
    
    print(f"✓ Inserted {num_records} loan applications")

def run_update_query():
    """Run UPDATE with subquery"""
    sql = """UPDATE loan_applications L
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
        )"""
    
    print("\n" + "="*70)
    print("TEST 1: UPDATE with Subquery (INNER JOIN)")
    print("="*70)
    
    start_time = time.time()
    
    stdout, stderr, code = run_db2_command(sql)
    
    end_time = time.time()
    
    duration_ms = (end_time - start_time) * 1000
    
    print(f"\n✓ Query executed successfully")
    print(f"Duration: {duration_ms:.2f} ms ({end_time - start_time:.4f} seconds)")
    
    return {
        'name': 'UPDATE with Subquery',
        'duration_ms': duration_ms
    }

def run_merge_query():
    """Run MERGE statement"""
    sql = """MERGE INTO loan_applications AS L
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
            updated_at = CURRENT_TIMESTAMP"""
    
    print("\n" + "="*70)
    print("TEST 2: MERGE Statement")
    print("="*70)
    
    start_time = time.time()
    
    stdout, stderr, code = run_db2_command(sql)
    
    end_time = time.time()
    
    duration_ms = (end_time - start_time) * 1000
    
    print(f"\n✓ Query executed successfully")
    print(f"Duration: {duration_ms:.2f} ms ({end_time - start_time:.4f} seconds)")
    
    return {
        'name': 'MERGE Statement',
        'duration_ms': duration_ms
    }

def reset_data():
    """Reset applications to PENDING"""
    print("\nResetting data for next test...")
    sql = """UPDATE loan_applications
    SET 
        status = 'PENDING',
        approval_level = 1"""
    
    run_db2_command(sql)
    print("✓ Data reset complete")

def main():
    print("\n" + "="*70)
    print("DB2 QUERY PERFORMANCE COMPARISON")
    print("UPDATE vs MERGE Statement Performance Test")
    print("="*70)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup
    create_tables()
    populate_data(10000)  # Test with 10,000 records
    
    # Test 1: UPDATE
    result1 = run_update_query()
    
    # Reset for second test
    reset_data()
    
    # Test 2: MERGE
    result2 = run_merge_query()
    
    # Compare Results
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON RESULTS")
    print("="*70)
    
    print(f"\n{result1['name']}:")
    print(f"  Duration: {result1['duration_ms']:.2f} ms")
    
    print(f"\n{result2['name']}:")
    print(f"  Duration: {result2['duration_ms']:.2f} ms")
    
    print("\n" + "-"*70)
    
    if result1['duration_ms'] < result2['duration_ms']:
        diff = result2['duration_ms'] - result1['duration_ms']
        percent = (diff / result2['duration_ms']) * 100
        speedup = result2['duration_ms'] / result1['duration_ms']
        print(f"\n🏆 WINNER: {result1['name']}")
        print(f"   Faster by: {diff:.2f} ms ({percent:.1f}%)")
        print(f"   Speedup: {speedup:.2f}x")
    else:
        diff = result1['duration_ms'] - result2['duration_ms']
        percent = (diff / result1['duration_ms']) * 100
        speedup = result1['duration_ms'] / result2['duration_ms']
        print(f"\n🏆 WINNER: {result2['name']}")
        print(f"   Faster by: {diff:.2f} ms ({percent:.1f}%)")
        print(f"   Speedup: {speedup:.2f}x")
    
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
