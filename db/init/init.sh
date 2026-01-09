#!/bin/bash
# This script is executed by DB2 container on startup

echo "Starting DB2 database initialization..."

# Wait for DB2 to be ready
sleep 30

# Connect to the database and run schema creation
su - db2inst1 -c "db2 connect to LOANDB && db2 -tvf /docker-entrypoint-initdb.d/01_create_schema.sql"

echo "Database schema created successfully!"
