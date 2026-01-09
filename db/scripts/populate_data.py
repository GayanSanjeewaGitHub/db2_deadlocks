"""
Data Population Script for Loan Approval System
Generates 100,000 records for each table with realistic data
"""

import ibm_db
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_HOST = os.getenv('DB2_HOST', 'localhost')
DB_PORT = os.getenv('DB2_PORT', '50000')
DB_DATABASE = os.getenv('DB2_DATABASE', 'LOANDB')
DB_USER = os.getenv('DB2_USER', 'db2inst1')
DB_PASSWORD = os.getenv('DB2_PASSWORD', 'db2admin123')

# Sample data for generating realistic records
FIRST_NAMES = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 
               'William', 'Jennifer', 'James', 'Mary', 'Christopher', 'Patricia', 'Daniel',
               'Linda', 'Matthew', 'Barbara', 'Anthony', 'Susan', 'Mark', 'Jessica', 'Donald',
               'Karen', 'Steven', 'Nancy', 'Paul', 'Betty', 'Andrew', 'Margaret']

LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
              'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
              'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
              'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'Hall']

DEPARTMENTS = ['Finance', 'Operations', 'Risk Management', 'Credit Analysis', 'Compliance',
               'Business Development', 'Customer Service', 'Legal', 'Audit', 'Collections']

REGIONS = ['North', 'South', 'East', 'West', 'Central', 'Northeast', 'Southeast', 'Northwest', 'Southwest']

STATUSES = ['PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'ON_HOLD']


def get_db_connection():
    """Establish connection to DB2 database"""
    dsn = f"DATABASE={DB_DATABASE};HOSTNAME={DB_HOST};PORT={DB_PORT};PROTOCOL=TCPIP;UID={DB_USER};PWD={DB_PASSWORD};"
    try:
        conn = ibm_db.connect(dsn, "", "")
        print("✓ Connected to DB2 database successfully!")
        return conn
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return None


def populate_approvers_l1(conn, num_records=100000):
    """Populate approvers_l1 table with 100k records"""
    print(f"\nPopulating approvers_l1 table with {num_records:,} records...")
    
    # Clear existing data
    ibm_db.exec_immediate(conn, "DELETE FROM approvers_l1")
    ibm_db.exec_immediate(conn, "COMMIT")
    
    batch_size = 1000
    inserted = 0
    
    for batch_start in range(1, num_records + 1, batch_size):
        values = []
        for i in range(batch_start, min(batch_start + batch_size, num_records + 1)):
            approver_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            department = random.choice(DEPARTMENTS)
            max_limit = random.choice([50000, 100000, 250000, 500000, 1000000])
            active = 'Y' if random.random() > 0.1 else 'N'  # 90% active
            region = random.choice(REGIONS)
            
            values.append(f"({i}, '{approver_name}', '{department}', {max_limit}, '{active}', '{region}')")
        
        sql = f"""
        INSERT INTO approvers_l1 (approver_id, approver_name, department, max_approval_limit, active_flag, region)
        VALUES {', '.join(values)}
        """
        
        try:
            ibm_db.exec_immediate(conn, sql)
            ibm_db.exec_immediate(conn, "COMMIT")
            inserted += len(values)
            if inserted % 10000 == 0:
                print(f"  Inserted {inserted:,} records...")
        except Exception as e:
            print(f"  Error inserting batch: {e}")
            ibm_db.exec_immediate(conn, "ROLLBACK")
    
    print(f"✓ Completed: {inserted:,} records inserted into approvers_l1")


def populate_approvers_l2(conn, num_records=100000):
    """Populate approvers_l2 table with 100k records"""
    print(f"\nPopulating approvers_l2 table with {num_records:,} records...")
    
    # Clear existing data
    ibm_db.exec_immediate(conn, "DELETE FROM approvers_l2")
    ibm_db.exec_immediate(conn, "COMMIT")
    
    batch_size = 1000
    inserted = 0
    
    for batch_start in range(1, num_records + 1, batch_size):
        values = []
        for i in range(batch_start, min(batch_start + batch_size, num_records + 1)):
            approver_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            department = random.choice(DEPARTMENTS)
            max_limit = random.choice([1000000, 2500000, 5000000, 10000000])
            active = 'Y' if random.random() > 0.15 else 'N'  # 85% active
            region = random.choice(REGIONS)
            seniority = random.randint(1, 5)
            
            values.append(f"({i}, '{approver_name}', '{department}', {max_limit}, '{active}', '{region}', {seniority})")
        
        sql = f"""
        INSERT INTO approvers_l2 (approver_id, approver_name, department, max_approval_limit, active_flag, region, seniority_level)
        VALUES {', '.join(values)}
        """
        
        try:
            ibm_db.exec_immediate(conn, sql)
            ibm_db.exec_immediate(conn, "COMMIT")
            inserted += len(values)
            if inserted % 10000 == 0:
                print(f"  Inserted {inserted:,} records...")
        except Exception as e:
            print(f"  Error inserting batch: {e}")
            ibm_db.exec_immediate(conn, "ROLLBACK")
    
    print(f"✓ Completed: {inserted:,} records inserted into approvers_l2")


def populate_loan_applications(conn, num_records=100000):
    """Populate loan_applications table with 100k records"""
    print(f"\nPopulating loan_applications table with {num_records:,} records...")
    
    # Clear existing data
    ibm_db.exec_immediate(conn, "DELETE FROM loan_applications")
    ibm_db.exec_immediate(conn, "COMMIT")
    
    batch_size = 1000
    inserted = 0
    start_date = datetime.now() - timedelta(days=365)
    
    for batch_start in range(1, num_records + 1, batch_size):
        values = []
        for i in range(batch_start, min(batch_start + batch_size, num_records + 1)):
            applicant_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            loan_amount = round(random.uniform(10000, 5000000), 2)
            app_date = start_date + timedelta(days=random.randint(0, 365))
            status = random.choice(STATUSES)
            current_approver = random.randint(1, 100000) if status in ['PENDING', 'IN_REVIEW'] else None
            approval_level = random.randint(1, 2)
            
            approver_str = str(current_approver) if current_approver else 'NULL'
            
            values.append(
                f"({i}, '{applicant_name}', {loan_amount}, '{app_date.strftime('%Y-%m-%d')}', "
                f"'{status}', {approver_str}, {approval_level}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        
        sql = f"""
        INSERT INTO loan_applications (application_id, applicant_name, loan_amount, application_date, 
                                      status, current_approver_id, approval_level, created_at, updated_at)
        VALUES {', '.join(values)}
        """
        
        try:
            ibm_db.exec_immediate(conn, sql)
            ibm_db.exec_immediate(conn, "COMMIT")
            inserted += len(values)
            if inserted % 10000 == 0:
                print(f"  Inserted {inserted:,} records...")
        except Exception as e:
            print(f"  Error inserting batch: {e}")
            ibm_db.exec_immediate(conn, "ROLLBACK")
    
    print(f"✓ Completed: {inserted:,} records inserted into loan_applications")


def verify_data(conn):
    """Verify the inserted data"""
    print("\nVerifying data...")
    
    tables = ['loan_applications', 'approvers_l1', 'approvers_l2']
    
    for table in tables:
        sql = f"SELECT COUNT(*) as count FROM {table}"
        stmt = ibm_db.exec_immediate(conn, sql)
        result = ibm_db.fetch_assoc(stmt)
        count = result['COUNT'] if result else 0
        print(f"  {table}: {count:,} records")


def main():
    """Main execution function"""
    print("=" * 60)
    print("DB2 Loan Approval System - Data Population")
    print("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database. Exiting...")
        return
    
    try:
        # Populate all tables
        populate_approvers_l1(conn, 100000)
        populate_approvers_l2(conn, 100000)
        populate_loan_applications(conn, 100000)
        
        # Verify
        verify_data(conn)
        
        print("\n" + "=" * 60)
        print("✓ Data population completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during data population: {e}")
    finally:
        ibm_db.close(conn)
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
