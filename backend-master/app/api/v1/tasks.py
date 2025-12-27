import logging
import threading
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import uuid
from app.services.db import get_db
from app.services.models import Task, TaskStatus, TaskType, Device
from app.api.v1.auth import oauth2_scheme, decode_access_token
from app.api.v1.users import get_current_user
from app.scheduler import scheduler

# 辅助函数，处理大小写不一致的枚举值
def _normalize_enum_value(value, enum_class):
    """标准化枚举值，处理大小写不一致问题"""
    if isinstance(value, str):
        # 尝试直接匹配枚举值（不区分大小写）
        value_lower = value.lower()
        for enum_member in enum_class:
            if enum_member.value.lower() == value_lower:
                return enum_member
        # 尝试匹配枚举名称（不区分大小写）
        for enum_member in enum_class:
            if enum_member.name.lower() == value_lower:
                return enum_member
        # 如果没有找到匹配项，抛出异常
        raise ValueError(f"无效的枚举值: {value}")
    return value

def _safe_get_status(status):
    """安全获取状态值，处理可能的大小写问题"""
    try:
        # 如果已经是枚举，返回其值
        if hasattr(status, 'value'):
            return status.value
        # 如果是字符串，直接返回
        return str(status)
    except:
        # 如果转换失败，返回原始值
        return str(status)

def _safe_get_task_type(task_type):
    """安全获取任务类型值，处理可能的大小写问题"""
    try:
        # 如果已经是枚举，返回其值
        if hasattr(task_type, 'value'):
            return task_type.value
        # 如果是字符串，直接返回
        return str(task_type)
    except:
        # 如果转换失败，返回原始值
        return str(task_type)

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter(tags=["任务管理"])

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str  # 改为字符串类型以更好地处理前端传来的值
    target_device_ids: List[int]
    scheduled_time: Optional[datetime] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None  # 修改为字符串类型，便于处理
    progress: Optional[int] = None
    result: Optional[str] = None
    logs: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    task_type: str  # 输出也改为字符串类型
    status: str  # 输出也改为字符串类型
    progress: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    scheduled_time: Optional[datetime]
    result: Optional[str]
    logs: Optional[str]
    target_devices: List[Dict[str, Any]]

    class Config:
        from_attributes = True  # 修复Pydantic警告，使用新的配置键名

class TaskListResponse(BaseModel):
    total: int
    data: List[TaskOut]
    page: int
    page_size: int

@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str = Query(""),
    task_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        offset = (page - 1) * page_size
        
        query = db.query(Task)
        
        # 搜索过滤
        if search:
            query = query.filter(Task.name.like(f"%{search}%") | Task.description.like(f"%{search}%"))
        
        # 任务类型过滤
        if task_type:
            # 将字符串转换为枚举值，处理大小写不一致问题
            try:
                task_type_enum = _normalize_enum_value(task_type, TaskType)
                query = query.filter(Task.task_type == task_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的任务类型: {task_type}")
        
        # 状态过滤
        if status:
            # 处理大小写不敏感的状态匹配
            try:
                status_enum = _normalize_enum_value(status, TaskStatus)
                query = query.filter(Task.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的任务状态: {status}")
        
        # 总数用于分页
        total = query.count()
        
        # 排序并获取结果
        tasks = query.order_by(desc(Task.created_at)).offset(offset).limit(page_size).all()
        
        # 转换任务列表为字典格式，处理枚举类型
        tasks_list = []
        for task in tasks:
            # 获取枚举值，直接使用数据库中存储的值
            status_value = _safe_get_status(task.status)
            task_type_value = _safe_get_task_type(task.task_type)
            
            task_dict = {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "status": status_value,
                "task_type": task_type_value,
                "created_at": task.created_at,
                "scheduled_time": task.scheduled_time,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "progress": task.progress,
                "result": task.result,
                "logs": task.logs,
                "target_devices": [
                    {
                        "id": dev.id,
                        "name": dev.name,
                        "management_ip": dev.management_ip
                    } for dev in task.target_devices
                ]
            }
            tasks_list.append(task_dict)
        
        # 返回与前端期望格式匹配的结构
        return {
            "data": tasks_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        # 记录错误详情
        print(f"获取任务列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.post("/", response_model=TaskOut)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    创建新任务
    """
    # 验证令牌
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    # 验证设备是否存在
    devices = db.query(Device).filter(Device.id.in_(task_data.target_device_ids)).all()
    if len(devices) != len(task_data.target_device_ids):
        raise HTTPException(status_code=400, detail="一个或多个设备不存在")
    
    # 验证任务类型是否有效（支持大小写）
    task_type_lower = task_data.task_type.lower()
    try:
        task_type_enum = TaskType(task_type_lower)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的任务类型: {task_data.task_type}")
    
    # 创建任务
    task = Task(
        name=task_data.name,
        description=task_data.description,
        task_type=task_type_enum,  # 使用枚举值
        status=TaskStatus.PENDING,
        progress=0,
        scheduled_time=task_data.scheduled_time
    )
    
    # 关联设备
    task.target_devices = devices
    
    # 保存到数据库
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 记录系统日志
    try:
        from app.services.system_log import create_system_log
        create_system_log(
            db=db,
            level="INFO",
            module="TASK",
            message=f"用户 {username} 创建任务 '{task.name}' (ID: {task.id})，类型: {task.task_type}",
            user_id=None  # 可以进一步扩展以获取用户ID
        )
    except Exception as e:
        logger.error(f"记录系统日志失败: {str(e)}")
    
    # 转换为输出格式
    target_devices = []
    for device in task.target_devices:
        target_devices.append({
            "id": device.id,
            "name": device.name,
            "management_ip": device.management_ip
        })
    
    return TaskOut(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value if hasattr(task.task_type, 'value') else task.task_type,
        status=task.status.value if hasattr(task.status, 'value') else task.status,
        progress=task.progress,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        scheduled_time=task.scheduled_time,
        result=task.result,
        logs=task.logs,
        target_devices=target_devices
    )

@router.get("/{task_id}", response_model=TaskOut)
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    获取任务详情
    """
    # 验证令牌
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    # 获取任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 记录系统日志
    try:
        from app.services.system_log import create_system_log
        create_system_log(
            db=db,
            level="INFO",
            module="TASK",
            message=f"用户 {username} 查看任务详情 '{task.name}' (ID: {task.id})",
            user_id=None  # 可以进一步扩展以获取用户ID
        )
    except Exception as e:
        logger.error(f"记录系统日志失败: {str(e)}")
    
    # 转换为输出格式
    target_devices = []
    for device in task.target_devices:
        target_devices.append({
            "id": device.id,
            "name": device.name,
            "management_ip": device.management_ip
        })
    
    return TaskOut(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value if hasattr(task.task_type, 'value') else task.task_type,
        status=task.status.value if hasattr(task.status, 'value') else task.status,
        progress=task.progress,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        scheduled_time=task.scheduled_time,
        result=task.result,
        logs=task.logs,
        target_devices=target_devices
    )

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    更新任务状态
    """
    # 验证令牌
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    # 获取任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 记录原始状态
    original_status = task.status
    
    # 如果更新状态，使用统一的枚举处理函数
    if task_update.status:
        try:
            normalized_status = _normalize_enum_value(task_update.status, TaskStatus)
            # 直接设置字符串值，让数据库模型处理转换
            task.status = normalized_status
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # 更新其他字段
    if task_update.progress is not None:
        task.progress = task_update.progress
    if task_update.result is not None:
        task.result = task_update.result
    if task_update.logs is not None:
        task.logs = task_update.logs
    
    # 如果任务状态变为运行中，设置开始时间
    if task_update.status == TaskStatus.RUNNING and not task.started_at:
        task.started_at = datetime.utcnow()
    
    # 如果任务完成或失败，设置完成时间
    if task_update.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and not task.completed_at:
        task.completed_at = datetime.utcnow()
    
    # 保存到数据库
    db.commit()
    db.refresh(task)
    
    # 记录系统日志
    try:
        from app.services.system_log import create_system_log
        if original_status != task.status:
            create_system_log(
                db=db,
                level="INFO",
                module="TASK",
                message=f"用户 {username} 更新任务 '{task.name}' (ID: {task.id}) 状态从 '{original_status}' 变更为 '{task.status}'",
                user_id=None  # 可以进一步扩展以获取用户ID
            )
    except Exception as e:
        logger.error(f"记录系统日志失败: {str(e)}")
    
    # 转换为输出格式
    target_devices = []
    for device in task.target_devices:
        target_devices.append({
            "id": device.id,
            "name": device.name,
            "management_ip": device.management_ip
        })
    
    return TaskOut(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value if hasattr(task.task_type, 'value') else task.task_type,
        status=task.status.value if hasattr(task.status, 'value') else task.status,
        progress=task.progress,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        scheduled_time=task.scheduled_time,
        result=task.result,
        logs=task.logs,
        target_devices=target_devices
    )

@router.post("/{task_id}/execute")
def execute_task(
    task_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    执行任务
    """
    # 验证令牌
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    # 获取任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查任务状态，只能执行待处理的任务
    # 使用统一的枚举值处理方式
    current_status = _safe_get_status(task.status)
    expected_status = TaskStatus.PENDING.value  # "pending"
    
    # 将当前状态转换为小写进行比较，确保大小写不敏感
    if current_status.lower() != expected_status.lower():
        raise HTTPException(status_code=400, detail="只能执行待处理的任务")
    
    try:
        # 记录系统日志
        try:
            from app.services.system_log import create_system_log
            create_system_log(
                db=db,
                level="INFO",
                module="TASK",
                message=f"用户 {username} 手动执行任务 '{task.name}' (ID: {task_id})",
                user_id=None  # 可以进一步扩展以获取用户ID
            )
        except Exception as e:
            logger.error(f"记录系统日志失败: {str(e)}")
        
        # 直接调用调度器执行任务，而不是等待调度器轮询
        # 创建一个新的线程来执行任务，避免阻塞API响应
        scheduler.execute_task_now(task_id)
        
        return {"message": "任务已提交执行"}
            
    except Exception as e:
        logger.error(f"执行任务 {task_id} 失败: {str(e)}", exc_info=True)
        
        # 记录系统日志
        try:
            from app.services.system_log import create_system_log
            create_system_log(
                db=db,
                level="ERROR",
                module="TASK",
                message=f"用户 {username} 手动执行任务 '{task.name}' (ID: {task_id}) 失败: {str(e)}",
                user_id=None  # 可以进一步扩展以获取用户ID
            )
        except Exception as log_error:
            logger.error(f"记录系统日志失败: {str(log_error)}")
        
        raise HTTPException(status_code=500, detail=f"执行任务失败: {str(e)}")

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    删除任务
    """
    # 验证令牌
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    # 获取任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查任务状态，运行中的任务不能删除
    current_status = _safe_get_status(task.status)
    running_status = _safe_get_status(TaskStatus.RUNNING)
    if current_status == running_status:
        raise HTTPException(status_code=400, detail="运行中的任务不能被删除")
    
    task_name = task.name
    task_type = task.task_type
    
    # 删除任务
    db.delete(task)
    db.commit()
    
    # 记录系统日志
    try:
        from app.services.system_log import create_system_log
        create_system_log(
            db=db,
            level="INFO",
            module="TASK",
            message=f"用户 {username} 删除任务 '{task_name}' (ID: {task_id})，类型: {task_type}",
            user_id=None  # 可以进一步扩展以获取用户ID
        )
    except Exception as e:
        logger.error(f"记录系统日志失败: {str(e)}")
    
    return {"message": "任务删除成功"}


@router.get("/{task_id}/download-report")
def download_inspection_report(
    task_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    下载设备巡检任务报告
    """
    # 验证令牌
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    # 获取任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查任务类型是否为设备巡检
    task_type_str = _safe_get_task_type(task.task_type)
    if task_type_str != "device_inspection":
        raise HTTPException(status_code=400, detail="只有设备巡检任务可以下载报告")
    
    # 检查任务是否已完成
    status_str = _safe_get_status(task.status)
    completed_status = _safe_get_status(TaskStatus.COMPLETED)
    if status_str != completed_status:
        raise HTTPException(status_code=400, detail="只有已完成的任务可以下载报告")
    
    # 生成报告内容
    import io
    from fastapi.responses import Response
    
    # 构建报告内容
    report_content = f"""设备巡检报告

任务名称: {task.name}
任务ID: {task_id}
创建时间: {task.created_at}
开始时间: {task.started_at}
完成时间: {task.completed_at}
任务描述: {task.description or '无'}

巡检结果摘要:
{task.result}

详细日志:
{task.logs}

巡检设备列表:
"""
    for device in task.target_devices:
        report_content += f"- {device.name} ({device.management_ip})\n"

    # 将内容转换为字节
    report_bytes = report_content.encode('utf-8')

    # 创建响应
    response = Response(
        content=report_bytes,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=inspection_report_{task_id}.txt",
            "Content-Length": str(len(report_bytes))
        }
    )
    
    # 记录系统日志
    try:
        from app.services.system_log import create_system_log
        create_system_log(
            db=db,
            level="INFO",
            module="TASK",
            message=f"用户 {username} 下载设备巡检报告 '{task.name}' (ID: {task.id})",
            user_id=None
        )
    except Exception as e:
        logger.error(f"记录系统日志失败: {str(e)}")
    
    return response