# ============================================================
# AI Playlist Assistant — 单镜像（API + Web）多架构构建
# 支持平台：linux/amd64 / linux/arm64 (Apple Silicon) / linux/arm/v7
# ============================================================

# ---------- 阶段 1：构建前端 ----------
# 前端产物是纯静态文件、与目标架构无关，固定在 BUILDPLATFORM 上构建，
# 避免 QEMU 模拟下跑 node 导致构建极慢。
FROM --platform=$BUILDPLATFORM node:22-bookworm-slim AS web-builder

WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY web/ ./
RUN npm run build

# ---------- 阶段 2：Python 依赖 ----------
FROM python:3.13-slim-bookworm AS py-deps

WORKDIR /app
COPY server/requirements.txt ./

# armv7 下部分包可能没有预编译 wheel，装上最小构建工具兜底
RUN --mount=type=cache,target=/root/.cache/pip \
    apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --prefix=/install -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# ---------- 阶段 3：运行时 ----------
FROM python:3.13-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="AI Playlist Assistant" \
      org.opencontainers.image.description="Subsonic + LLM 智能歌单助手（API + Web 单镜像）"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SERVER__HOST=0.0.0.0 \
    SERVER__PORT=8000 \
    SERVER__WEB_DIST=/app/web-dist \
    TZ=Asia/Shanghai

WORKDIR /app

# 非 root 运行
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

COPY --from=py-deps /install /usr/local
COPY server/app ./app
COPY --from=web-builder /build/web/dist ./web-dist

# 数据目录（SQLite / 运行时配置）默认位于容器内部 /app/data。
# 镜像【不声明 VOLUME】，便于「NAS Docker 不支持卷配置」的场景直接运行：
# 数据随容器保留（stop/start、重启都不丢，仅 docker rm 重建容器时清空）。
# 需要持久化到宿主机时，可在运行期用 -e APP_DATA_DIR=/your/path 指向已挂载目录，
# 或直接 -v /host/path:/app/data 挂载（支持卷的环境）。
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,os,sys; \
        sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"SERVER__PORT\",\"8000\")}/api/v1/health', timeout=4).status == 200 else 1)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
