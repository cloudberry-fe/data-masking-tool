# Cloudberry Data Management Console - User Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Data Source Management](#data-source-management)
3. [Data Masking](#data-masking)
4. [Data Lineage](#data-lineage)
5. [Data Synchronization](#data-synchronization)
6. [System Management](#system-management)
7. [Masking Algorithms](#masking-algorithms)

---

## Quick Start

### 1. Start the System

#### Using Docker (Recommended)
```bash
# Clone the project
git clone <repository-url>
cd data-masking-tool

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Manual Startup
```bash
# Backend
cd backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to configure database
python scripts/init_db.py
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

### 2. Access the System
- Frontend URL: http://localhost
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs

### 3. Login to System
- Default Username: `admin`
- Default Password: `admin123`

> ⚠️ **Security Warning**: Please change the default password immediately after first login!

---

## Data Source Management

### 1. Add a Data Source

1. Click **"Data Sources"** in the left menu
2. Click **"New Data Source"** in the top-right corner
3. Fill in the data source information:

| Field | Description | Example |
|-------|-------------|---------|
| Data Source Name | Custom name | Production MPP Database |
| Data Source Type | Select database type | HashData Lightning (MPP) |
| Host Address | Database server IP | 192.168.1.100 |
| Port | Database port | 5432 |
| Database Name | Database name | hashdata |
| Username | Database username | gpadmin |
| Password | Database password | ******** |

4. Click **"Test Connection"** to verify the configuration
5. Click **"OK"** to save

### 2. Manage Data Sources

- **Edit**: Click "Edit" in the actions column to modify data source information
- **Delete**: Click "Delete" to remove a data source (requires confirmation)
- **Test Connection**: Click "Test Connection" to verify if connection works
- **View References**: View which tasks reference the data source on the detail page

### 3. Account Mapping

To enable account mapping:
1. Edit the data source and enable "Enable Account Mapping"
2. Configure source-to-target account mappings in the data source details

---

## Data Masking

### 1. Create a Masking Task

1. Click **"Data Masking"** in the left menu
2. Click **"New Task"** in the top-right corner
3. Fill in task information:
   - Task Name: Customer Information Masking
   - Data Source: Select a configured data source
   - Source Schema: public (optional)
   - Target Schema: public (optional)
   - Schedule Type: Manual / Scheduled

### 2. Configure Tables and Fields

Click **"Configure"** in the task list to enter task details:

#### Add a Table
1. Click **"Add Table"**
2. Enter table name, or select from data source
3. Set source and target table names
4. Click "OK"

#### Configure Field Masking
1. Click **"Field Configuration"** for a table
2. Click **"Manual Add"** or **"Select from Table"**
3. Select fields and masking algorithms

### 3. Masking Algorithm Configuration

Each field can be configured with these masking algorithms:

| Algorithm | Description | Use Case |
|-----------|-------------|----------|
| Mask | Keep partial info, replace rest with * | Phone, ID card, Bank card |
| Hash | SHA256 irreversible hash | Unique identifiers |
| Replace | Fixed value replacement | Sensitive fields |
| Null | Set to NULL | Unneeded fields |
| Round | Numeric range rounding | Amount, Age |
| Offset | Numeric fixed offset | Age, Date |
| Format Preserving | Format-preserving randomization | Names, Addresses |

### 4. Execute Masking Tasks

1. Click **"Execute"** in task list or detail page
2. Confirm and the task starts executing
3. View execution status and results in **"Execution History"**

### 5. Using HashData Anon Extension

The system integrates HashData Lightning's Anon extension for high-performance masking:

```sql
-- Anon extension usage examples
SELECT anon.partial('13812345678', 3, 4);  -- 138****5678
SELECT anon.digest('secret', 'sha256');      -- Hash masking
SELECT anon.random_first_name();               -- Random first name
```

---

## Data Lineage

### 1. View Lineage Graph

1. Click **"Data Lineage"** in the left menu
2. Select a data source
3. Click **"Analyze"** to generate lineage graph

### 2. Graph Operations

- **Zoom**: Use mouse wheel to zoom in/out
- **Pan**: Drag the canvas to move view
- **Node Details**: Click nodes to view details

---

## Data Synchronization

### 1. Create a Sync Task

1. Click **"Data Sync"** in the left menu
2. Click **"New Task"**
3. Configure the task:
   - Task Name
   - Source Data Source
   - Target Data Source
   - Sync Mode: Full / Incremental
   - Schedule Type: Manual / Scheduled

### 2. Execute Sync

Click **"Execute"** to start the sync task. View execution status in the task list.

---

## System Management

### 1. User Management

#### Add User
1. Go to **"System Management" → "Users"**
2. Click **"New User"**
3. Fill in user information:
   - Username (unique)
   - Password
   - Real Name
   - Email, Phone (optional)

#### Assign Roles
1. Click **"Assign Roles"** for a user
2. Check the required roles
3. Click "OK"

#### Other Operations
- **Edit**: Modify user information
- **Enable/Disable**: Toggle user status
- **Delete**: Remove user (cannot delete yourself)

### 2. Role Management

#### Create Role
1. Go to **"System Management" → "Roles"**
2. Click **"New"**
3. Fill in role code and name

#### Configure Permissions
1. Click to select a role in the role list
2. Check permissions in the right configuration area
3. Click **"Save"**

#### Permission Categories

| Module | Permission Description |
|--------|------------------------|
| Data Source Management | View, create, edit, delete data sources |
| Data Masking | View, create, edit, execute masking tasks |
| Data Lineage | View lineage graphs |
| Data Sync | View, create, execute sync tasks |
| System Management | Users, roles, audit log management |

### 3. Audit Logs

#### View Logs
Go to **"System Management" → "Audit Logs"** to view all operation logs:

- **Operation Type**: LOGIN/LOGOUT/CREATE/UPDATE/DELETE/EXECUTE
- **Operation Module**: auth/datasource/masking/lineage/sync/system
- **Result**: Success/Failure
- **Time Range**: Filter by time

#### Log Details
Click "Details" to view complete log information, including:
- Request parameters
- Error message (if any)
- IP address
- User-Agent

---

## Masking Algorithms

### 1. Mask Algorithm (MASK)

Suitable for phone numbers, ID cards, bank cards that need to retain partial information.

**Parameters**:
- `prefix_length`: Prefix retention length, default 3
- `suffix_length`: Suffix retention length, default 4
- `mask_char`: Mask character, default *

**Example**:
```
Phone: 13812345678 → 138****5678
ID card: 110101199001011234 → 110***********1234
```

### 2. Hash Algorithm (HASH)

Uses SHA-256 algorithm for irreversible hashing, suitable for unique identifiers.

**Parameters**:
- `salt`: Salt value (optional, increases security)

**Example**:
```
Original value: abc123
Hash value: a665a45920422f9d417e4866ef6e32b7...
```

### 3. Replace Algorithm (REPLACE)

Replaces original data with a fixed value.

**Parameters**:
- `replacement`: Replacement value

**Example**:
```
Original value: Zhang San
Replacement value: ***
```

### 4. Null Algorithm (NULL)

Sets field value to NULL.

### 5. Round Algorithm (ROUND)

Rounds numeric values, suitable for amounts, ages, etc.

**Parameters**:
- `precision`: Precision, negative means power of 10

**Example**:
```
precision=-3: 12345.67 → 12000
precision=2: 12.345 → 12.35
```

### 6. Offset Algorithm (OFFSET)

Applies fixed offset to numeric values, suitable for scenarios needing relative relationships preserved.

**Parameters**:
- `offset`: Offset amount
- `min_value`: Minimum value (optional)
- `max_value`: Maximum value (optional)

**Example**:
```
offset=5: 30 → 35
```

### 7. Format-Preserving Algorithm (PRESERVATION)

Randomizes while preserving data format, such as replacing names with random names, addresses with random addresses.

---

## Best Practices

### 1. Data Security
- Regularly change administrator password
- Follow least privilege principle for role assignment
- Regularly backup metadata database
- Approval process before sensitive operations

### 2. Masking Configuration
- Test masking rules in test environment first
- Backup important data before masking
- Use mask and format preservation to minimize business impact
- Reasonably set target tables, avoid overwriting source tables

### 3. Performance Optimization
- Use HashData MPP database for parallel processing
- Reasonably set task batch sizes
- Execute masking tasks during off-peak hours
- Regularly clean execution history logs

### 4. Operation & Monitoring
- Configure task failure alerts
- Regularly check disk space
- Monitor masking task execution duration
- Regularly audit operation logs

---

## FAQ

### Q: What if data source connection test fails?
A: Check these:
- Network connectivity: `telnet host port`
- Username/password are correct
- Database allows remote connections (check pg_hba.conf)
- Firewall has port open

### Q: What if masking task executes very slowly?
A: Optimization suggestions:
- Use HashData MPP database to leverage parallel processing
- Process large tables in batches
- Avoid peak business hours
- Check if Anon extension is enabled

### Q: How to rollback masking operations?
A: Recommendations:
- Backup data before masking
- Use target tables instead of overwriting source tables
- Keep source data until verification passes

### Q: Which database types are supported?
A: Currently supported:
- HashData Lightning (MPP)
- PostgreSQL
- MySQL
- Oracle
- GoldenDB
- Dameng

### Q: How to use scheduled execution?
A: Configure Cron expression:
- `0 0 2 * * ?` Every day at 2 AM
- `0 0 2 * * 0` Every Sunday at 2 AM
- `0 0 2 1 * ?` Every 1st of month at 2 AM

---

## Appendix

### Cron Expression Reference
```
Second Minute Hour Day Month Weekday
0      0      2    *   *     ?  → Execute daily at 2 AM
```

### Contact
- Issues: Submit to Issue tracker
- Documentation: Check docs/ directory

---

**Document Version**: v1.0
**Last Updated**: 2026-03-02
