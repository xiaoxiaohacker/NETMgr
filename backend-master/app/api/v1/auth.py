import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.services.db import get_db as _get_db
from app.services.models import User
from app.services.schemas import UserCreate, Token, UserResponse
from app.services.auth import hash_password, verify_password, create_access_token, decode_access_token, authenticate_user
from app.services.system_log import create_system_log

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 重用服务层的数据库会话依赖项
get_db = _get_db


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册接口
    创建新用户并保存到数据库
    
    参数:
        user: 包含用户名、邮箱和密码的用户创建数据
        db: 数据库会话
    
    返回:
        创建成功的用户信息
    
    异常:
        400: 用户名已存在或邮箱已被使用
        500: 服务器内部错误
    """
    try:
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user.username).first():
            logger.warning(f"注册失败: 用户名已存在 - {user.username}")
            create_system_log(
                db=db,
                level="WARNING",
                module="AUTH",
                message=f"用户注册失败: 用户名已存在 - {user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
            
        # 检查邮箱是否已存在
        if db.query(User).filter(User.email == user.email).first():
            logger.warning(f"注册失败: 邮箱已被使用 - {user.email}")
            create_system_log(
                db=db,
                level="WARNING",
                module="AUTH",
                message=f"用户注册失败: 邮箱已被使用 - {user.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )

        # 创建新用户
        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password),
            is_active=user.is_active,
            role=user.role  # 设置用户角色
        )
        
        # 保存到数据库
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"用户注册成功: {user.username}")
        create_system_log(
            db=db,
            level="INFO",
            module="AUTH",
            message=f"用户注册成功: {user.username}",
            user_id=new_user.id
        )
        return new_user
        
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户注册过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="AUTH",
            message=f"用户注册过程中发生错误: {str(e)}"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户注册失败，请稍后重试"
        )


@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录接口
    验证用户凭据并颁发访问令牌
    
    参数:
        request: HTTP请求对象
        form_data: 包含用户名和密码的表单数据
        db: 数据库会话
    
    返回:
        访问令牌和令牌类型
    
    异常:
        401: 认证失败（用户名或密码错误）
        500: 服务器内部错误
    """
    try:
        # 使用统一的认证函数验证用户
        user = authenticate_user(db, form_data.username, form_data.password)
        
        if not user:
            logger.warning(f"用户登录失败: {form_data.username} (用户名或密码错误)")
            create_system_log(
                db=db,
                level="WARNING",
                module="AUTH",
                message=f"用户登录失败: {form_data.username} (用户名或密码错误)"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # 创建访问令牌
        access_token = create_access_token({"sub": user.username})
        
        logger.info(f"用户登录成功: {user.username}")
        create_system_log(
            db=db,
            level="INFO",
            module="AUTH",
            message=f"用户登录成功: {user.username}",
            user_id=user.id
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户登录过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="AUTH",
            message=f"用户登录过程中发生错误: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误，请稍后重试"
        )


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """用户登出接口
    记录用户登出日志
    
    参数:
        token: OAuth2访问令牌
        db: 数据库会话
    
    返回:
        登出成功消息
    
    异常:
        401: 无效或过期的令牌
        500: 服务器内部错误
    """
    try:
        # 解码访问令牌获取用户名
        username = decode_access_token(token)
        if not username:
            logger.warning("无效或过期的访问令牌")
            create_system_log(
                db=db,
                level="WARNING",
                module="AUTH",
                message="无效或过期的访问令牌"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的Token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 获取用户信息
        user = db.query(User).filter(User.username == username).first()
        
        # 记录登出日志
        logger.info(f"用户登出成功: {username}")
        create_system_log(
            db=db,
            level="INFO",
            module="AUTH",
            message=f"用户登出成功: {username}",
            user_id=user.id if user else None
        )
        return {"message": "登出成功"}
        
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户登出过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="AUTH",
            message=f"用户登出过程中发生错误: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出过程中发生错误，请稍后重试"
        )


@router.get("/me", response_model=UserResponse)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户信息
    根据访问令牌获取用户详细信息
    
    参数:
        token: OAuth2访问令牌
        db: 数据库会话
    
    返回:
        当前用户的详细信息
    
    异常:
        401: 无效或过期的令牌
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        # 解码访问令牌获取用户名
        username = decode_access_token(token)
        if not username:
            logger.warning("无效或过期的访问令牌")
            create_system_log(
                db=db,
                level="WARNING",
                module="AUTH",
                message="无效或过期的访问令牌"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的Token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # 查询用户信息
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"找不到用户: {username}")
            create_system_log(
                db=db,
                level="WARNING",
                module="AUTH",
                message=f"找不到用户: {username}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 检查用户是否已激活
        if hasattr(user, 'is_active') and not user.is_active:
            logger.warning(f"用户已禁用: {username}")
            create_system_log(
                db=db,
                level="WARNING",
                module="AUTH",
                message=f"用户已禁用: {username}",
                user_id=user.id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用",
                headers={"WWW-Authenticate": "Bearer"}
            )

        logger.debug(f"用户信息查询成功: {username}")
        create_system_log(
            db=db,
            level="INFO",
            module="AUTH",
            message=f"用户信息查询成功: {username}",
            user_id=user.id
        )
        return user
        
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取用户信息过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="AUTH",
            message=f"获取用户信息过程中发生错误: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败，请稍后重试"
        )