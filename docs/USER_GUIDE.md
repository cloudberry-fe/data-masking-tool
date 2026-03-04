# Cloudberry Data Management Console - User Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Language Settings](#language-settings)
3. [Data Source Management](#data-source-management)
4. [Data Masking](#data-masking)
   - [Masking Modes](#masking-modes)
   - [Static Masking](#static-masking)
   - [Dynamic Masking](#dynamic-masking)
   - [Anonymization](#anonymization)
5. [Data Lineage](#data-lineage)
6. [Data Synchronization](#data-synchronization)
7. [System Management](#system-management)
8. [Masking Algorithms](#masking-algorithms)

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

After startup, access the system:
- **Frontend UI**: http://localhost (or http://localhost:5173 for dev mode)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

### 3. Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Super Admin |

> ⚠️ **Security Warning**: Please change the default password immediately after first login!

---

## Language Settings

### Switching Languages

The system supports **English** and **中文** (Chinese) languages.

1. Click the **🌍** (globe) icon in the top right corner of the header
2. Select your preferred language from the dropdown:
   - 🇺🇸 **English** - Default language
   - 🇨🇳 **中文** - Chinese (Simplified)

The language preference is saved automatically in your browser and will persist across sessions.

---

## Data Source Management

### Adding a Data Source

1. Navigate to **Data Sources** from the sidebar menu
2. Click **New Data Source**
3. Fill in the connection details:
   - **Data Source Name**: Descriptive name for identification
   - **Data Source Type**: Select database type (MPP, PostgreSQL, MySQL, Oracle, Dameng)
   - **Host**: Database server address
   - **Port**: Database port number
   - **Database Name**: Target database name
   - **Username**: Database username
   - **Password**: Database password
4. Click **Test Connection** to verify connectivity
5. Click **Save** to create the data source

### Editing a Data Source

1. Find the data source in the list
2. Click **Edit**
3. Modify the required fields
4. Click **Test Connection** to verify
5. Click **Save**

---

## Data Masking

### Masking Modes

The system supports **four masking modes** for different use cases:

| Mode | Description | Use Case | Original Data | Irreversible |
|------|-------------|----------|---------------|--------------|
| **Static Masking** | Create masked data copy | Dev/Test environments, Data export | Unchanged | No |
| **Dynamic Masking** | Role-based query masking | Production environments | Unchanged | No |
| **Anonymization** | Permanent data modification | GDPR compliance, Data destruction | Modified | Yes |
| **Generalization** | Convert to ranges | Data analytics, Statistical reports | Unchanged | No |

### Choosing the Right Mode

```
┌─────────────────────────────────────────────────────────────┐
│                    Which Masking Mode?                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Do you need to modify original data?                       │
│  ├── NO  → Do you need real-time masking?                   │
│  │         ├── YES → Dynamic Masking                        │
│  │         └── NO  → Static Masking or Generalization       │
│  │                    ├── Preserve format? → Static         │
│  │                    └── For analytics? → Generalization   │
│  │                                                          │
│  └── YES → Anonymization (⚠️ IRREVERSIBLE!)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Static Masking

Static masking creates a new table with masked data, leaving the original data unchanged.

#### Creating a Static Masking Task

1. Navigate to **Data Masking > Static Masking**
2. Click **New Task**
3. Fill in the form:
   - **Task Name**: Descriptive name (e.g., "Customer Data Masking")
   - **Data Source**: Select the target database
   - **Masking Mode**: Select "Static Masking"
   - **Source Schema**: Source schema name (default: public)
   - **Target Schema**: Target schema name (default: public)
4. Click **Save**

#### Configuring Tables and Columns

1. Click **Configure** on the created task
2. Click **Add Table**
3. Enter table configuration:
   - **Table Name**: Identifier for this table config
   - **Source Table**: Original table name
   - **Target Table**: Masked table name (e.g., `users_masked`)
4. Click **Select from Database** to load columns automatically, or add columns manually
5. For each column, select a masking algorithm and configure parameters

#### Executing the Task

1. Return to the task list
2. Click **Execute** on the task
3. The system will:
   - Create the target table
   - Copy data from source table
   - Apply masking transformations
   - Display execution results

### Dynamic Masking

Dynamic masking applies role-based masking rules on queries, without modifying the original data. Different database roles see different data when querying the same table.

#### Features:
- Original data remains unchanged
- Different roles see different data
- Uses PostgreSQL SECURITY LABEL mechanism
- Real-time masking on query
- Suitable for production environments

#### Creating a Dynamic Masking Rule

1. Navigate to **Data Masking > Dynamic Masking**
2. Click **New Rule**
3. Configure the rule:
   - **Rule Name**: Descriptive name
   - **Data Source**: Target database
   - **Schema Name**: Schema (default: public)
   - **Table Name**: Table to apply masking
   - **Masked Roles**: Database roles that will see masked data
   - **Exempted Roles**: Database roles that can see original data
4. Click **Save**

#### Adding Column Rules

1. Click **Configure** on the rule
2. Add column masking rules:
   - **Column Name**: Column to mask
   - **Masking Algorithm**: Algorithm to apply
   - **Parameters**: Algorithm parameters
3. Click **Save**

#### Enabling the Rule

1. Click **Enable** on the rule
2. The system will generate and execute SQL to:
   - Set SECURITY LABEL on columns
   - Create masked views
   - Grant appropriate permissions

#### Example SQL Generated:

```sql
-- Create masked role if not exists
CREATE ROLE analyst NOINHERIT;

-- Set security label on column
SECURITY LABEL FOR anon ON COLUMN public.users.email
  IS 'MASKED WITH FUNCTION anon.fake_email()';

-- Create masked view
CREATE VIEW public.users_masked AS SELECT * FROM public.users;

-- Grant access to masked view
GRANT SELECT ON public.users_masked TO analyst;
```

### Anonymization

⚠️ **WARNING**: Anonymization permanently modifies the original table data. This operation is **IRREVERSIBLE**. Always enable backup!

#### Features:
- Permanent data modification in original table
- Optional backup before execution
- Suitable for GDPR compliance
- Data destruction scenarios

#### Creating an Anonymization Task

1. Navigate to **Data Masking > Anonymization**
2. Click **New Task**
3. Configure:
   - **Task Name**: Descriptive name
   - **Data Source**: Target database
   - **Schema Name**: Schema name
   - **Table Name**: Table to anonymize
   - **Backup Before Anonymize**: ✓ (Strongly recommended!)
   - **Description**: Task description
4. Click **Save**

#### Adding Column Rules

Same as static masking - configure which columns to anonymize and which algorithms to use.

#### Preview and Execute

1. Click **Preview SQL** to review the generated SQL
2. Verify the backup table name
3. Click **Execute** to anonymize

#### Example SQL Generated:

```sql
-- Create backup table
CREATE TABLE public.users_backup_20260304 AS SELECT * FROM public.users;

-- Anonymize columns (permanent UPDATE)
UPDATE public.users SET email = anon.fake_email();
UPDATE public.users SET phone = anon.partial(phone::text, 3, '*', 4);
UPDATE public.users SET salary = anon.noise(salary, 0.15);
```

---

## Data Lineage

The Data Lineage module provides visual analysis of data flow and dependencies.

1. Navigate to **Lineage Analysis**
2. Select a data source
3. Select a table to analyze
4. View upstream (sources) and downstream (targets) dependencies

---

## Data Synchronization

The Data Sync module enables data migration between databases.

### Creating a Sync Task

1. Navigate to **Data Sync**
2. Click **New Task**
3. Configure:
   - **Task Name**: Descriptive name
   - **Source Data Source**: Source database
   - **Target Data Source**: Target database
   - **Sync Mode**: Full sync or Incremental sync
4. Add table mappings
5. Configure field mappings if needed
6. Save and execute

---

## System Management

### User Management

1. Navigate to **System > Users**
2. View, create, edit, or delete users
3. Assign roles to users
4. Reset passwords

### Role Management

1. Navigate to **System > Roles**
2. Create and configure roles
3. Assign permissions to roles
4. Permissions include:
   - Menu access
   - Operation permissions (create, edit, delete, execute)
   - Data permissions

### Audit Logs

1. Navigate to **System > Audit Logs**
2. View comprehensive operation history
3. Filter by:
   - Operation type (CREATE, UPDATE, DELETE, EXECUTE)
   - Module (datasource, masking, system)
   - Time range
   - User

---

## Masking Algorithms

### Algorithm Categories

| Category | Description | Use Case |
|----------|-------------|----------|
| **Fake Data** | Generate realistic fake data | Names, emails, addresses |
| **Random** | Generate random values | IDs, codes |
| **Partial** | Preserve partial information | Phone numbers, ID cards |
| **Pseudonymization** | Deterministic replacement | Consistent fake data |
| **Hash** | One-way hash transformation | Passwords, sensitive IDs |
| **Noise** | Add random noise | Salaries, ages |
| **Generalization** | Convert to ranges | Age groups, salary ranges |

### Common Algorithms Reference

#### anon.fake_email
Generate fake but valid email addresses.
```
Original: zhangsan@example.com
Masked:   lauren95@example.com
```

#### anon.fake_first_name
Generate fake first names.
```
Original: 张三
Masked:   Ronnie
```

#### anon.fake_phone_number
Generate fake phone numbers.
```
Original: 13812345678
Masked:   01-23-45-67-89
```

#### anon.partial
Partial masking - preserve prefix and suffix.

**Parameters:**
- `prefix_len`: Characters to keep at start (default: 2)
- `mask_char`: Masking character (default: '*')
- `suffix_len`: Characters to keep at end (default: 2)

```
Original: 13812345678
Params:   prefix_len=3, mask_char='*', suffix_len=4
Masked:   138****5678
```

#### anon.noise
Add random noise to numeric values.

**Parameters:**
- `ratio`: Noise ratio (e.g., 0.15 means ±15%)

```
Original: 15000.00
Params:   ratio=0.15
Masked:   15135.68 (within ±15% of original)
```

#### anon.digest
Hash transformation with custom salt.

**Parameters:**
- `salt`: Salt value for hashing
- `algorithm`: Hash algorithm (md5, sha1, sha256)

```
Original: 110101199001011234
Params:   salt='my_salt', algorithm='sha256'
Masked:   5d41402abc4b2a76b9719d911017c592...
```

#### anon.hash
Hash transformation with system salt.
```
Original: sensitive_data
Masked:   a1b2c3d4e5f6...
```

---

## Best Practices

### 1. Always Backup Before Anonymization
Enable the backup option when performing anonymization to protect against accidental data loss.

### 2. Test with Small Datasets First
Before running masking on production data, test with a small sample to verify the results meet expectations.

### 3. Choose Appropriate Algorithms

| Data Type | Recommended Algorithm |
|-----------|----------------------|
| Email | `anon.fake_email` |
| Phone | `anon.partial` (preserve area code) |
| Name | `anon.fake_first_name`, `anon.fake_last_name` |
| ID Card | `anon.digest` or `anon.hash` |
| Salary | `anon.noise` or generalization |
| Address | `anon.fake_address` |

### 4. Use Dynamic Masking for Production
For production environments where original data must be preserved, use dynamic masking instead of anonymization.

### 5. Review Generated SQL
Always preview the generated SQL before executing to understand what operations will be performed.

---

## Troubleshooting

### Connection Failed
- Verify the database host and port are accessible
- Check firewall rules
- Verify username and password
- Ensure the database exists

### Masking Execution Failed
- Check algorithm compatibility with column data type
- Verify the target table doesn't already exist (for static masking)
- Check database user has necessary permissions
- Review error messages in execution history

### Language Not Changing
- Clear browser cache and cookies
- Refresh the page
- Check browser localStorage

### Performance Issues
- For large tables, consider batch processing
- Use database indexes appropriately
- Schedule masking during off-peak hours

---

## Support

For additional support, please contact your system administrator or refer to the technical documentation.

---

**Document Version**: v2.0.0
**Last Updated**: 2026-03-04
