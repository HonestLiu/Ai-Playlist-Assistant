"""数据库引擎与会话。

- 使用 SQLite（文件落在 ``{data_dir}/app.db``），``check_same_thread=False`` 以适配
  FastAPI 的线程池。
- ``init_db()`` 在建表；迁移 PostgreSQL 时只改 ``_engine`` 这一行。
- ``get_session`` 是 FastAPI 的依赖项，每个请求一个 Session，自动关闭。
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

_settings = get_settings()
_db_file = _settings.data_dir / "app.db"
_engine = create_engine(
    f"sqlite:///{_db_file}",
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """创建所有表。模型必须在此前导入以注册到 metadata。"""

    from app.database import models  # noqa: F401

    SQLModel.metadata.create_all(_engine)


def get_session() -> Iterator[Session]:
    """FastAPI 依赖：每个请求一个会话，结束自动关闭。"""

    with Session(_engine) as session:
        yield session
