# 开发文档 (Development Guide)

本文档旨在指导开发者如何在本地环境中进行后端和前端的开发、调试与测试。

## 🛠️ 环境准备

在开始之前，请确保你的机器上安装了以下工具：

- **Docker & Docker Compose**: 运行数据库和其他基础设施。
- **Python 3.10+**: 后端开发语言。
- **Node.js 18+**: 前端开发环境。
- **uv**: 现代化的 Python 包管理器 (推荐) 或 Poetry。
- **npm / pnpm / yarn**: Node 包管理器。

## 💻 本地开发模式

通常我们推荐 **混合模式** 进行开发：
- 使用 Docker 运行数据库 (PostgreSQL)、邮件服务 (Mailcatcher) 等基础设施。
- 在本地直接运行后端 (FastAPI) 和前端 (Vite) 服务，以便获得最快的开发反馈（如热重载、调试器支持）。

### 1. 启动基础设施
只启动数据库和其他辅助服务，不启动后端和前端容器：

```bash
# 停止所有正在运行的容器
docker compose down

# 启动数据库和辅助服务 (根据 docker-compose.yml 的具体服务名调整)
docker compose up -d db mailcatcher adminer
```

### 2. 后端开发 (Backend)

进入 `backend` 目录：
```bash
cd backend
```

#### 安装依赖
使用 `uv` 安装依赖 (如果使用其他工具请相应调整)：
```bash
uv sync
```

#### 激活虚拟环境
```bash
source .venv/bin/activate
```

#### 运行数据库迁移
确保数据库是最新的：
```bash
# 首次运行前可能需要运行预启动脚本
bash scripts/prestart.sh

# 或者手动运行 alembic
alembic upgrade head
```

#### 启动后端服务
```bash
fastapi dev app/main.py
```
后端服务将在 [http://localhost:8000](http://localhost:8000) 启动。

### 3. 前端开发 (Frontend)

进入 `frontend` 目录：
```bash
cd frontend
```

#### 安装依赖
```bash
npm install
```

#### 启动前端服务
```bash
npm run dev
```
前端服务将在 [http://localhost:5173](http://localhost:5173) 启动。

## 🔄 前后端联调与代码生成

前端使用了 `openapi-ts` 根据后端的 OpenAPI 规范自动生成 TypeScript 客户端代码。

当你修改了后端的 API (例如修改了 Pydantic 模型或路由) 后，前端需要更新客户端代码：

1. 确保后端服务正在运行 (`localhost:8000`)。
2. 在 `frontend` 目录下运行：
   ```bash
   npm run generate-client
   ```
这将会更新 `frontend/src/client` 下的代码，使前端能获得最新的类型提示和 API 方法。

## 🗄️ 数据库管理

- **GUI 工具**: 访问 [http://localhost:8080](http://localhost:8080) (Adminer) 管理数据库。
  - System: PostgreSQL
  - Server: `db` (如果在 Docker 网络内) 或 `localhost` (如果端口映射到了主机)
  - Username/Password: 查看 `.env` 文件

- **迁移 (Alembic)**:
  - 创建新迁移 (修改模型后):
    ```bash
    # 在 backend 目录下
    alembic revision --autogenerate -m "Add new table"
    ```
  - 应用迁移:
    ```bash
    alembic upgrade head
    ```

## 🧪 测试

### 后端测试
使用 `pytest` 运行测试：
```bash
# 在 backend 目录下
bash scripts/test.sh
# 或者直接运行 pytest
pytest
```

### 前端测试
前端通常包含单元测试和 E2E 测试 (Playwright)。
```bash
# 运行单元测试
npm run test

# 运行 E2E 测试 (需要先启动服务)
npx playwright test
```

## 🧹 代码规范 (Linting & Formatting)

项目配置了 Pre-commit 钩子或类似工具来保证代码质量。

### 后端
通常使用 `ruff` 进行格式化和 Lint 检查。
```bash
bash scripts/lint.sh
bash scripts/format.sh
```

### 前端
使用 `Biome` 或 `ESLint` + `Prettier`。
```bash
npm run lint
npm run format
```

## 常见问题

**Q: 数据库连接失败？**
A: 检查 Docker 容器 `db` 是否正常运行。检查 `.env` 中的 `POSTGRES_SERVER` 地址。如果在本地运行后端（非 Docker），`POSTGRES_SERVER` 应设为 `localhost`；如果在 Docker 容器内运行后端，应设为 `db`。

**Q: 前端无法连接后端？**
A: 检查浏览器的网络请求。默认情况下前端代理配置在 `vite.config.ts` 或通过环境变量 `VITE_API_URL` 设置。确保后端服务在 `http://localhost:8000` 可访问，并且处理了 CORS (如果前后端端口不同)。
