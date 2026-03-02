# 恒丰银行数据脱敏系统

基于 HashData Lightning + Anon 插件的企业级数据脱敏平台，提供数据源管理、数据脱敏、血缘分析、翻数工具等功能。

## 功能特性

- **数据源管理**: 支持 MPP、Oracle、MySQL、达梦等多种数据源
- **数据脱敏**: 基于 HashData Lightning + Anon 插件的高性能脱敏引擎
- **血缘分析**: 可视化数据血缘关系图谱
- **翻数工具**: 高效的数据同步翻数功能
- **权限管理**: 完善的用户角色权限控制
- **审计日志**: 完整的操作审计追踪

## 技术栈

### 后端
- Python 3.10+
- FastAPI (Web框架)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (元数据存储)
- Celery + Redis (异步任务)
- HashData Lightning + Anon (脱敏引擎)

### 前端
- Vue 3 + TypeScript
- Ant Design Vue (UI组件库)
- Pinia (状态管理)
- ECharts + AntV G6 (可视化)

## 项目结构

```
data-masking-tool/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务逻辑
│   │   ├── tasks/          # 异步任务
│   │   └── utils/          # 工具类
│   ├── alembic/            # 数据库迁移
│   └── tests/              # 测试
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/            # API调用
│   │   ├── assets/         # 静态资源
│   │   ├── components/     # 公共组件
│   │   ├── layouts/        # 布局组件
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # 状态管理
│   │   ├── utils/          # 工具函数
│   │   └── views/          # 页面视图
│   └── public/
├── docs/                   # 文档
└── docker/                 # Docker配置
```

## 快速开始

### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置
alembic upgrade head
uvicorn app.main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 默认账号

- 管理员: admin / admin123

## 许可证

MIT License
