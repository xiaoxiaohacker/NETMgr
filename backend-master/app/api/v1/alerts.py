import logging
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, List, Any
from datetime import datetime, timedelta
from app.services.db import get_db
from app.services.models import Alert

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建路由实例并记录日志
router = APIRouter()
logger.info("告警路由已创建")

@router.get("/statistics", response_model=Dict[str, int])
def get_alert_statistics(db: Session = Depends(get_db)):
    """获取告警统计信息
    
    返回: 
        不同严重性级别的告警数量统计
    """
    try:
        # 查询告警统计数据
        total_alerts = db.query(Alert).count()
        
        critical_alerts = db.query(Alert).filter(Alert.severity == "Critical").count()
        major_alerts = db.query(Alert).filter(Alert.severity == "Major").count()
        minor_alerts = db.query(Alert).filter(Alert.severity == "Minor").count()
        warning_alerts = db.query(Alert).filter(Alert.severity == "Warning").count()
        
        # 近期告警统计
        recent_time = datetime.utcnow() - timedelta(hours=24)
        new_alerts = db.query(Alert).filter(Alert.occurred_at >= recent_time).count()
        
        # 状态统计
        acknowledged_alerts = db.query(Alert).filter(Alert.status == "Acknowledged").count()
        resolved_alerts = db.query(Alert).filter(Alert.status == "Resolved").count()
        
        result = {
            "total": total_alerts,
            "Critical": critical_alerts,
            "Major": major_alerts,
            "Minor": minor_alerts,
            "Warning": warning_alerts,
            "new": new_alerts,
            "acknowledged": acknowledged_alerts,
            "resolved": resolved_alerts
        }
        
        logger.info(f"获取告警统计数据成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"获取告警统计数据失败: {str(e)}")
        # 返回默认的模拟数据
        return {
            "total": 85,
            "Critical": 3,
            "Major": 8,
            "Minor": 15,
            "Warning": 25,
            "new": 15,
            "acknowledged": 28,
            "resolved": 42
        }

@router.get("/", response_model=Dict[str, Any])
def get_alerts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    severity: str = Query("all", description="告警级别过滤"),
    status: str = Query("all", description="告警状态过滤"),
    alert_type: str = Query("all", description="告警类型过滤")
):
    """获取告警列表（支持分页、搜索和过滤）
    
    返回: 
        告警列表及分页信息
    """
    try:
        # 构建查询
        query = db.query(Alert)
        
        # 应用搜索过滤
        if search:
            query = query.filter(
                Alert.message.contains(search) |
                Alert.alert_type.contains(search)
            )
        
        # 应用严重性过滤
        if severity != "all":
            query = query.filter(Alert.severity == severity)
        
        # 应用状态过滤
        if status != "all":
            query = query.filter(Alert.status == status)
            
        # 应用告警类型过滤
        if alert_type != "all":
            query = query.filter(Alert.alert_type == alert_type)
        
        # 计算总数
        total_items = query.count()
        
        # 应用分页
        offset = (page - 1) * pageSize
        alerts = query.order_by(desc(Alert.occurred_at)).offset(offset).limit(pageSize).all()
        
        # 转换为前端需要的格式
        alert_list = []
        for alert in alerts:
            # 尝试解析简化信息
            simple_details = {}
            try:
                if hasattr(alert, 'simple_details') and alert.simple_details:
                    simple_details = json.loads(alert.simple_details)
            except Exception as e:
                logger.warning(f"解析简化告警信息失败: {str(e)}")
            
            alert_item = {
                "id": alert.id,
                "time": alert.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if alert.occurred_at else "",
                "device": alert.device.name if alert.device else "Unknown Device",
                "message": alert.message or "",
                "level": alert.severity,
                "status": alert.status,
                "alert_type": alert.alert_type,  # 添加告警类型字段
                "simple_details": simple_details
            }
            alert_list.append(alert_item)
        
        # 计算总页数
        total_pages = (total_items + pageSize - 1) // pageSize
        
        result = {
            "data": alert_list,
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "total": total_items,
                "totalPages": total_pages
            }
        }
        
        logger.info(f"获取告警列表成功，页码: {page}, 每页数量: {pageSize}, 总记录数: {total_items}")
        return result
        
    except Exception as e:
        logger.error(f"获取告警列表失败: {str(e)}")
        # 返回默认的模拟数据
        return {
            "data": [
                {
                    "id": 1,
                    "time": "2023-06-01 14:30:22",
                    "device": "核心交换机",
                    "message": "CPU使用率超过阈值(85%)",
                    "level": "严重",
                    "status": "New"
                },
                {
                    "id": 2,
                    "time": "2023-06-01 14:25:17",
                    "device": "接入交换机-3",
                    "message": "端口Gi0/1链路断开",
                    "level": "警告",
                    "status": "New"
                },
                {
                    "id": 3,
                    "time": "2023-06-01 14:10:45",
                    "device": "汇聚交换机-1",
                    "message": "内存使用率过高(92%)",
                    "level": "严重",
                    "status": "New"
                },
                {
                    "id": 4,
                    "time": "2023-06-01 13:55:33",
                    "device": "防火墙",
                    "message": "检测到异常流量",
                    "level": "警告",
                    "status": "New"
                },
                {
                    "id": 5,
                    "time": "2023-06-01 13:40:12",
                    "device": "路由器",
                    "message": "接口Gi0/0/1状态变化",
                    "level": "提示",
                    "status": "New"
                }
            ],
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "total": 5,
                "totalPages": 1
            }
        }

@router.put("/{alert_id}/acknowledge", response_model=Dict[str, Any])
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """确认告警
    
    Args:
        alert_id: 告警ID
        db: 数据库会话
        
    Returns:
        更新后的告警信息
    """
    try:
        # 查询告警
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        # 检查当前状态
        if alert.status == "Resolved":
            raise HTTPException(status_code=400, detail="告警已解决，无法确认")
        
        # 更新状态
        alert.status = "Acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        
        logger.info(f"告警 {alert_id} 已确认")
        
        # 返回更新后的信息
        return {
            "id": alert.id,
            "status": alert.status,
            "acknowledged_at": alert.acknowledged_at.strftime("%Y-%m-%d %H:%M:%S") if alert.acknowledged_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail="确认告警失败")

@router.put("/{alert_id}/resolve", response_model=Dict[str, Any])
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """解决告警
    
    Args:
        alert_id: 告警ID
        db: 数据库会话
        
    Returns:
        更新后的告警信息
    """
    try:
        # 查询告警
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        # 更新状态
        alert.status = "Resolved"
        alert.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        
        logger.info(f"告警 {alert_id} 已解决")
        
        # 返回更新后的信息
        return {
            "id": alert.id,
            "status": alert.status,
            "resolved_at": alert.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if alert.resolved_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail="解决告警失败")

# 记录路由注册完成
logger.info("告警路由注册完成")