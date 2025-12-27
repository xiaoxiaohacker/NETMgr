from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.services.db import get_db
from app.services.snmp_config import get_snmp_config, update_snmp_config

# 配置日志记录器
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/config")
def get_snmp_configuration():
    """
    获取SNMP配置信息
    
    Returns:
        SNMP配置信息
    """
    try:
        config = get_snmp_config()
        return {"success": True, "data": config}
    except Exception as e:
        logger.error(f"获取SNMP配置失败: {str(e)}")
        return {"success": False, "message": f"获取SNMP配置失败: {str(e)}"}

@router.put("/config")
def update_snmp_configuration(config: Dict[str, Any]):
    """
    更新SNMP配置信息
    
    Args:
        config: 新的SNMP配置
        
    Returns:
        更新结果
    """
    try:
        success = update_snmp_config(config)
        if success:
            return {"success": True, "message": "SNMP配置更新成功"}
        else:
            return {"success": False, "message": "SNMP配置更新失败"}
    except Exception as e:
        logger.error(f"更新SNMP配置失败: {str(e)}")
        return {"success": False, "message": f"更新SNMP配置失败: {str(e)}"}