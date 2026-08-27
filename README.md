# 毛仔天气 - 气象数据应用系统

对接中国气象数据网（CIMISS/天擎）官方 API，提供 Web 管理端 + Android App 双端服务。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python FastAPI + SQLAlchemy + APScheduler |
| Web 前端 | Vue3 + Element Plus + Vite + Pinia |
| Android | Kotlin + Jetpack Compose |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis 7 |
| 部署 | Docker Compose |

## 项目结构

```
maozi-weather/
├── backend/          # FastAPI 后端服务
├── web-admin/        # Vue3 Web 管理端
├── android-app/      # Kotlin Android App
├── docker/           # Docker 相关配置
├── mysql/            # MySQL 初始化脚本
├── docs/             # 项目文档
└── docker-compose.yml
```

## 快速开始

### 1. 启动基础服务（MySQL + Redis）

```bash
docker-compose up -d mysql redis
```

### 2. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 配置数据库连接等

# 建表与初始数据（管理员账号、全国城市库）：
docker-compose up -d mysql redis   # 若尚未启动
docker exec -i $(docker-compose ps -q mysql) mysql -uroot -p < ../mysql/init/01_init.sql

uvicorn app.main:app --reload --host 0.0.0.0 --port 60245
```

> alembic 已列入依赖但迁移目录尚未建立；当前以 `mysql/init/01_init.sql` 作为唯一建表入口。

后端启动后访问：
- API 文档：http://localhost:60245/docs
- 健康检查：http://localhost:60245/health

### 3. 启动 Web 管理端

```bash
cd web-admin
npm install
npm run dev
```

访问：http://localhost:60240

### 4. Android App

使用 Android Studio 打开 `android-app/` 目录。

## 核心功能

- 用户账号体系（JWT 鉴权）
- 关注城市/站点管理
- 实时天气（实况、预报、预警）
- 历史气象数据存储与同步
- 气象数据分析与可视化
- 系统监控与日志
- Android 桌面小组件 + 预警推送

## 安全约束

- 前端不直接调用 CMA API，全部走后端代理
- appid/appsecret 加密存储在后端
- 所有业务接口需要 JWT 鉴权
- QPS ≤ 10，批量任务限速

## 数据来源

数据来源：中国气象数据网（data.cma.cn）
