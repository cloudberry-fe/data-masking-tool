# Cloudberry Data Management Console

A comprehensive data management platform featuring data masking, lineage analysis, data synchronization, and data source management. Built with HashData Lightning and PostgreSQL Anon extension for high-performance data masking.

## Features

- **Data Source Management**: Support for HashData Lightning (MPP), PostgreSQL, MySQL, Oracle, Dameng and more
- **Data Masking**: High-performance masking engine based on HashData Lightning + Anon extension
- **Data Lineage**: Visual data lineage analysis with graph visualization
- **Data Sync**: Efficient data synchronization and migration tools
- **User & Permission**: Complete RBAC (Role-Based Access Control) system
- **Audit Log**: Comprehensive operation audit trail

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

- [System Requirements](docs/SYSTEM_REQUIREMENTS.md) - Detailed system requirements and architecture
- [Deployment Guide](docs/DEPLOYMENT.md) - Step-by-step deployment instructions
- [User Guide](docs/USER_GUIDE.md) - Complete user manual
- [Project Summary](docs/PROJECT_SUMMARY.md) - Project overview and features

## Masking Algorithms

The system includes 10 pre-built masking algorithms:

| Algorithm | Description | Use Case |
|-----------|-------------|----------|
| MASK | Partial masking with wildcard | Phone, ID card |
| HASH | SHA-256 one-way hash | Unique identifiers |
| REPLACE | Fixed value replacement | Sensitive fields |
| NULL | Set to NULL | Unneeded fields |
| ROUND | Numeric rounding | Amount, age |
| OFFSET | Numeric offset | Age, date |
| SHUFFLE | Column shuffling | Randomization |
| SUBSTITUTION | Dictionary substitution | Realistic fake data |
| PRESERVATION | Format-preserving | Names, addresses |
| ENCRYPT | Reversible encryption | Secure storage |

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License
