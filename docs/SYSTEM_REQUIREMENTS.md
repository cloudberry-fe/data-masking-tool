# Cloudberry Data Management Console - System Requirements Document (SRD)

**Document Version**: v1.0
**Date**: 2026-03-02
**Project Name**: Cloudberry Data Management Console

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [System Architecture](#4-system-architecture)
5. [Database Design](#5-database-design)
6. [API Definitions](#6-api-definitions)
7. [Security Requirements](#7-security-requirements)
8. [Acceptance Criteria](#8-acceptance-criteria)

---

## 1. Project Overview

### 1.1 Project Background
Organizations managing large-scale data platforms face significant challenges in data masking and data synchronization. Testing and development environments frequently require large datasets with sensitive information properly masked. Without proper tools, this process relies on manual identification and custom scripts, leading to long cycles (typically 7+ days) and security risks.

This platform addresses these challenges by providing a unified solution for data lineage analysis, MPP data masking, and data synchronization tools.

### 1.2 Project Goals
- Provide a unified platform for data masking, lineage analysis, and data synchronization
- Reduce data masking cycle times from days to automated processing
- Enhance data security through proper access controls and audit trails
- Support multiple database types including MPP, Oracle, MySQL, and more

---

## 2. Functional Requirements

### 2.1 Data Source Management (FR-001)

#### FR-001-01 Data Source Registration
| Feature | Description |
|---------|-------------|
| Create | Add data sources of various types (MPP, Oracle, MySQL, Dameng, etc.) |
| Edit | Modify existing data source configurations |
| Delete | Remove unused data sources |
| Test Connection | Verify if data source connection works properly |
| Configuration | Configure host, port, username, password, database name |

#### FR-001-02 Data Source References
| Feature | Description |
|---------|-------------|
| Environment References | View which environments reference the data source |
| Project References | View which projects reference the data source |
| Task References | View which tasks reference the data source |

#### FR-001-03 Account Mapping
| Feature | Description |
|---------|-------------|
| Enable/Disable | Toggle "source system account mapping" feature |
| Configure | Configure source-to-target account mappings |

### 2.2 Data Masking (FR-002)

#### FR-002-01 Masking Task Management
| Feature | Description |
|---------|-------------|
| Create | Create new data masking tasks |
| Edit | Modify masking task configurations |
| Delete | Remove masking tasks |
| Execute | Manually trigger masking task execution |
| Schedule | Support scheduled masking task execution |

#### FR-002-02 Masking Rule Configuration
| Feature | Description |
|---------|-------------|
| Algorithm Selection | Support for multiple algorithms (replace, mask, hash, encrypt, round, offset, etc.) |
| Field-level Config | Configure masking rules at the field level |
| Table-level Config | Batch configure multiple fields in a table |
| Rule Templates | Support saving and reusing masking rule templates |

#### FR-002-03 Masking Algorithm Library
| Algorithm | Description | Example |
|-----------|-------------|---------|
| REPLACE | Replace with fixed/random value | Name → "***" |
| MASK | Partial masking with wildcards | Phone → 138****1234 |
| HASH | One-way hash | ID → SHA256 hash |
| ENCRYPT | Reversible encryption | Card number → AES encrypted |
| ROUND | Numeric rounding | Amount 1234.56 → 1000 |
| OFFSET | Numeric offset | Age 30 → 35 |
| SHUFFLE | Shuffle within column | Randomize order |
| NULL | Set to NULL | - |
| SUBSTITUTION | Dictionary substitution | Use dictionary data |
| PRESERVATION | Format-preserving | Keep format while masking |

#### FR-002-04 Database Compatibility
| Database | Support Status |
|----------|----------------|
| HashData Lightning (MPP) | Core Support |
| PostgreSQL | Supported |
| Oracle | Supported |
| MySQL | Supported |
| Dameng | Supported |
| GoldenDB | Supported |

#### FR-002-05 Execution Monitoring
| Feature | Description |
|---------|-------------|
| Progress View | Real-time masking task progress |
| Log View | View detailed execution logs |
| Statistics | Count records processed, succeeded, failed |
| Alerts | Alert notifications on task failures |

### 2.3 Data Synchronization (FR-003)

#### FR-003-01 Sync Task Management
| Feature | Description |
|---------|-------------|
| Create | Create new data sync tasks |
| Configure | Configure source/target data sources, table mappings |
| Execute | Execute sync tasks |
| Monitor | Monitor sync task execution status |

#### FR-003-02 Data Sync Capabilities
| Feature | Description |
|---------|-------------|
| Full Sync | One-time full data sync |
| Incremental Sync | Timestamp or change log based incremental sync |
| Batch Processing | Support large-scale batch processing |

### 2.4 Platform Capabilities (FR-004)

#### FR-004-01 User Management
| Feature | Description |
|---------|-------------|
| Create | Admin adds new users |
| Edit | Modify user information |
| Delete | Delete user accounts |
| View | Query user list and details |
| Status | Enable/disable user accounts |

#### FR-004-02 Role Management
| Feature | Description |
|---------|-------------|
| Create | Create new roles |
| Edit | Modify role information |
| Delete | Delete roles |
| Assign | Assign roles to users (multiple roles supported) |
| Adjust | Adjust user roles at any time |

#### FR-004-03 Permission Management
| Feature | Description |
|---------|-------------|
| Configure | Configure feature permissions for roles |
| Inheritance | Support permission inheritance |
| Access Control | Restrict accessible features after login |

#### FR-004-04 Authentication
| Feature | Description |
|---------|-------------|
| Login | User authentication |
| Password | Password change/reset |
| Session | Session timeout control |

#### FR-004-06 Audit Log
| Feature | Description |
|---------|-------------|
| Operation Log | Record user key operations |
| Login Log | Record user login/logout |
| Log Query | Query by time, user, operation type |

---

## 3. Non-Functional Requirements

### 3.1 Performance (NFR-001)

| Metric | Requirement |
|--------|-------------|
| Data Scale | Support large-scale data processing |
| Processing Cycle | Significantly reduce from manual 7-day cycles |
| Concurrent Users | Support at least 50 concurrent users |
| Page Response | <2s for normal pages, <5s for complex queries |
| Task Concurrency | Support at least 100 concurrent masking tasks |

### 3.2 Compatibility (NFR-002)

| Category | Requirement |
|----------|-------------|
| Databases | HashData Lightning, PostgreSQL, Oracle, MySQL, Dameng, GoldenDB |
| Browsers | Chrome, Firefox, Edge, Safari (latest 2 versions) |
| OS | Server: Linux (CentOS 7+, Ubuntu 18+)<br>Client: Windows, macOS |

### 3.3 Security (NFR-003)

| Category | Requirement |
|----------|-------------|
| Data Transfer | HTTPS/TLS encrypted |
| Data Storage | Sensitive configurations encrypted |
| Password | Salted hash storage, complexity policies |
| Audit Trails | Complete operation audit logs |
| Access Isolation | Strict feature and data permission isolation |

### 3.4 Reliability (NFR-004)

| Metric | Requirement |
|--------|-------------|
| Availability | ≥99.5% |
| Backup | Support configuration and task data backup |
| Recovery | Support breakpoint recovery/retry on task failure |

---

## 4. System Architecture

### 4.1 Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │ Data Source│ │  Masking   │ │  Lineage   │ │   Sync   │ │
│  │ Management │ │            │ │  Analysis  │ │   Tools  │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
│  ┌────────────┐ ┌────────────┐                                │
│  │User/Perms  │ │   System   │                                │
│  │ Management │ │  Monitoring │                                │
│  └────────────┘ └────────────┘                                │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                     Backend Service Layer                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    API Gateway                          │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │  DataSrc   │ │  Masking   │ │  Lineage   │ │   Sync   │ │
│  │  Service   │ │  Service   │ │  Service   │ │  Service │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │    User    │ │  Scheduler  │ │   Audit    │              │
│  │  Service   │ │             │ │   Service  │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Access Layer                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage Layer                       │
│  ┌────────────┐ ┌────────────┐ ┌─────────────────────────┐  │
│  │  Metadata  │ │  Audit Log │ │  HashData Lightning    │  │
│  │  (PostgreSQL)││(Elasticsearch││  (MPP + Anon Plugin)  │  │
│  └────────────┘ └────────────┘ └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Technology Stack

#### Backend
- **Language**: Python 3.10+
- **Web Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 14+
- **Cache/Queue**: Redis
- **Masking Engine**: HashData Lightning + Anon Extension

#### Frontend
- **Framework**: Vue 3 + TypeScript
- **UI Component**: Ant Design Vue
- **State Management**: Pinia
- **Visualization**: ECharts + AntV G6

---

## 5. Database Design

Please refer to the source code models for complete database schema definitions.

Key tables include:
- `sys_user` - User accounts
- `sys_role` - User roles
- `sys_permission` - Permission definitions
- `datasource` - Data source configurations
- `masking_task` - Masking task definitions
- `masking_table` - Table masking configurations
- `masking_column` - Column masking configurations
- `masking_task_execution` - Task execution history
- `data_sync_task` - Data sync tasks
- `audit_log` - Audit log entries

---

## 6. API Definitions

Please refer to the Swagger/OpenAPI documentation at `/api/docs` for complete API definitions.

Key API groups include:
- `/api/v1/auth` - Authentication endpoints
- `/api/v1/datasources` - Data source management
- `/api/v1/masking` - Data masking tasks
- `/api/v1/lineage` - Data lineage analysis
- `/api/v1/sync` - Data synchronization
- `/api/v1/system` - System management (users, roles, permissions)
- `/api/v1/audit` - Audit logs

---

## 7. Security Requirements

1. **Authentication & Authorization**
   - All API endpoints require authentication (except login)
   - JWT-based token authentication
   - RBAC-based permission control

2. **Data Security**
   - Database passwords and sensitive configs encrypted (AES-256)
   - Passwords stored with bcrypt/Argon2 salted hash
   - HTTPS/TLS encrypted transmission
   - Sensitive data masked in logs

3. **Audit Requirements**
   - Record user login/logout
   - Record key business operations (create, update, delete)
   - Record data access
   - Logs retained for at least 6 months
   - Logs cannot be tampered with

---

## 8. Acceptance Criteria

### 8.1 Feature Acceptance

| Module | Item | Criteria |
|--------|------|----------|
| Data Source | CRUD Operations | All CRUD operations work properly |
| Data Source | Connection Test | Connection test validates correctly |
| Data Masking | Task Creation | Tasks can be created and executed |
| Data Masking | Algorithms | At least 6+ masking algorithms available |
| Data Masking | DB Support | Supports MPP, Oracle, MySQL, Dameng |
| Data Masking | Scheduling | Scheduled task execution works |
| Lineage | Graph Visualization | Visual lineage graph display |
| Sync | Task Execution | Sync tasks can be executed |
| User/Roles | Assignment | Multi-role assignment and adjustment |
| Audit | Logging | Complete audit trail for key operations |

### 8.2 Performance Acceptance

| Metric | Criteria |
|--------|----------|
| Page Response | <2s for normal pages, <5s for complex queries |
| Concurrent Users | 50 concurrent users supported |
| System Availability | No crashes during demo period |

---

**End of Document**
