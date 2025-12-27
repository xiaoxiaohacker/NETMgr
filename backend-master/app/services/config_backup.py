import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

# 配置日志记录器
logger = logging.getLogger(__name__)

"""
配置备份模块
此模块已废弃，所有功能已移至config_backup_service.py
保留此文件以确保向后兼容性
"""

# 保留导入以确保向后兼容性
from app.services.config_backup_service import (
    create_config_backup,
    get_config_backup,
    get_device_config_backups,
    delete_config_backup,
    get_latest_config_backup,
    CONFIG_BACKUP_DIR
)

__all__ = [
    "create_config_backup",
    "get_config_backup",
    "get_device_config_backups",
    "delete_config_backup",
    "get_latest_config_backup",
    "CONFIG_BACKUP_DIR"
]