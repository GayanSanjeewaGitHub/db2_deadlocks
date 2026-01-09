"""
Query implementations for performance comparison
1. Traditional UPDATE with subquery (INNER JOIN)
2. MERGE statement approach
"""


class QueryTypes:
    """
    Contains the two query types for performance comparison
    
    Scenario: Update loan applications to assign new approvers based on 
    matching criteria from L1 and L2 approver tables
    """
    
    @staticmethod
    def get_update_with_subquery():
        """
        Traditional UPDATE approach using subquery with INNER JOIN
        
        Updates loan_applications (L) table by finding matching approvers 
        from the INNER JOIN of approvers_l1 (L1) and approvers_l2 (L2)
        
        Logic:
        - Find active approvers from both L1 and L2 tables who match the region
        - Join them based on department matching
        - Update loan applications with new approver IDs
        """
        query = """
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
        """
        return query
    
    @staticmethod
    def get_merge_query():
        """
        MERGE statement approach (optimized for DB2)
        
        Uses MERGE to update loan applications based on matching approvers
        MERGE is typically faster in DB2 as it:
        - Reduces the number of table scans
        - Optimizes the join operations
        - Better handles bulk operations
        
        Logic:
        - Create a source query with INNER JOIN of L1 and L2
        - MERGE into loan_applications based on matching conditions
        - Update approver IDs when matched
        """
        query = """
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
        """
        return query
    
    @staticmethod
    def get_reset_query():
        """
        Query to reset the data for testing
        Sets some applications back to PENDING status for retesting
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
        return query
    
    @staticmethod
    def get_count_query():
        """Get count of records that will be affected"""
        query = """
        SELECT COUNT(*) as affected_count
        FROM loan_applications L
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
        """
        return query


# Query descriptions for UI
QUERY_DESCRIPTIONS = {
    'update_subquery': {
        'name': 'UPDATE with Subquery (INNER JOIN)',
        'description': 'Traditional UPDATE statement with correlated subquery using INNER JOIN',
        'approach': 'Updates each row individually after finding matches via subquery'
    },
    'merge': {
        'name': 'MERGE Statement',
        'description': 'DB2-optimized MERGE statement with INNER JOIN in source',
        'approach': 'Bulk operation that merges data from joined source into target table'
    }
}
