# Cloudberry Data Management Console - Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Backend Deployment](#backend-deployment)
3. [Frontend Deployment](#frontend-deployment)
4. [HashData Lightning + Anon Configuration](#hashdata-lightning--anon-configuration)
5. [Docker Deployment](#docker-deployment)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Server Configuration
- **OS**: Linux (CentOS 7+, Ubuntu 18.04+)
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Disk**: 100GB+ free space

### Software Dependencies
- **Python**: 3.10+
- **Node.js**: 18+
- **PostgreSQL**: 14+ (for metadata storage)
- **Redis**: 6+ (for task queue and cache)
- **HashData Lightning**: (MPP database for data masking)

---

## Backend Deployment

### 1. Clone the Project
```bash
cd /opt
git clone <repository-url> data-masking-tool
cd data-masking-tool/backend
```

### 2. Create Python Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
vim .env
```

Key configuration parameters:

```env
# Application Configuration
APP_NAME=Cloudberry Data Management Console
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/data_masking

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# JWT Configuration (use strong secret in production)
JWT_SECRET_KEY=your-very-strong-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Encryption Configuration (32-byte key)
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# HashData Lightning Configuration
HASHDATA_HOST=hashdata-host
HASHDATA_PORT=5432
HASHDATA_DATABASE=hashdata
HASHDATA_USERNAME=gpadmin
HASHDATA_PASSWORD=your-password

# CORS Configuration
CORS_ORIGINS=["http://localhost","http://localhost:5173"]
```

### 5. Initialize Database
```bash
# Create database
psql -U postgres
CREATE DATABASE data_masking;
\q

# Initialize tables and data
python scripts/init_db.py
```

### 6. Start the Service
```bash
# Development
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
```

### 7. Systemd Service Management
Create `/etc/systemd/system/cloudberry-backend.service`:

```ini
[Unit]
Description=Cloudberry Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=app
WorkingDirectory=/opt/data-masking-tool/backend
Environment="PATH=/opt/data-masking-tool/backend/venv/bin"
ExecStart=/opt/data-masking-tool/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
systemctl daemon-reload
systemctl enable cloudberry-backend
systemctl start cloudberry-backend
systemctl status cloudberry-backend
```

---

## Frontend Deployment

### 1. Install Dependencies
```bash
cd /opt/data-masking-tool/frontend
npm install
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
vim .env
```

```env
VITE_API_BASE_URL=http://your-backend-host:8000/api/v1
```

### 3. Build Frontend
```bash
npm run build
```

### 4. Deploy with Nginx
Deploy the `dist` directory to Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend static files
    location / {
        root /opt/data-masking-tool/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
}
```

---

## HashData Lightning + Anon Configuration

### 1. Install Anon Extension
```sql
-- Connect to HashData Lightning
psql -h hashdata-host -p 5432 -U gpadmin -d hashdata

-- Create extension
CREATE EXTENSION IF NOT EXISTS anon CASCADE;

-- Verify installation
SELECT extversion FROM pg_extension WHERE extname = 'anon';
```

### 2. Configure Anon Extension
```sql
-- Enable dynamic masking (optional)
ALTER DATABASE hashdata SET anon.mask_function = 'anon.mask';

-- View available masking functions
\df anon.*
```

### 3. Common Anon Masking Function Examples
```sql
-- Partial masking
SELECT anon.partial_email('user@example.com');
SELECT anon.partial('13812345678', 3, 4);

-- Hash masking
SELECT anon.digest('sensitive data', 'sha256');

-- Randomization
SELECT anon.random_first_name();
SELECT anon.random_last_name();
SELECT anon.random_date_between('1970-01-01'::date, '2000-01-01'::date);

-- Noise addition
SELECT anon.add_noise(1000, 0.1);
```

---

## Docker Deployment

### Using docker-compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    container_name: cloudberry-db
    environment:
      POSTGRES_DB: data_masking
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cloudberry

  redis:
    image: redis:7-alpine
    container_name: cloudberry-redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - cloudberry

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cloudberry-backend
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/data_masking
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: your-secret-key-change-in-production
      ENCRYPTION_KEY: your-32-byte-encryption-key-here
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    networks:
      - cloudberry

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: cloudberry-frontend
    depends_on:
      - backend
    ports:
      - "80:80"
    networks:
      - cloudberry

volumes:
  postgres_data:
  redis_data:

networks:
  cloudberry:
    driver: bridge
```

### Backend Dockerfile (`backend/Dockerfile`)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p logs uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Startup command
CMD ["sh", "-c", "python scripts/init_db.py && gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app"]
```

### Frontend Dockerfile (`frontend/Dockerfile`)

```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build
COPY . .
RUN npm run build

# Runtime stage
FROM nginx:alpine

# Copy build artifacts
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Start Containers
```bash
docker-compose up -d

# View logs
docker-compose logs -f backend

# Initialize database
docker-compose exec backend python scripts/init_db.py
```

---

## Troubleshooting

### 1. Backend Startup Failure
**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Ensure you're starting from the project root or set `PYTHONPATH`:
```bash
export PYTHONPATH=/opt/data-masking-tool/backend
```

### 2. Database Connection Failure
**Problem**: `connection to server at "localhost" failed`

**Solution**: Check `DATABASE_URL` in `.env` and verify PostgreSQL is running.

### 3. HashData Connection Test Failure
**Problem**: HashData connection test fails

**Solution**:
- Check network connectivity: `telnet hashdata-host 5432`
- Verify username/password is correct
- Check HashData's `pg_hba.conf` configuration

### 4. Anon Extension Not Available
**Problem**: `function anon.partial does not exist`

**Solution**: Execute in HashData database:
```sql
CREATE EXTENSION IF NOT EXISTS anon CASCADE;
```

### 5. Frontend Page is Blank
**Problem**: Blank page when accessing

**Solution**:
- Check browser console for errors
- Verify `VITE_API_BASE_URL` is configured correctly
- Check if backend service is running

---

## Appendix

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

### Port Reference
| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI service |
| Frontend Web | 80 | Nginx service |
| PostgreSQL | 5432 | Metadata database |
| Redis | 6379 | Cache/Queue |
| HashData | 5432 | MPP database |

### Directory Structure
```
/opt/data-masking-tool/
├── backend/          # Backend service
├── frontend/         # Frontend application
├── docs/            # Documentation
└── logs/            # Log directory
```
