import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.services.db import get_db
from app.services.models import User as UserModel
from app.services.schemas import UserResponse, UserCreate
from app.api.v1.auth import oauth2_scheme, decode_access_token
from app.services.auth import hash_password
from app.services.system_log import create_system_log

# 配置日志记录器
logger = logging.getLogger(__name__)

# 定义获取当前用户的依赖函数
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前认证用户"""
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

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        logger.warning(f"找不到用户: {username}")
        create_system_log(
            db=db,
            level="WARNING",
            module="USER",
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
        module="USER",
        message=f"用户信息查询成功: {username}",
        user_id=user.id
    )
    return user

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取用户列表
    
    参数:
        db: 数据库会话
        current_user: 当前认证用户
    
    返回:
        用户列表
    
    异常:
        403: 权限不足
        500: 服务器内部错误
    """
    try:
        # 检查当前用户权限（仅管理员可访问）
        if current_user.username != "admin":
            logger.warning(f"权限不足，用户 {current_user.username} 无法访问用户列表")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"用户 {current_user.username} 尝试访问用户列表，权限不足",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，仅管理员可访问用户列表"
            )

        users = db.query(UserModel).all()
        logger.info(f"用户 {current_user.username} 查询了用户列表，共 {len(users)} 个用户")
        create_system_log(
            db=db,
            level="INFO",
            module="USER",
            message=f"用户 {current_user.username} 查询了用户列表，共 {len(users)} 个用户",
            user_id=current_user.id
        )
        return users
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取用户列表过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="USER",
            message=f"获取用户列表过程中发生错误: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败，请稍后重试"
        )


@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """创建新用户
    
    参数:
        user: 用户创建数据
        db: 数据库会话
        current_user: 当前认证用户
    
    返回:
        创建的用户信息
    
    异常:
        400: 用户名或邮箱已存在
        403: 权限不足
        500: 服务器内部错误
    """
    try:
        # 检查当前用户权限（仅管理员可创建用户）
        if current_user.username != "admin":
            logger.warning(f"权限不足，用户 {current_user.username} 无法创建新用户")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"用户 {current_user.username} 尝试创建新用户，权限不足",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，仅管理员可创建新用户"
            )

        # 检查用户名是否已存在
        if db.query(UserModel).filter(UserModel.username == user.username).first():
            logger.warning(f"创建用户失败: 用户名已存在 - {user.username}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"创建用户失败: 用户名已存在 - {user.username}",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        if db.query(UserModel).filter(UserModel.email == user.email).first():
            logger.warning(f"创建用户失败: 邮箱已存在 - {user.email}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"创建用户失败: 邮箱已存在 - {user.email}",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

        # 创建新用户
        hashed_password = hash_password(user.password)
        new_user = UserModel(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"用户 {user.username} 创建成功")
        create_system_log(
            db=db,
            level="INFO",
            module="USER",
            message=f"用户 {user.username} 创建成功",
            user_id=new_user.id
        )
        
        return new_user
        
    except Exception as e:
        logger.error(f"创建用户过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="USER",
            message=f"创建用户过程中发生错误: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败，请稍后重试"
        )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """更新用户信息
    
    参数:
        user_id: 要更新的用户ID
        user_update: 用户更新数据
        db: 数据库会话
        current_user: 当前认证用户
    
    返回:
        更新后的用户信息
    
    异常:
        403: 权限不足
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        # 检查当前用户权限（仅管理员可更新用户，或用户更新自己的信息）
        if current_user.username != "admin" and current_user.id != user_id:
            logger.warning(f"权限不足，用户 {current_user.username} 无法更新用户 {user_id}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"用户 {current_user.username} 尝试更新用户 {user_id}，权限不足",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，仅管理员或用户本人可更新用户信息"
            )

        # 获取要更新的用户
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"尝试更新不存在的用户: {user_id}",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 如果不是管理员，检查用户名是否试图更改
        if current_user.username != "admin" and user.username != user_update.username:
            logger.warning(f"普通用户不能更改用户名: {current_user.username}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"用户 {current_user.username} 尝试更改用户名，权限不足",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，普通用户不能更改用户名"
            )

        # 检查用户名是否已被其他用户使用
        existing_user = db.query(UserModel).filter(
            UserModel.username == user_update.username,
            UserModel.id != user_id
        ).first()
        if existing_user:
            logger.warning(f"更新用户失败: 用户名已存在 - {user_update.username}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"更新用户 {user_id} 失败: 用户名已存在 - {user_update.username}",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已被其他用户使用
        existing_email = db.query(UserModel).filter(
            UserModel.email == user_update.email,
            UserModel.id != user_id
        ).first()
        if existing_email:
            logger.warning(f"更新用户失败: 邮箱已被使用 - {user_update.email}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"更新用户 {user_id} 失败: 邮箱已被使用 - {user_update.email}",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )

        # 更新用户信息
        user.username = user_update.username
        user.email = user_update.email
        if user_update.password:  # 如果提供了新密码，则更新
            user.hashed_password = hash_password(user_update.password)

        db.commit()
        db.refresh(user)

        logger.info(f"用户 {current_user.username} 更新了用户 {user_id} 的信息")
        create_system_log(
            db=db,
            level="INFO",
            module="USER",
            message=f"用户 {current_user.username} 更新了用户 {user_id} 的信息",
            user_id=current_user.id
        )
        return user
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"更新用户过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="USER",
            message=f"更新用户过程中发生错误: {str(e)}"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败，请稍后重试"
        )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """删除用户
    
    参数:
        user_id: 要删除的用户ID
        db: 数据库会话
        current_user: 当前认证用户
    
    返回:
        删除成功消息
    
    异常:
        403: 权限不足
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        # 检查当前用户权限（仅管理员可删除用户）
        if current_user.username != "admin":
            logger.warning(f"权限不足，用户 {current_user.username} 无法删除用户 {user_id}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"用户 {current_user.username} 尝试删除用户 {user_id}，权限不足",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，仅管理员可删除用户"
            )

        # 获取要删除的用户
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"尝试删除不存在的用户: {user_id}",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 不能删除自己
        if current_user.id == user_id:
            logger.warning(f"用户不能删除自己: {current_user.username}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"用户 {current_user.username} 尝试删除自己",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )

        # 删除用户前先处理相关系统日志记录，避免外键约束问题
        # 将相关系统日志中的user_id设置为NULL（如果允许）
        from app.services.models import SystemLog
        db.query(SystemLog).filter(SystemLog.user_id == user_id).update({SystemLog.user_id: None})
        
        # 如果有其他引用用户的表，也需要类似处理
        # 例如，如果有任务表引用用户，也需要处理
        # from app.services.models import Task
        # db.query(Task).filter(Task.creator_id == user_id).update({Task.creator_id: None})

        # 删除用户
        db.delete(user)
        db.commit()

        logger.info(f"用户 {current_user.username} 删除了用户: {user.username}")
        # 注意：这里不能再创建系统日志，因为用户已经删除，而日志记录会引用用户ID
        # 可以记录到文件日志
        logger.info(f"用户 {current_user.username} 删除了用户: {user.username}")
        return {"message": "用户删除成功"}
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"删除用户过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="USER",
            message=f"删除用户过程中发生错误: {str(e)}"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败，请稍后重试"
        )


@router.patch("/{user_id}/status")
def toggle_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """切换用户状态
    
    参数:
        user_id: 用户ID
        is_active: 激活状态
        db: 数据库会话
        current_user: 当前认证用户
    
    返回:
        更新后的用户状态
    
    异常:
        403: 权限不足
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        # 检查当前用户权限（仅管理员可切换用户状态）
        if current_user.username != "admin":
            logger.warning(f"权限不足，用户 {current_user.username} 无法切换用户 {user_id} 的状态")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"用户 {current_user.username} 尝试切换用户 {user_id} 的状态，权限不足",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，仅管理员可切换用户状态"
            )

        # 获取用户
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            create_system_log(
                db=db,
                level="WARNING",
                module="USER",
                message=f"尝试切换不存在的用户 {user_id} 的状态",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 更新用户状态
        user.is_active = is_active
        db.commit()
        db.refresh(user)

        status_text = "启用" if is_active else "禁用"
        logger.info(f"用户 {current_user.username} {status_text}了用户: {user.username}")
        create_system_log(
            db=db,
            level="INFO",
            module="USER",
            message=f"用户 {current_user.username} {status_text}了用户: {user.username}",
            user_id=current_user.id
        )
        return {"id": user.id, "is_active": user.is_active}
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"切换用户状态过程中发生错误: {str(e)}")
        create_system_log(
            db=db,
            level="ERROR",
            module="USER",
            message=f"切换用户状态过程中发生错误: {str(e)}"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换用户状态失败，请稍后重试"
        )