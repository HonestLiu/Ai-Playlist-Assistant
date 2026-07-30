"""密码哈希与会话令牌。

刻意只用标准库（``hashlib.pbkdf2_hmac``），不引入 bcrypt/argon2：
后者在 linux/arm/v7 上没有预编译 wheel，会拖慢甚至拖垮多架构镜像构建。
PBKDF2-SHA256 + 每用户随机 salt + 高迭代次数，对本项目的单机自托管场景足够。

存储格式（单字段，便于将来换算法）::

    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 240_000
_SALT_BYTES = 16
_TOKEN_BYTES = 32

MIN_PASSWORD_LENGTH = 6


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
    """把明文密码转成可落库的字符串。"""

    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """校验明文密码。任何格式异常一律判为失败，不抛异常。"""

    try:
        algorithm, raw_iterations, salt_hex, digest_hex = encoded.split("$")
        if algorithm != _ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(raw_iterations),
        )
    except (ValueError, AttributeError):
        return False
    # 定长比较，避免计时侧信道
    return hmac.compare_digest(digest.hex(), digest_hex)


def generate_session_token() -> str:
    """URL 安全的随机会话令牌。"""

    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """会话令牌落库前做一次 SHA-256，数据库泄露时无法直接复用 cookie。"""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
