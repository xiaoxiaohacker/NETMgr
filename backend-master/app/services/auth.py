"""
认证服务模块
此模块整合了统一的认证功能，确保系统使用一致的认证方式
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

# 导入统一的认证工具和配置
# 直接导入函数而非通过别名，可以更好地反映原始函数的更改
from app.services.auth_utils import (
    get_password_hash,
    verify_password as _verify_password,
    create_access_token as _create_access_token,
    decode_access_token as _decode_access_token,
    authenticate_user as _authenticate_user
)
from app.services.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# 配置日志记录器
logger = logging.getLogger(__name__)


# 为了保持向后兼容性，保留原始的函数名和接口
# 但直接使用从auth_utils导入的函数

def hash_password(password: str) -> str:
    """生成密码的哈希值
    直接使用 auth_utils 中的 get_password_hash 函数，包含密码长度验证和安全处理
    """
    logger.debug("调用密码哈希函数")
    return get_password_hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希密码是否匹配
    直接使用 auth_utils 中的 verify_password 函数
    """
    return _verify_password(password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌
    直接使用 auth_utils 中的 create_access_token 函数
    """
    logger.debug("创建访问令牌")
    return _create_access_token(data, expires_delta)


def decode_access_token(token: str) -> Optional[str]:
    """解码访问令牌并返回用户名
    基于 auth_utils 中的 decode_access_token 函数，但只返回用户名
    """
    payload = _decode_access_token(token)
    if payload:
        return payload.get("sub")
    return None


def authenticate_user(db, username: str, password: str):
    """验证用户身份
    直接使用 auth_utils 中的 authenticate_user 函数
    """
    return _authenticate_user(db, username, password)

# 导出配置常量，以便其他模块可以使用
__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "authenticate_user",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES"
]
