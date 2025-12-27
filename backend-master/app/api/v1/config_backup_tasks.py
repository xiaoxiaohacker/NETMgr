from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
import os
from app.services.db import get_db
from app.services.models import Config, Task
from app.api.v1.auth import oauth2_scheme, decode_access_token
from app.services.config_backup_service import get_device_config_backups, create_config_backup, delete_config_backup, get_config_backup
from app.services.schemas import ConfigCreate, ConfigOut


router = APIRouter(tags=["配置备份"])

# 配置备份文件存储路径
CONFIG_BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config_backups')

@router.get("/backup-tasks/all")
def get_all_backup_tasks(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """
    获取所有配置备份列表（支持分页）
    """
    # 验证令牌
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    # 计算分页偏移量
    offset = (page - 1) * size
    
    # 查询总数
    total = db.query(Config).count()
    
    # 查询配置备份列表
    backups = db.query(Config).offset(offset).limit(size).all()
    
    # 构建响应数据
    backup_list = []
    for backup in backups:
        backup_list.append({
            "id": backup.id,
            "device_id": backup.device_id,
            "filename": backup.filename,
            "taken_by": backup.taken_by,
            "description": backup.description,
            "file_size": backup.file_size,
            "hash": backup.hash,
            "created_at": backup.created_at.isoformat() if backup.created_at else None
        })
    
    return {
        "total": total,
        "items": backup_list,
        "page": page,
        "size": size
    }


@router.delete("/{backup_id}")
def delete_backup_task(
    backup_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    删除指定的配置备份
    """
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    try:
        result = delete_config_backup(db, backup_id)
        if not result:
            raise HTTPException(status_code=404, detail="备份未找到")
        return {"message": "备份删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")


@router.get("/{backup_id}/download")
def download_backup_task(
    backup_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    下载指定的配置备份文件
    """
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    try:
        # 获取备份信息
        backup = get_config_backup(db, backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="备份未找到")
        
        # 构建文件路径
        filepath = os.path.join(CONFIG_BACKUP_DIR, backup.filename)
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 返回文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载备份失败: {str(e)}")


@router.get("/statistics")
def get_backup_statistics(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    获取配置备份统计信息
    """
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    try:
        # 总备份数
        total_backups = db.query(Config).count()
        
        # 按设备分组的备份数
        device_backup_counts = db.query(Config.device_id, func.count(Config.id)).group_by(Config.device_id).all()
        
        # 最近一周的备份数
        from datetime import datetime, timedelta
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_backups = db.query(Config).filter(Config.created_at >= one_week_ago).count()
        
        return {
            "total_backups": total_backups,
            "device_backup_counts": dict(device_backup_counts),
            "recent_backups": recent_backups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/")
def create_backup_task(
    config_data: ConfigCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    创建配置备份任务
    """
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    try:
        # 设置备份创建者
        config_data.taken_by = username
        if not config_data.description:
            config_data.description = f"手动创建的配置备份"
            
        backup = create_config_backup(db, config_data)
        return backup
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")


@router.post("/batch-execute")
def execute_batch_backup(
    device_ids: List[int],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    批量执行配置备份任务
    """
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    try:
        # 这里应该实现真正的批量备份逻辑
        # 目前只是返回一个模拟的成功响应
        return {
            "message": f"已开始为 {len(device_ids)} 个设备执行备份任务",
            "device_count": len(device_ids),
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行批量备份失败: {str(e)}")