# Cloudberry 数据管理平台

[English](README.md) | [中文](README_CN.md)

一个综合性的数据管理平台，提供数据脱敏、血缘分析、数据同步和数据源管理功能。基于 HashData Lightning 和 PostgreSQL Anon 扩展构建高性能数据脱敏引擎。

## 功能特性

- **数据源管理**: 支持 HashData Lightning (MPP)、PostgreSQL、MySQL、Oracle、达梦等多种数据库
- **数据脱敏**: 基于 HashData Lightning + Anon 扩展的高性能脱敏引擎，内置 72 种脱敏算法
- **血缘分析**: 可视化数据血缘图谱分析
- **数据同步**: 高效的数据同步和迁移工具
- **用户权限**: 完整的 RBAC（基于角色的访问控制）系统
- **审计日志**: 全面的操作审计追踪，记录详细的执行信息
- **SQL生成**: 自动生成脱敏任务的SQL语句，支持预览

## 技术栈

### 后端
- Python 3.10+
- FastAPI (Web框架)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (元数据存储)
- Redis (缓存/队列)
- HashData Lightning + Anon (脱敏引擎)

### 前端
- Vue 3 + TypeScript
- Ant Design Vue (UI组件库)
- Pinia (状态管理)
- AntV G6 (图谱可视化)
- ECharts (图表)

## 快速开始

### Docker 部署（推荐）

```bash
git clone <repository-url>
cd data-masking-tool
docker-compose up -d
```

访问地址：
- 前端: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/api/docs

### 手动部署

#### 后端
```bash
cd backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置相关信息
python scripts/init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 默认账号

- **用户名**: `admin`
- **密码**: `admin123`

> ⚠️ **安全提示**: 首次登录后请立即修改默认密码！

## 项目结构

```
data-masking-tool/
├── docs/                    # 文档
│   ├── SYSTEM_REQUIREMENTS.md
│   ├── DEPLOYMENT.md
│   ├── USER_GUIDE.md
│   └── PROJECT_SUMMARY.md
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   └── main.py
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── layouts/        # 布局组件
│   │   ├── router/         # 路由配置
│   │   └── stores/         # 状态管理
│   └── package.json
└── docker-compose.yml
```

## 文档

### 中文文档
- [系统需求](docs/系统需求文档.md) - 详细的系统需求和架构说明
- [部署文档](docs/部署文档.md) - 分步部署指南
- [使用说明](docs/使用说明.md) - 完整的用户手册
- [项目总结](docs/项目总结.md) - 项目概述和功能介绍

### English Documentation
- [System Requirements](docs/SYSTEM_REQUIREMENTS.md) - Detailed system requirements and architecture
- [Deployment Guide](docs/DEPLOYMENT.md) - Step-by-step deployment instructions
- [User Guide](docs/USER_GUIDE.md) - Complete user manual
- [Project Summary](docs/PROJECT_SUMMARY.md) - Project overview and features

## 脱敏算法

系统内置 72 种脱敏算法，分为 8 大类：

| 分类 | 算法示例 | 说明 |
|------|----------|------|
| 假数据生成 | fake_address, fake_city, fake_country, fake_email 等 | 生成逼真的假数据 |
| 随机值 | random_int, random_string, random_date 等 | 生成随机数据 |
| 部分混淆 | partial, partial_email, partial_phone | 保留部分信息的掩码 |
| 假名化 | pseudo_first_name, pseudo_last_name | 确定性假名替换 |
| 哈希 | digest, hash | 单向哈希转换 |
| 噪声 | add_noise, add_noise_numeric | 添加随机噪声 |
| 泛化 | generalize_date, generalize_number | 将精确值泛化为范围 |
| 条件脱敏 | MASK, REPLACE, NULL, ROUND, OFFSET | 条件脱敏操作符 |

### 核心特性

- **SQL生成**: 自动生成脱敏任务的SQL语句
- **执行详情**: 查看详细的执行日志，包括执行时长和记录数
- **审计日志**: 完整的操作追踪，记录成功/失败状态
- **类型感知脱敏**: 自动检测数值类型，正确处理替换值

## API 参考

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/current-user` | GET | 获取当前用户信息 |
| `/api/v1/datasources` | GET/POST | 数据源列表/创建 |
| `/api/v1/datasources/{id}/test-connection` | POST | 测试数据源连接 |
| `/api/v1/datasources/{id}/tables` | GET | 获取表列表 |
| `/api/v1/masking/tasks` | GET/POST | 脱敏任务列表/创建 |
| `/api/v1/masking/tasks/{id}/execute` | POST | 执行脱敏任务 |
| `/api/v1/masking/tasks/{id}/generate-sql` | POST | 生成脱敏SQL |
| `/api/v1/masking/executions/{id}/logs` | GET | 获取执行详情 |
| `/api/v1/masking/algorithms` | GET | 获取算法列表 |
| `/api/v1/audit/logs` | GET | 获取审计日志 |

## 测试

运行完整的测试套件：

```bash
cd backend
source venv/bin/activate
python ../test_all_features.py
```

## 贡献

欢迎贡献代码！请随时提交问题和拉取请求。

## 许可证

MIT License
