import logging
from datetime import datetime, timedelta
from typing import Optional
import logging
import jose
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.services.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.services.models import User

# 配置日志记录器
logger = logging.getLogger(__name__)

# 尝试导入bcrypt库
BCRYPT_AVAILABLE = False
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    logger.info("成功导入bcrypt库")
except ImportError:
    logger.warning("无法导入bcrypt库，将使用替代方案")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    完全绕过passlib，直接使用bcrypt库进行密码验证
    """
    try:
        # 确保bcrypt库可用
        if not BCRYPT_AVAILABLE:
            logger.error("bcrypt库不可用，无法进行密码验证")
            return False
        
        # 确保密码不超过72字节（bcrypt限制）
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            logger.warning(f"密码字节长度超过bcrypt限制: {len(password_bytes)}字节，自动截断到72字节")
            password_bytes = password_bytes[:72]
        
        # 确保哈希密码是字节类型
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
        
        # 直接使用bcrypt库验证密码
        try:
            result = bcrypt.checkpw(password_bytes, hashed_bytes)
            logger.debug(f"密码验证结果: {result}")
            return result
        except Exception as bcrypt_e:
            logger.error(f"bcrypt密码验证失败: {type(bcrypt_e).__name__}: {str(bcrypt_e)}")
            
            # 处理可能的密码长度错误
            if "password cannot be longer than 72 bytes" in str(bcrypt_e).lower():
                logger.warning("bcrypt报告密码长度错误，即使我们已经尝试截断")
                # 再次尝试更严格的截断（72字节）
                try:
                    password_bytes = password_bytes[:72]
                    result = bcrypt.checkpw(password_bytes, hashed_bytes)
                    logger.warning("使用更严格的截断后密码验证成功")
                    return result
                except:
                    logger.error("严格截断后密码验证仍然失败")
            return False
    except Exception as e:
        logger.error(f"密码验证过程中发生未预期的错误: {type(e).__name__}: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """
    生成密码的哈希值
    直接使用bcrypt库进行密码哈希
    """
    try:
        if not BCRYPT_AVAILABLE:
            logger.error("bcrypt库不可用，无法生成密码哈希")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码加密功能不可用"
            )
        
        # 详细记录密码长度信息以调试问题
        logger.debug(f"开始处理密码 - 字符长度: {len(password)}")
        
        # 检查密码长度是否符合最小要求
        if len(password) < 10:
            logger.warning(f"密码太短: {len(password)}字符")
            raise ValueError("密码长度不能少于10个字符")
            
        # 检查密码的字节长度
        password_bytes = password.encode('utf-8')
        logger.debug(f"密码字节长度: {len(password_bytes)}字节")
        
        # 对于超长密码，我们有两个选择：
        # 1. 拒绝超长密码（更安全，明确告诉用户）
        # 2. 自动截断（更方便用户，但可能导致安全隐患）
        # 选择：拒绝超长密码并明确提示
        if len(password_bytes) > 72:
            logger.warning(f"密码字节长度超过限制: {len(password_bytes)}字节")
            raise ValueError(f"密码字节长度({len(password_bytes)})超过bcrypt限制的72字节")
        
        # 生成盐值
        salt = bcrypt.gensalt(rounds=12)
        
        # 生成哈希密码
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        
        # 转换为字符串返回
        hashed_password = hashed_bytes.decode('utf-8')
        logger.debug("密码哈希生成成功")
        return hashed_password
    except HTTPException:
        # 已经是HTTPException，直接重新抛出
        raise
    except Exception as e:
        logger.error(f"密码哈希生成过程中发生错误: {type(e).__name__}: {str(e)}")
        # 提供更具体的错误信息给前端
        error_msg = "密码加密过程失败"
        if "密码长度不能少于10个字符" in str(e):
            error_msg = "密码长度不能少于10个字符，请设置更长的密码"
        elif "超过bcrypt限制的72字节" in str(e):
            error_msg = "密码不能超过72个字符，请缩短密码后重试"
        # 处理bcrypt可能抛出的原始异常
        elif "cannot be longer than 72 bytes" in str(e).lower():
            error_msg = "密码不能超过72个字符，请缩短密码后重试"
        logger.debug(f"抛出HTTP异常: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户身份
    """
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"用户不存在: {username}")
            return None
        
        if hasattr(user, 'is_active') and not user.is_active:
            logger.warning(f"用户已禁用: {username}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"用户密码验证失败: {username}")
            return None
        
        # 注意：User模型中没有last_login字段，所以不更新最后登录时间
        
        logger.info(f"用户认证成功: {username}")
        return user
    except Exception as e:
        logger.error(f"用户认证过程中发生错误: {str(e)}")
        db.rollback()
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"创建访问令牌过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌创建失败"
        )

def decode_access_token(token: str) -> Optional[dict]:
    """
    解码访问令牌
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("令牌中未找到用户名")
            return None
        return payload
    except JWTError as e:
        logger.error(f"令牌解码失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"令牌处理过程中发生未知错误: {str(e)}")
        return None

# 注意：不再使用别名，所有调用应直接使用get_password_hash
# 如需兼容旧代码，请在各自模块中处理
