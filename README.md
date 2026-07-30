# AI 音乐歌单助手（Subsonic + AI）

连接 Subsonic 音乐服务器，用大模型按自然语言生成歌单，并支持每日 Daily Mix。

当前进度：**Phase 7 · 登录校验 + 容器启动引导已完成**（账号体系 / 会话 / 首次启动向导）。

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

然后启动两个终端：

```bash
make server   # http://127.0.0.1:8000  （API 文档 /docs）
make web      # http://localhost:5173
```

首次打开网页会进入**启动引导（Onboarding Wizard）**，按四步完成配置，无需手改 `.env`：

1. **创建管理员账号** —— 设置登录用户名 / 密码（密码至少 6 位）。
2. **配置音乐服务器** —— 填写 Subsonic 服务器地址、用户名、密码并测试连接。
3. **配置 AI 模型** —— 选择 OpenAI 兼容 / Mock，填 API Key 与模型名。
4. **同步曲库 + 完成** —— 一键把服务器曲库索引到本地，AI 才能据此选歌。

引导完成后写入 `server/data/app.db`（账号 / 会话）与 `server/data/runtime_config.json`（服务器 / AI 配置）。
也可以不跑引导、直接在 `server/.env` 里预填好配置（见下方「登录与启动引导」），
但**管理员账号必须在引导里创建**（或在已登录后于「设置 → 账号」修改密码）。

前端 dev server 会把 `/api` 代理到后端，因此浏览器侧没有跨域问题；
未来同源部署时代码无需改动。

> 注：`.env` 里的 `SUBSONIC__*` / `LLM__*` 仍可作为默认值在引导中预填与覆盖。

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

## 登录与启动引导（Phase 7）

系统默认开启登录校验。鉴权使用 **HttpOnly Cookie 会话**（非 Bearer Header），
原因是浏览器对 `<audio src>` 串流和封面 `<img>` 发起的请求无法附加 `Authorization` 头，
Cookie 才能让播放器 / 封面在已登录状态下正常放行、未登录时被中间件拦截。

核心行为：

- **未初始化（数据库无管理员账号）**：访问任何受保护接口返回 `401 { code: "needs_bootstrap" }`，
  前端自动跳到引导页 `/setup`。
- **已初始化但未登录**：返回 `401 { code: "unauthorized" }`，前端跳到 `/login`。
- **引导四步**完成后，系统标记 `onboarding_completed`，之后直接进入主界面。
- 会话令牌只把 **SHA-256 哈希**落库，明文 token 仅在签发瞬间出现一次，可随时吊销；
  修改密码会自动吊销其它设备的会话。

### 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AUTH__ENABLED` | `true` | 是否开启登录校验；设 `false` 则所有人免登录（开发 / 内网可信环境） |
| `AUTH__SESSION_TTL_HOURS` | `720` | 会话有效期（小时），即 30 天 |
| `AUTH__COOKIE_NAME` | `apa_session` | Cookie 名称 |
| `AUTH__COOKIE_SECURE` | `false` | 生产 HTTPS 部署建议设 `true` |
| `AUTH__COOKIE_SAMESITE` | `lax` | 同站策略 |

密码哈希使用标准库 `hashlib.pbkdf2_hmac`（PBKDF2-SHA256，24 万迭代，每用户随机 salt），
**不引入 bcrypt / argon2**，以保证 `linux/arm/v7` 等多架构镜像能正常构建（这些平台缺预编译 wheel）。

### Docker 部署时初始化

容器首次启动（数据卷为空）即进入引导流程。用浏览器打开 `http://localhost:8000`
走完四步即可。若通过 Docker 运行且不想用网页引导，也可在 `docker run -e` 里预填
`SUBSONIC__*` / `LLM__*` 与 `AUTH__*`，但仍需在网页完成一次管理员账号创建。

### 重置引导 / 忘记管理员密码

```bash
# 进入容器或本地 server 目录，清空账号与会话（曲库 / 配置保留）
rm -f server/data/app.db
# 重启服务后将再次进入引导，重新创建管理员账号
```

忘记密码且仍能登录时，可在「设置 → 账号」修改；完全遗忘则需按上一步重建账号。

## 已实现的接口（摘要）

> 完整接口见 `/docs`（Swagger）。以下为与鉴权 / 引导相关的新增端点：
>
> | 方法 | 路径 | 说明 |
> | --- | --- | --- |
> | GET | `/api/v1/auth/session` | 前端鉴权网关唯一数据源（是否启用 / 是否需引导 / 是否已登录） |
> | POST | `/api/v1/auth/bootstrap` | 创建首个管理员账号并签发会话（仅限未初始化时） |
> | POST | `/api/v1/auth/login` | 登录，签发 HttpOnly Cookie |
> | POST | `/api/v1/auth/logout` | 登出，吊销当前会话 |
> | POST | `/api/v1/auth/password` | 修改密码（自动吊销其它设备会话） |
> | GET | `/api/v1/setup/status` | 引导各步进度聚合 |
> | POST | `/api/v1/setup/complete` | 落盘 onboarding 完成标记 |

### Phase 1 基础接口



| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/health` | 服务健康检查 |
| GET | `/api/v1/settings/subsonic` | 读取当前连接配置（密码不返回） |
| PUT | `/api/v1/settings/subsonic` | 保存连接配置 |
| DELETE | `/api/v1/settings/subsonic` | 清除网页配置，回落到 `.env` |
| POST | `/api/v1/settings/subsonic/test` | 测试连接（不保存） |
| GET | `/api/v1/subsonic/status` | 当前连接状态 |

## 路线图

已完成：**Phase 1** 基础框架 · **Phase 2** 音乐库同步（SQLModel + SQLite）· **Phase 3** 统一 LLM Provider 与 AI 建歌单 · **Phase 4** APScheduler 每日推荐 · **Phase 5** UI 打磨 · **Phase 6** 多架构 Docker + CI · **Phase 7** 登录校验 + 容器启动引导。

后续可考虑：

- 多用户 / 角色（当前为单管理员模型）。
- 第三方登录（OIDC / 反向代理鉴权透传）。
- 引导中「同步曲库」的进度实时推送（SSE / WebSocket）。
