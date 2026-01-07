# 项目说明文档

这是一个基于 [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template) 的全栈 Web 应用模板。它集成了现代化的后端和前端技术栈，并提供了完善的 Docker 容器化部署方案。

## 📚 技术栈

### 后端 (Backend)
- **FastAPI**: 高性能的 Python Web 框架。
- **SQLModel**: 基于 Python 类型提示的 SQL 数据库交互 (ORM)，结合了 SQLAlchemy 和 Pydantic。
- **Pydantic**: 数据验证和设置管理。
- **PostgreSQL**: 强大的开源关系型数据库。
- **Celery** (可选): 异步任务队列 (如果项目中包含)。
- **Docker**: 容器化应用。

### 前端 (Frontend)
- **React**: 用于构建用户界面的 JavaScript 库。
- **TypeScript**: 强类型的 JavaScript 超集。
- **Vite**: 极速的前端构建工具。
- **Tailwind CSS**: 实用优先的 CSS 框架。
- **Shadcn/ui**:基于 Radix UI 和 Tailwind CSS 的可重用组件库。
- **TanStack Router**: 现代化的 React 路由解决方案。
- **TanStack Query**: 强大的异步状态管理。
- **OpenAPI TS**: 根据后端 OpenAPI 规范自动生成前端客户端代码。

### 基础设施与工具
- **Docker Compose**: 本地开发和多容器编排。
- **Nginx / Traefik**: 反向代理和负载均衡。
- **Adminer**: 数据库管理界面。
- **Mailcatcher**: 本地开发时的邮件测试服务。

## 🚀 快速启动 (Docker 方式)

这是最简单的启动方式，适合快速预览和开发。

### 1. 克隆项目
```bash
git clone <repository-url>
cd full-stack-fastapi-template
```

### 2. 配置环境变量
项目根目录下有一个 `.env` 文件，其中包含了数据库密码、密钥等配置。
首次使用时，你可以直接使用默认值，但建议修改以下关键变量（特别是生产环境）：
- `SECRET_KEY`: 后端密钥。
- `FIRST_SUPERUSER_PASSWORD`: 初始管理员密码。
- `POSTGRES_PASSWORD`: 数据库密码。

生成安全密钥的命令：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. 启动服务
使用 Docker Compose 启动所有服务：

```bash
docker compose watch
```
*注意：`watch` 模式会监听文件变化并自动同步到容器中，非常适合开发。*

### 4. 访问服务
启动成功后，可以通过以下地址访问：

- **前端面板**: [http://localhost:5173](http://localhost:5173)
- **后端 API 文档 (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **后端 API 文档 (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **数据库管理 (Adminer)**: [http://localhost:8080](http://localhost:8080)
- **邮件测试 (Mailcatcher)**: [http://localhost:1080](http://localhost:1080) (SMTP 端口: 1025)
- **Traefik 仪表盘**: [http://localhost:8090](http://localhost:8090)

初始管理员账号通常在 `.env` 文件中定义：
- 邮箱: `admin@example.com`
- 密码: `changethis` (请查看你的 .env 文件确认)

## 📂 项目结构

```
.
├── backend/            # Python FastAPI 后端代码
│   ├── app/            # 应用源码 (API, Models, CRUD 等)
│   ├── alembic/        # 数据库迁移脚本
│   └── tests/          # 后端测试
├── frontend/           # React 前端代码
│   ├── src/            # 源码 (Components, Routes, Hooks 等)
│   └── client/         # 自动生成的 API 客户端代码
├── scripts/            # 辅助脚本 (构建, 测试, 部署等)
├── .env                # 环境变量配置
├── docker-compose.yml  # Docker 编排文件
└── README.md           # 原始英文文档
```

## 🚢 部署 (Deployment)

项目支持使用 Docker Compose 进行生产环境部署。

1. **修改域名**: 在 `.env` 文件中设置 `DOMAIN` 变量为你的实际域名。
2. **构建镜像**: 运行 `./scripts/build.sh` 构建生产镜像。
3. **启动服务**: 使用 `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` (具体命令可能根据 CI/CD 流程有所不同，通常由 GitHub Actions 处理)。

详细部署指南请参考 `deployment.md` (英文) 或相关 CI/CD 配置文件。
