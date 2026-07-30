"""账号与会话的领域逻辑。

约定：本层只跟 Session（数据库会话）打交道，不认识 FastAPI 的 Request/Response，
cookie 的读写留给 API 层，方便单测与将来换成 header token。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, col, delete, func, select

from app.core.errors import AppError
from app.core.logging import get_logger
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.database.models import AppUser, AuthSession

logger = get_logger(__name__)


class AuthError(AppError):
    """凭据不正确 / 未登录。"""

    code = "unauthorized"
    status_code = 401
    message = "未登录或登录已过期"


class BootstrapClosedError(AppError):
    """已存在账号，禁止再次走「创建首个管理员」通道。"""

    code = "bootstrap_closed"
    status_code = 409
    message = "系统已完成初始化，请直接登录"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    """SQLite 取回的 datetime 不带时区，统一补成 UTC 再比较。"""

    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class AuthService:
    def __init__(self, session_ttl_hours: int = 24 * 30) -> None:
        self._ttl = timedelta(hours=session_ttl_hours)

    # ------------------------------------------------------------------ 账号
    def user_count(self, session: Session) -> int:
        return int(session.exec(select(func.count()).select_from(AppUser)).one())

    def needs_bootstrap(self, session: Session) -> bool:
        return self.user_count(session) == 0

    def get_by_username(self, session: Session, username: str) -> AppUser | None:
        normalized = username.strip().lower()
        return session.exec(
            select(AppUser).where(func.lower(AppUser.username) == normalized)
        ).first()

    def bootstrap_admin(self, session: Session, username: str, password: str) -> AppUser:
        """创建首个管理员。并发下靠「再查一次」兜底，够单机场景用。"""

        if not self.needs_bootstrap(session):
            raise BootstrapClosedError()
        user = AppUser(
            username=username.strip(),
            password_hash=hash_password(password),
            is_admin=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info("已创建管理员账号: %s", user.username)
        return user

    def change_password(
        self, session: Session, user: AppUser, current: str, new: str
    ) -> None:
        if not verify_password(current, user.password_hash):
            raise AuthError("当前密码不正确", code="invalid_credentials", status_code=400)
        user.password_hash = hash_password(new)
        session.add(user)
        # 改密即踢掉其它所有会话，调用方随后会重新签发当前设备的会话
        self.revoke_all(session, user.id or 0)
        session.commit()
        logger.info("用户 %s 已修改密码，其余会话已失效", user.username)

    # ------------------------------------------------------------------ 会话
    def authenticate(self, session: Session, username: str, password: str) -> AppUser:
        user = self.get_by_username(session, username)
        # 用户不存在时也走一次哈希校验，避免用响应时间枚举用户名
        reference = user.password_hash if user else hash_password("dummy-placeholder")
        if not verify_password(password, reference) or user is None:
            raise AuthError("用户名或密码错误", code="invalid_credentials")
        user.last_login_at = _now()
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def create_session(
        self, session: Session, user: AppUser, *, user_agent: str | None = None
    ) -> tuple[str, AuthSession]:
        """返回 (明文 token, 会话记录)。明文只在此刻出现一次，随后只存哈希。"""

        self.purge_expired(session)
        token = generate_session_token()
        record = AuthSession(
            token_hash=hash_session_token(token),
            user_id=user.id or 0,
            expires_at=_now() + self._ttl,
            user_agent=(user_agent or "")[:200] or None,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return token, record

    def resolve(self, session: Session, token: str | None) -> AppUser | None:
        """由 cookie 里的 token 反查用户。过期即顺手清理。"""

        if not token:
            return None
        record = session.exec(
            select(AuthSession).where(AuthSession.token_hash == hash_session_token(token))
        ).first()
        if record is None:
            return None
        if _aware(record.expires_at) <= _now():
            session.delete(record)
            session.commit()
            return None
        return session.get(AppUser, record.user_id)

    def revoke(self, session: Session, token: str | None) -> None:
        if not token:
            return
        record = session.exec(
            select(AuthSession).where(AuthSession.token_hash == hash_session_token(token))
        ).first()
        if record is not None:
            session.delete(record)
            session.commit()

    def revoke_all(self, session: Session, user_id: int) -> None:
        session.exec(delete(AuthSession).where(col(AuthSession.user_id) == user_id))

    def purge_expired(self, session: Session) -> None:
        session.exec(delete(AuthSession).where(col(AuthSession.expires_at) <= _now()))
        session.commit()
