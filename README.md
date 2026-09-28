# 毛仔天气 - 气象数据应用系统

多源气象数据聚合应用，提供 Web 管理端 + Android App 双端服务。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python FastAPI + SQLAlchemy + APScheduler |
| Web 前端 | Vue3 + Element Plus + Vite + Pinia + ECharts |
| Android | Kotlin + Jetpack Compose + Glance + Room + WorkManager |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis 7 |
| 部署 | 服务器裸机部署（uvicorn + nginx），备用 Docker Compose |

## 项目结构

```
maozi-weather/
├── backend/          # FastAPI 后端服务
├── web-admin/        # Vue3 Web 管理端
├── android-app/      # Kotlin Android App
├── docker/           # Docker 相关配置（备用）
├── mysql/            # MySQL 初始化脚本
├── docs/             # 项目文档
└── docker-compose.yml
```

## 数据来源（如实）

- **主源：Open-Meteo**（免费、无需 Key）——实况/16天预报/逐小时/15分钟临近降水/空气质量/历史
- **备源：和风天气**（需 Key，可选）——主源失败时兜底
- 中国气象数据网（CIMISS/天擎）预留了客户端代码但**未接入**，`CMA_*` 配置暂不生效
- 空气质量 AQI 为国标口径（由污染物浓度按 GB 3095 计算，非 Open-Meteo 欧标原值）

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

使用 Android Studio 打开 `android-app/` 目录，或直接从 GitHub Actions 产物 / 服务器
`http://<server>:60240/maozi-weather.apk` 下载 debug 包。

## 核心功能

- 用户账号体系（JWT 鉴权）；App 默认游客免登录（可定位自动选城市），管理后台用账号登录
- 默认管理员：`admin / admin123`（见 `mysql/init/01_init.sql`）
- 关注城市/站点管理
- 实时天气（实况、7天/逐小时/15分钟临近预报、预警、国标 AQI、生活指数、日出日落）
- 实况快照落库（`weather_realtime` 表，每城市最新一条）
- 历史气象数据存储与同步、数据分析可视化
- 系统监控与日志
- Android：详情页温度曲线、降水提醒推送、气象预警推送、桌面小组件（点击打开 App）、离线缓存

## 安全约束

- 前端不直接调用上游气象 API，全部走后端代理
- appid/appsecret 加密存储在后端
- 除 `/api/public/*` 外所有业务接口需 JWT 鉴权；公开接口有 Redis 缓存 + IP 限流
- 上游 QPS ≤ 10，批量任务限速

## 服务器部署（120.48.13.152）

- 后端：`/opt/maozi-weather/backend`，venv + uvicorn 端口 60245，日志 `/var/log/maozi-weather.log`
- 前端：`web-admin/dist` 由 nginx 托管端口 60240，`/api/` 反代 60245；APK 同目录静态下载
- MySQL/Redis 使用服务器系统服务（非 Docker）
- 更新流程：`git pull` → 重启 uvicorn →（前端）本地 build 后 rsync `dist/`

## 数据来源说明

数据来源：Open-Meteo（https://open-meteo.com ）+ 和风天气（备源）
