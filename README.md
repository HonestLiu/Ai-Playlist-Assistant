# AI 音乐歌单助手（Subsonic + AI）

连接 Subsonic 音乐服务器，用大模型按自然语言生成歌单，并支持每日 Daily Mix。

当前进度：**Phase 1 · 基础框架已完成**。

---

## 目录结构

```text
server/                 # Python 服务端
  app/
    api/                # 路由层：只做入参校验与 DTO 转换
      v1/               # 版本化路由
      deps.py           # 依赖注入装配点
    core/               # 横切关注点：配置 / 日志 / 异常
    database/           # 持久化：Phase 1 是 JSON 配置存储，Phase 2 换 SQLModel
    models/             # 领域模型（值对象）
    schemas/            # API 传输结构（DTO）
    services/           # 用例层：业务编排
    subsonic/           # 防腐层：唯一允许发 Subsonic HTTP 请求的地方
    ai/                 # Phase 3
    scheduler/          # Phase 4
    utils/              # 纯函数工具
web/                    # React 前端
  src/
    components/ui/      # 基础组件（shadcn 风格）
    components/layout/  # 布局
    pages/              # 页面
    hooks/              # 数据层 hook（TanStack Query）
    services/           # HTTP 出口
    stores/             # 客户端状态（zustand）
    types/              # 与后端 schema 对应的类型
```

## 架构约束

1. **依赖方向单向**：`api → services → subsonic/database`，反向依赖一律禁止。
2. **HTTP 隔离**：业务代码不允许直接请求 Subsonic，只能通过 `SubsonicClient`。
3. **配置集中**：服务端一切配置经 `app.core.config.get_settings()` 读取，禁止散落的 `os.environ`。
4. **错误统一**：所有对外异常继承 `AppError`，前端只解析 `{ code, message, detail }`。
5. **前端分层**：组件 → hook → service → `request()`，组件里不出现 `fetch`。

## 本地运行（macOS）

一次性初始化：

```bash
make setup
```

然后编辑 `server/.env`，至少填写：

```bash
SUBSONIC__URL=https://your-navidrome.example.com
SUBSONIC__USERNAME=your-username
SUBSONIC__PASSWORD=your-password
```

分别启动两个终端：

```bash
make server   # http://127.0.0.1:8000  （API 文档 /docs）
make web      # http://localhost:5173
```

前端 dev server 会把 `/api` 代理到后端，因此浏览器侧没有跨域问题；
未来同源部署时代码无需改动。

也可以不改 `.env`，直接在网页「设置」页填连接信息并保存，
运行时配置会写入 `server/data/runtime_config.json` 并覆盖 `.env` 默认值。

## Docker 部署（多架构）

单镜像同时提供 API 与 Web（后端托管 `web/dist`，`SERVER__WEB_DIST` 控制）。

```bash
# 本地构建（宿主架构）
docker build -t ai-playlist .

# 运行：数据（SQLite / 运行时配置）挂卷持久化
docker run -d --name ai-playlist \
  -p 8000:8000 \
  -v ai-playlist-data:/app/data \
  -e TZ=Asia/Shanghai \
  ai-playlist
# 打开 http://localhost:8000 即可使用（含 Web 界面）
```

### GitHub Actions 自动构建

`.github/workflows/docker.yml` 会构建三个平台的镜像并推送到 GHCR：

| 平台 | 适用场景 |
| --- | --- |
| `linux/amd64` | 常规 x64 Linux 服务器 |
| `linux/arm64` | Apple Silicon 跑 Linux 容器、树莓派 4+（64 位）、ARM 云主机 |
| `linux/arm/v7` | 常规 32 位 ARM Linux（树莓派 2/3、旧款 NAS 等） |

触发规则：push `main` → `latest` + `sha-xxxxxxx`；打 tag `v1.2.3` → `1.2.3` / `1.2` / `1`；PR 仅验证构建不推送；也可手动触发（可勾选是否推送）。

```bash
docker pull ghcr.io/<owner>/<repo>:latest   # 自动匹配本机架构
```

## Phase 1 已实现的接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/health` | 服务健康检查 |
| GET | `/api/v1/settings/subsonic` | 读取当前连接配置（密码不返回） |
| PUT | `/api/v1/settings/subsonic` | 保存连接配置 |
| DELETE | `/api/v1/settings/subsonic` | 清除网页配置，回落到 `.env` |
| POST | `/api/v1/settings/subsonic/test` | 测试连接（不保存） |
| GET | `/api/v1/subsonic/status` | 当前连接状态 |

## 路线图

- **Phase 2**：音乐库同步（歌曲 / 专辑 / 艺术家），引入 SQLModel + SQLite。
- **Phase 3**：统一 LLM Provider（OpenAI 兼容 / Gemini / Claude / Ollama）、Prompt 管理、AI 推荐与建歌单。
- **Phase 4**：APScheduler 定时任务，多个 Daily Mix 自动生成与轮换。
- **Phase 5**：UI 打磨、缓存、日志与性能优化。
