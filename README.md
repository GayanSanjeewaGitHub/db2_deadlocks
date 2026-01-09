# DB2 Query Performance Testing - UPDATE vs MERGE

A comprehensive performance testing framework for comparing traditional UPDATE statements with MERGE operations in DB2, specifically designed for a loan approval system scenario.

## 🎯 Project Overview

This project demonstrates and compares the performance of two different query approaches in DB2:

1. **Traditional UPDATE with Subquery** - Uses INNER JOIN within a correlated subquery
2. **MERGE Statement** - DB2-optimized bulk operation approach

The test scenario simulates a loan approval workflow where applications need to be routed to appropriate approvers based on matching criteria from two approver tables (L1 and L2).

## 📊 Features

- **Docker-based DB2 Setup** - Easy deployment with IBM DB2 Community Edition
- **Automated Data Population** - Scripts to generate 100,000 records per table
- **Real-time Performance Monitoring** - Tracks execution time and CPU usage
- **Web-based UI** - Flask application with interactive dashboard
- **Comprehensive Metrics** - Detailed performance comparison with visual results
- **Reusable Test Data** - Reset functionality for multiple test runs

## 🏗️ Architecture

### Database Schema

```
loan_applications (L)
├── application_id (PK)
├── applicant_name
├── loan_amount
├── application_date
├── status
├── current_approver_id
├── approval_level
└── timestamps

approvers_l1 (L1)
├── approver_id (PK)
├── approver_name
├── department
├── max_approval_limit
├── active_flag
└── region

approvers_l2 (L2)
├── approver_id (PK)
├── approver_name
├── department
├── max_approval_limit
├── active_flag
├── region
└── seniority_level
```

### Query Comparison

**Query 1: UPDATE with Subquery**
```sql
UPDATE loan_applications L
SET current_approver_id = (
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
)
WHERE L.status = 'PENDING' AND L.approval_level = 1
```

**Query 2: MERGE Statement**
```sql
MERGE INTO loan_applications AS L
USING (
    SELECT L1.approver_id as l1_approver_id,
           L2.approver_id as l2_approver_id,
           L1.department, L1.region,
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
    UPDATE SET current_approver_id = approvers.l2_approver_id
```

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
- **Python 3.8+**
- **8GB+ RAM** recommended for DB2
- **10GB+ disk space**

### Step 1: Clone and Setup

```powershell
# Navigate to project directory
cd "d:\DailyGITHUB_DistinGuished_Engineer\2026 jan\db2_deadlocks"

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Start DB2 Container

```powershell
# Start DB2 using Docker Compose
docker-compose up -d

# Wait for DB2 to initialize (takes 3-5 minutes)
# Check logs to confirm DB2 is ready
docker-compose logs -f db2
```

Wait until you see messages indicating the database is ready. Press `Ctrl+C` to exit log view.

### Step 3: Populate Database

```powershell
# Run the data population script
python db\scripts\populate_data.py
```

This will create 100,000 records in each table:
- loan_applications: 100,000 loan applications
- approvers_l1: 100,000 L1 approvers
- approvers_l2: 100,000 L2 approvers

**Note:** This process takes 10-15 minutes depending on your system.

### Step 4: Start Web Application

```powershell
# Start the Flask application
python app.py
```

The web interface will be available at: **http://localhost:5000**

## 📖 Usage Guide

### Web Interface

1. **Connect to Database**
   - Click "Connect to DB2" button
   - View database statistics once connected

2. **Execute Queries**
   - Click "Execute UPDATE with Subquery" to run the traditional approach
   - Click "Execute MERGE Statement" to run the MERGE approach
   - View real-time performance metrics

3. **Compare Results**
   - After running both queries, a comparison card will appear
   - Shows time difference, percentage improvement, and speedup factor

4. **Reset Test Data**
   - Click "Reset Test Data" to restore applications to PENDING status
   - Allows you to re-run tests for consistency

5. **Clear Results**
   - Click "Clear Results" to remove all performance data from display

### Performance Metrics Tracked

- **Execution Time** - Milliseconds and seconds
- **Rows Affected** - Number of records updated
- **CPU Usage** - Average, max, and min during execution
- **Memory Usage** - Average and maximum in MB
- **Success Status** - Query execution status

## 📂 Project Structure

```
db2_deadlocks/
├── app.py                      # Flask web application
├── docker-compose.yml          # Docker configuration for DB2
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── .env.example               # Example environment file
├── .gitignore                 # Git ignore rules
│
├── db/
│   ├── init/
│   │   ├── 01_create_schema.sql   # Database schema
│   │   └── init.sh                # Initialization script
│   └── scripts/
│       └── populate_data.py       # Data population script
│
├── src/
│   ├── __init__.py
│   ├── db_connection.py       # DB2 connection manager
│   ├── queries.py             # Query definitions
│   └── performance_monitor.py # Performance tracking
│
├── templates/
│   └── index.html             # Web UI template
│
└── README.md                  # This file
```

## 🔧 Configuration

Environment variables can be configured in `.env` file:

```env
# DB2 Connection
DB2_HOST=localhost
DB2_PORT=50000
DB2_DATABASE=LOANDB
DB2_USER=db2inst1
DB2_PASSWORD=db2admin123

# Flask
FLASK_ENV=development
FLASK_PORT=5000
```

## 🧪 Testing Methodology

### Test Scenario

The loan approval workflow simulates:
1. Applications are submitted and assigned to L1 approvers
2. Based on loan amount and criteria, they need to be routed to L2 approvers
3. The system updates `current_approver_id` by matching:
   - Department and region between L1 and L2 approvers
   - Active approvers only
   - L2 approver's limit must cover the loan amount

### Why MERGE is Typically Faster

1. **Reduced Table Scans** - MERGE performs a single scan of the joined data
2. **Optimized Execution Plan** - DB2 optimizer handles bulk operations efficiently
3. **Better Resource Usage** - Less overhead compared to row-by-row correlated subqueries
4. **Efficient Locking** - Better lock management for bulk updates

## 🐛 Troubleshooting

### DB2 Container Won't Start

```powershell
# Check Docker logs
docker-compose logs db2

# Restart container
docker-compose restart db2

# If issues persist, remove and recreate
docker-compose down -v
docker-compose up -d
```

### Connection Errors

- Ensure DB2 container is running: `docker ps`
- Wait 3-5 minutes after starting for full initialization
- Check port 50000 is not in use: `netstat -an | findstr 50000`

### Python Package Installation Issues

```powershell
# Update pip first
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

### IBM DB2 Driver Issues (Windows)

The `ibm_db` package may require:
- Visual C++ Redistributable
- .NET Framework 4.0+

Download from Microsoft if needed.

## 📈 Expected Results

Based on typical DB2 behavior:

- **MERGE** is usually **30-60% faster** than UPDATE with subquery
- **CPU usage** tends to be more consistent with MERGE
- **Memory usage** is similar between both approaches
- Results may vary based on:
  - Data distribution
  - Index effectiveness
  - System resources
  - DB2 optimizer decisions

## 🛠️ Advanced Usage

### Manual Query Testing

```powershell
# Connect to DB2 container
docker exec -it db2_performance_test bash

# Switch to db2inst1 user
su - db2inst1

# Connect to database
db2 connect to LOANDB

# Run queries manually
db2 -tvf /scripts/your_query.sql
```

### Export Performance Data

Results are stored in memory during the Flask session. To persist results, you can modify `src/performance_monitor.py` to export to JSON/CSV.

## 📝 License

This project is for educational and testing purposes.

## 👥 Author

Created for DB2 performance analysis and optimization studies.

## 🙏 Acknowledgments

- IBM DB2 Community Edition
- Flask Framework
- Python ibm_db library

---

**Note:** This is a testing framework. Always test thoroughly in a development environment before applying similar patterns to production systems.