# Cloudberry Data Management Console

[English](README.md) | [中文](README_CN.md)

A comprehensive data management platform featuring data masking, lineage analysis, data synchronization, and data source management. Built with HashData Lightning and PostgreSQL Anon extension for high-performance data masking.

## Features

- **Data Source Management**: Support for HashData Lightning (MPP), PostgreSQL, MySQL, Oracle, Dameng and more
- **Data Masking**: High-performance masking engine based on HashData Lightning + Anon extension with 72 built-in algorithms
- **Data Lineage**: Visual data lineage analysis with graph visualization
- **Data Sync**: Efficient data synchronization and migration tools
- **User & Permission**: Complete RBAC (Role-Based Access Control) system
- **Audit Log**: Comprehensive operation audit trail with detailed execution records
- **SQL Generation**: Automatic SQL generation for masking tasks with preview capability

## Tech Stack

### Backend
- Python 3.10+
- FastAPI (Web Framework)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Metadata Storage)
- Redis (Cache/Queue)
- HashData Lightning + Anon (Masking Engine)

### Frontend
- Vue 3 + TypeScript
- Ant Design Vue (UI Component Library)
- Pinia (State Management)
- AntV G6 (Graph Visualization)
- ECharts (Charts)

## Quick Start

### Docker (Recommended)

```bash
git clone <repository-url>
cd data-masking-tool
docker-compose up -d
```

Access the application:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Manual Setup

#### Backend
```bash
cd backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python scripts/init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

> ⚠️ **Security Warning**: Please change the default password immediately after first login!

## Project Structure

```
data-masking-tool/
├── docs/                    # Documentation
│   ├── SYSTEM_REQUIREMENTS.md
│   ├── DEPLOYMENT.md
│   ├── USER_GUIDE.md
│   └── PROJECT_SUMMARY.md
├── backend/                 # Backend Service
│   ├── app/
│   │   ├── api/            # API Routes
│   │   ├── core/           # Core Configuration
│   │   ├── models/         # Data Models
│   │   ├── schemas/        # Pydantic Schemas
│   │   ├── services/       # Business Logic
│   │   └── utils/          # Utilities
│   └── main.py
├── frontend/               # Frontend Application
│   ├── src/
│   │   ├── views/          # Page Components
│   │   ├── layouts/        # Layout Components
│   │   ├── router/         # Router Configuration
│   │   └── stores/         # State Management
│   └── package.json
└── docker-compose.yml
```

## Documentation

### English
- [System Requirements](docs/SYSTEM_REQUIREMENTS.md) - Detailed system requirements and architecture
- [Deployment Guide](docs/DEPLOYMENT.md) - Step-by-step deployment instructions
- [User Guide](docs/USER_GUIDE.md) - Complete user manual
- [Project Summary](docs/PROJECT_SUMMARY.md) - Project overview and features

### 中文文档
- [系统需求](docs/系统需求文档.md) - 详细的系统需求和架构说明
- [部署文档](docs/部署文档.md) - 分步部署指南
- [使用说明](docs/使用说明.md) - 完整的用户手册
- [项目总结](docs/项目总结.md) - 项目概述和功能介绍

## Masking Algorithms

The system includes 72 pre-built masking algorithms across 8 categories:

| Category | Algorithms | Description |
|----------|------------|-------------|
| FAKE | fake_address, fake_city, fake_country, fake_email, etc. | Generate realistic fake data |
| RANDOM | random_int, random_string, random_date, etc. | Generate random values |
| PARTIAL | partial, partial_email, partial_phone | Partial masking with wildcards |
| PSEUDO | pseudo_first_name, pseudo_last_name | Deterministic pseudonym substitution |
| HASH | digest, hash | One-way hash transformation |
| NOISE | add_noise, add_noise_numeric | Add random noise |
| GENERALIZE | generalize_date, generalize_number | Convert exact values to ranges |
| CONDITIONAL | MASK, REPLACE, NULL, ROUND, OFFSET | Conditional masking operators |

### Key Features

- **SQL Generation**: Automatically generate SQL statements for masking tasks
- **Execution Details**: View detailed execution logs including duration and record counts
- **Audit Logging**: Complete operation trail with success/failure tracking
- **Type-aware Masking**: Automatic detection of numeric types for replacement values

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/current-user` | GET | Get current user info |
| `/api/v1/datasources` | GET/POST | List/create data sources |
| `/api/v1/datasources/{id}/test-connection` | POST | Test data source connection |
| `/api/v1/datasources/{id}/tables` | GET | Get table list |
| `/api/v1/masking/tasks` | GET/POST | List/create masking tasks |
| `/api/v1/masking/tasks/{id}/execute` | POST | Execute masking task |
| `/api/v1/masking/tasks/{id}/generate-sql` | POST | Generate masking SQL |
| `/api/v1/masking/executions/{id}/logs` | GET | Get execution details |
| `/api/v1/masking/algorithms` | GET | Get algorithm list |
| `/api/v1/audit/logs` | GET | Get audit logs |

## Testing

Run the comprehensive test suite:

```bash
cd backend
source venv/bin/activate
python ../test_all_features.py
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License
