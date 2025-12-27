import logging
from sqlalchemy.orm import Session
from app.services.models import SystemLog
from app.services.db import get_db
from typing import Optional

# 配置日志记录器
logger = logging.getLogger(__name__)

def create_system_log(
    db: Session,
    level: str,
    module: str,
    message: str,
    device_id: Optional[int] = None,
    user_id: Optional[int] = None
):
    """
    创建系统日志记录
    
    参数:
        db: 数据库会话
        level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
        module: 模块名称
        message: 日志消息
        device_id: 关联的设备ID（可选）
        user_id: 关联的用户ID（可选）
    """
    try:
        # 创建日志记录
        log_entry = SystemLog(
            level=level.upper(),
            module=module,
            message=message,
            device_id=device_id,
            user_id=user_id
        )
        
        # 添加到数据库
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        # 同时记录到文件日志
        log_message = f"[{module}] {message}"
        if level.upper() == "ERROR":
            logger.error(log_message)
        elif level.upper() == "WARNING":
            logger.warning(log_message)
        elif level.upper() == "DEBUG":
            logger.debug(log_message)
        else:
            logger.info(log_message)
            
        return log_entry
    except Exception as e:
        db.rollback()
        logger.error(f"创建系统日志记录失败: {str(e)}")
        raise