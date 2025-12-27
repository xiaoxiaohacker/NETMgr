import logging
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Dict, Any
from datetime import datetime
import csv
import io

from app.services.db import get_db
from app.services.models import SystemLog, Device, User
from app.api.v1.auth import oauth2_scheme, decode_access_token

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
def get_system_logs(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: str = Query("", description="搜索关键词"),
    level: str = Query("all", description="日志级别过滤"),
    device_id: int = Query(None, description="设备ID过滤"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期")
):
    """获取系统日志列表（支持分页、搜索和过滤）
    
    返回: 
        系统日志列表及分页信息
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return {"error": "无效的访问令牌"}

        # 构建查询条件
        query = db.query(SystemLog)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    SystemLog.message.contains(keyword),
                    SystemLog.module.contains(keyword)
                )
            )
        
        # 日志级别过滤
        if level != "all":
            query = query.filter(SystemLog.level == level.upper())
        
        # 设备ID过滤
        if device_id:
            query = query.filter(SystemLog.device_id == device_id)
        
        # 时间范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(SystemLog.timestamp >= start_datetime)
            except ValueError:
                pass  # 忽略无效的日期格式
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(SystemLog.timestamp <= end_datetime)
            except ValueError:
                pass  # 忽略无效的日期格式
        
        # 获取总记录数
        total = query.count()
        
        # 计算偏移量
        offset = (page - 1) * pageSize
        
        # 使用join确保正确加载关联的用户和设备信息
        logs = query.options(
            joinedload(SystemLog.user),
            joinedload(SystemLog.device)
        ).order_by(SystemLog.timestamp.desc()).offset(offset).limit(pageSize).all()
        
        # 格式化返回数据
        log_list = []
        for log in logs:
            log_item = {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "level": log.level,
                "module": log.module,
                "message": log.message,
                "device_id": log.device_id,
                "user_id": log.user_id
            }
            
            # 如果有关联设备，添加设备信息
            if log.device:
                log_item["device"] = {
                    "id": log.device.id,
                    "name": log.device.name,
                    "management_ip": log.device.management_ip
                }
            
            # 如果有关联用户，添加用户信息
            if log.user:
                log_item["user"] = {
                    "id": log.user.id,
                    "username": log.user.username
                }
                
            log_list.append(log_item)
        
        result = {
            "data": log_list,
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "total": total,
                "totalPages": (total + pageSize - 1) // pageSize
            }
        }
        
        logger.info(f"用户 {username} 获取系统日志列表，共 {total} 条记录")
        return result
        
    except Exception as e:
        logger.error(f"获取系统日志列表失败: {str(e)}")
        return {
            "error": "获取系统日志列表失败",
            "data": [],
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "total": 0,
                "totalPages": 0
            }
        }


@router.get("/export")
def export_system_logs(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(1000, ge=1, le=10000, description="每页数量"),
    keyword: str = Query("", description="搜索关键词"),
    level: str = Query("all", description="日志级别过滤"),
    device_id: int = Query(None, description="设备ID过滤"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期")
):
    """导出系统日志为CSV格式
    
    返回: 
        CSV格式的系统日志数据
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return {"error": "无效的访问令牌"}

        # 构建查询条件（预加载关联信息）
        query = db.query(SystemLog).options(
            db.joinedload(SystemLog.user),
            db.joinedload(SystemLog.device)
        )
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    SystemLog.message.contains(keyword),
                    SystemLog.module.contains(keyword)
                )
            )
        
        # 日志级别过滤
        if level != "all":
            query = query.filter(SystemLog.level == level.upper())
        
        # 设备ID过滤
        if device_id:
            query = query.filter(SystemLog.device_id == device_id)
        
        # 时间范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(SystemLog.timestamp >= start_datetime)
            except ValueError:
                pass  # 忽略无效的日期格式
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(SystemLog.timestamp <= end_datetime)
            except ValueError:
                pass  # 忽略无效的日期格式
        
        # 分页查询
        offset = (page - 1) * pageSize
        logs = query.order_by(SystemLog.timestamp.desc()).offset(offset).limit(pageSize).all()
        
        # 创建CSV数据
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['时间', '级别', '用户', '设备', '模块', '内容'])
        
        # 写入数据
        for log in logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
                log.level,
                log.user.username if log.user else '',
                log.device.name if log.device else '',
                log.module,
                log.message
            ])
        
        # 准备响应
        csv_data = output.getvalue()
        output.close()
        
        # 返回CSV文件
        headers = {
            'Content-Disposition': 'attachment; filename="system_logs.csv"',
            'Content-Type': 'text/csv; charset=utf-8'
        }
        
        logger.info(f"用户 {username} 导出系统日志，共 {len(logs)} 条记录")
        return Response(content=csv_data, headers=headers)
        
    except Exception as e:
        logger.error(f"导出系统日志失败: {str(e)}")
        raise

@router.get("/levels", response_model=List[str])
def get_log_levels(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取所有日志级别
    
    返回:
        日志级别列表
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return []
        
        # 查询所有唯一的日志级别
        levels = db.query(SystemLog.level).distinct().all()
        level_list = [level[0] for level in levels]
        
        logger.info(f"用户 {username} 获取日志级别列表")
        return level_list
        
    except Exception as e:
        logger.error(f"获取日志级别列表失败: {str(e)}")
        return []

@router.get("/modules", response_model=List[str])
def get_log_modules(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取所有日志模块
    
    返回:
        日志模块列表
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return []
        
        # 查询所有唯一的日志模块
        modules = db.query(SystemLog.module).distinct().all()
        module_list = [module[0] for module in modules]
        
        logger.info(f"用户 {username} 获取日志模块列表")
        return module_list
        
    except Exception as e:
        logger.error(f"获取日志模块列表失败: {str(e)}")
        return []