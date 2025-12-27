import logging
import os
import hashlib
from sqlalchemy.orm import Session
from datetime import datetime
from app.services.models import Config
from app.services.schemas import ConfigCreate

# 配置备份文件存储路径
CONFIG_BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config_backups')

# 确保备份目录存在
os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)

# 配置日志记录器
logger = logging.getLogger(__name__)

def create_config_backup(db: Session, config_data: ConfigCreate) -> Config:
    """创建配置备份
    
    参数:
        db: 数据库会话
        config_data: 配置备份数据
    
    返回:
        创建的配置备份对象
    """
    try:
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_backup_{config_data.device_id}_{timestamp}.cfg"
        filepath = os.path.join(CONFIG_BACKUP_DIR, filename)
        
        # 将配置内容写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(config_data.config)
        
        # 计算文件大小和哈希值
        file_size = os.path.getsize(filepath)
        with open(filepath, 'rb') as f:
            content = f.read()
            file_hash = hashlib.md5(content).hexdigest()
        
        # 创建数据库记录
        db_config = Config(
            device_id=config_data.device_id,
            filename=filename,
            config=config_data.config,
            taken_by=config_data.taken_by,
            description=config_data.description,
            file_size=file_size,
            hash=file_hash
        )
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        logger.info(f"配置备份创建成功，ID: {db_config.id}, 文件: {filename}")
        return db_config
    except Exception as e:
        db.rollback()
        logger.error(f"创建配置备份失败: {str(e)}")
        raise

def get_config_backup(db: Session, backup_id: int) -> Config:
    """获取指定的配置备份
    
    参数:
        db: 数据库会话
        backup_id: 配置备份ID
    
    返回:
        配置备份对象
    """
    try:
        backup = db.query(Config).filter(Config.id == backup_id).first()
        logger.debug(f"获取配置备份，ID: {backup_id}")
        return backup
    except Exception as e:
        logger.error(f"获取配置备份失败，ID: {backup_id}, 错误: {str(e)}")
        raise

def get_device_config_backups(db: Session, device_id: int, limit: int = 100) -> list:
    """获取设备的所有配置备份
    
    参数:
        db: 数据库会话
        device_id: 设备ID
        limit: 返回的最大记录数
    
    返回:
        配置备份列表
    """
    try:
        backups = db.query(Config).filter(Config.device_id == device_id).order_by(
            Config.created_at.desc()).limit(limit).all()
        logger.debug(f"获取设备配置备份列表，设备ID: {device_id}, 数量: {len(backups)}")
        return backups
    except Exception as e:
        logger.error(f"获取设备配置备份列表失败，设备ID: {device_id}, 错误: {str(e)}")
        raise

def delete_config_backup(db: Session, backup_id: int) -> bool:
    """删除指定的配置备份
    
    参数:
        db: 数据库会话
        backup_id: 配置备份ID
    
    返回:
        删除是否成功
    """
    try:
        backup = db.query(Config).filter(Config.id == backup_id).first()
        if not backup:
            logger.warning(f"配置备份未找到，ID: {backup_id}")
            return False
        
        # 删除备份文件
        filepath = os.path.join(CONFIG_BACKUP_DIR, backup.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"配置备份文件已删除，路径: {filepath}")
        
        # 删除数据库记录
        db.delete(backup)
        db.commit()
        
        logger.info(f"配置备份删除成功，ID: {backup_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"删除配置备份失败，ID: {backup_id}, 错误: {str(e)}")
        raise

def get_latest_config_backup(db: Session, device_id: int) -> Config:
    """获取设备的最新配置备份
    
    参数:
        db: 数据库会话
        device_id: 设备ID
    
    返回:
        最新的配置备份对象
    """
    try:
        backup = db.query(Config).filter(Config.device_id == device_id).order_by(
            Config.created_at.desc()).first()
        logger.debug(f"获取设备最新配置备份，设备ID: {device_id}")
        return backup
    except Exception as e:
        logger.error(f"获取设备最新配置备份失败，设备ID: {device_id}, 错误: {str(e)}")
        raise