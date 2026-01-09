"""
Database connection and query execution module
"""

import ibm_db
import os
from dotenv import load_dotenv
from typing import Optional, Tuple

load_dotenv()


class DB2Connection:
    """
    Handles DB2 database connections and query execution
    """
    
    def __init__(self):
        self.host = os.getenv('DB2_HOST', 'localhost')
        self.port = os.getenv('DB2_PORT', '50000')
        self.database = os.getenv('DB2_DATABASE', 'LOANDB')
        self.user = os.getenv('DB2_USER', 'db2inst1')
        self.password = os.getenv('DB2_PASSWORD', 'db2admin123')
        self.conn = None
        
    def connect(self) -> bool:
        """
        Establish connection to DB2 database
        
        Returns:
            True if successful, False otherwise
        """
        try:
            dsn = (
                f"DATABASE={self.database};"
                f"HOSTNAME={self.host};"
                f"PORT={self.port};"
                f"PROTOCOL=TCPIP;"
                f"UID={self.user};"
                f"PWD={self.password};"
            )
            self.conn = ibm_db.connect(dsn, "", "")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            try:
                ibm_db.close(self.conn)
                self.conn = None
            except Exception as e:
                print(f"Error closing connection: {e}")
    
    def execute_query(self, query: str) -> int:
        """
        Execute a query and return number of affected rows
        
        Args:
            query: SQL query to execute
            
        Returns:
            Number of rows affected
            
        Raises:
            Exception if query execution fails
        """
        if not self.conn:
            raise Exception("Not connected to database")
        
        try:
            stmt = ibm_db.exec_immediate(self.conn, query)
            ibm_db.commit(self.conn)
            
            # Get number of affected rows
            rows_affected = ibm_db.num_rows(stmt)
            
            return rows_affected if rows_affected >= 0 else 0
            
        except Exception as e:
            ibm_db.rollback(self.conn)
            raise Exception(f"Query execution failed: {str(e)}")
    
    def fetch_one(self, query: str) -> Optional[dict]:
        """
        Execute a query and fetch one row
        
        Args:
            query: SQL query to execute
            
        Returns:
            Dictionary with column names and values, or None
        """
        if not self.conn:
            raise Exception("Not connected to database")
        
        try:
            stmt = ibm_db.exec_immediate(self.conn, query)
            result = ibm_db.fetch_assoc(stmt)
            return result
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def fetch_all(self, query: str) -> list:
        """
        Execute a query and fetch all rows
        
        Args:
            query: SQL query to execute
            
        Returns:
            List of dictionaries with column names and values
        """
        if not self.conn:
            raise Exception("Not connected to database")
        
        try:
            stmt = ibm_db.exec_immediate(self.conn, query)
            results = []
            
            while True:
                row = ibm_db.fetch_assoc(stmt)
                if not row:
                    break
                results.append(row)
            
            return results
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def get_table_stats(self) -> dict:
        """
        Get statistics for all tables
        
        Returns:
            Dictionary with table statistics
        """
        tables = ['loan_applications', 'approvers_l1', 'approvers_l2']
        stats = {}
        
        for table in tables:
            try:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.fetch_one(query)
                stats[table] = result['COUNT'] if result else 0
            except Exception as e:
                stats[table] = f"Error: {str(e)}"
        
        return stats
    
    def get_pending_applications_count(self) -> int:
        """
        Get count of pending loan applications
        
        Returns:
            Number of pending applications
        """
        query = """
        SELECT COUNT(*) as count 
        FROM loan_applications 
        WHERE status = 'PENDING' AND approval_level = 1
        """
        result = self.fetch_one(query)
        return result['COUNT'] if result else 0
    
    def reset_test_data(self) -> int:
        """
        Reset some data for testing (set applications back to PENDING)
        
        Returns:
            Number of rows updated
        """
        query = """
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
        """
        return self.execute_query(query)
    
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self.conn is not None


def test_connection():
    """Test database connection"""
    db = DB2Connection()
    
    print("Testing DB2 connection...")
    if db.connect():
        print("✓ Connected successfully!")
        
        stats = db.get_table_stats()
        print("\nTable Statistics:")
        for table, count in stats.items():
            print(f"  {table}: {count:,}" if isinstance(count, int) else f"  {table}: {count}")
        
        db.disconnect()
        print("\n✓ Disconnected successfully!")
        return True
    else:
        print("✗ Connection failed!")
        return False


if __name__ == "__main__":
    test_connection()
