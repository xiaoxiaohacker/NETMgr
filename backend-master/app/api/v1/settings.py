import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from app.services.db import get_db
from app.services.models import Device, SystemSettings
from app.services.schemas import (
    BasicSettings,
    ScanSettings,
    NotificationSettings,
    SystemSettingsOut,
    SystemSettingsCreate,
    SystemSettingsUpdate
)
from app.api.v1.auth import oauth2_scheme, decode_access_token
from app.services.config import DATABASE_URL, REDIS_URL
from app.services.system_log import create_system_log

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

# 默认系统设置
DEFAULT_SETTINGS = {
    "system": {
        "name": "NetMgr 网络管理系统",
        "description": "企业级网络设备管理系统",
        "language": "zh-CN",
        "timezone": "Asia/Shanghai"
    },
    "scan": {
        "interval": 3600,  # 扫描间隔（秒）
        "ip_ranges": ["192.168.1.0/24"],  # IP扫描范围
        "ports": [22, 23, 80, 443],  # 扫描端口
        "timeout": 5  # 连接超时（秒）
    },
    "notification": {
        "email_enabled": False,
        "smtp_server": "",
        "smtp_port": 587,
        "smtp_username": "",
        "smtp_password": "",
        "sms_enabled": False,
        "sms_api_url": "",
        "sms_api_key": ""
    },
    "maintenance": {
        "log_retention_days": 30,
        "backup_retention_days": 90
    }
}

def get_setting(db: Session, setting_key: str):
    """获取单个设置项"""
    return db.query(SystemSettings).filter(SystemSettings.setting_key == setting_key).first()

def set_setting(db: Session, setting_key: str, setting_value: str, description: str = None):
    """设置单个设置项"""
    setting = get_setting(db, setting_key)
    if setting:
        # 更新现有设置
        setting.setting_value = setting_value
        if description:
            setting.description = description
    else:
        # 创建新设置
        setting = SystemSettings(
            setting_key=setting_key,
            setting_value=setting_value,
            description=description
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    return setting

@router.get("/basic", response_model=Dict[str, Any])
def get_basic_settings(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取基本设置
    
    返回:
        基本设置信息
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 获取基本设置
        basic_setting = get_setting(db, "basic_settings")
        if basic_setting:
            basic_settings = json.loads(basic_setting.setting_value)
        else:
            # 如果没有设置，则使用默认值
            basic_settings = {
                "systemName": "网络设备管理系统",
                "description": "一套完整的企业级网络设备管理解决方案",
                "language": "zh-CN",
                "timezone": "Asia/Shanghai"
            }
        
        logger.info(f"用户 {username} 获取基本设置")
        return basic_settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基本设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取基本设置失败")

@router.put("/basic", response_model=Dict[str, Any])
def update_basic_settings(
    settings: BasicSettings,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新基本设置
    
    参数:
        settings: 基本设置数据
    
    返回:
        更新结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 保存设置到数据库
        settings_dict = settings.dict()
        set_setting(
            db, 
            "basic_settings", 
            json.dumps(settings_dict, ensure_ascii=False), 
            "系统基本设置"
        )
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 更新了基本设置",
            user_id=None,  # 后续可从token中获取用户ID
            device_id=None
        )
        
        logger.info(f"用户 {username} 更新基本设置成功")
        return {"message": "基本设置更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新基本设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新基本设置失败")

@router.get("/scan", response_model=Dict[str, Any])
def get_scan_settings(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取扫描设置
    
    返回:
        扫描设置信息
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 获取扫描设置
        scan_setting = get_setting(db, "scan_settings")
        if scan_setting:
            scan_settings = json.loads(scan_setting.setting_value)
        else:
            # 如果没有设置，则使用默认值
            scan_settings = {
                "enabled": True,
                "interval": 30,
                "ipRange": "192.168.1.0/24",
                "ports": "22,23,80,443",
                "vendors": ["Cisco", "Huawei", "H3C"]
            }
        
        logger.info(f"用户 {username} 获取扫描设置")
        return scan_settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取扫描设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取扫描设置失败")

@router.put("/scan", response_model=Dict[str, Any])
def update_scan_settings(
    settings: ScanSettings,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新扫描设置
    
    参数:
        settings: 扫描设置数据
    
    返回:
        更新结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 保存设置到数据库
        settings_dict = settings.dict()
        set_setting(
            db, 
            "scan_settings", 
            json.dumps(settings_dict, ensure_ascii=False), 
            "设备扫描设置"
        )
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 更新了扫描设置",
            user_id=None,  # 后续可从token中获取用户ID
            device_id=None
        )
        
        logger.info(f"用户 {username} 更新扫描设置成功")
        return {"message": "扫描设置更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新扫描设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新扫描设置失败")

@router.get("/notification", response_model=Dict[str, Any])
def get_notification_settings(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取通知设置
    
    返回:
        通知设置信息
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 获取通知设置
        notification_setting = get_setting(db, "notification_settings")
        if notification_setting:
            notification_settings = json.loads(notification_setting.setting_value)
        else:
            # 如果没有设置，则使用默认值
            notification_settings = {
                "emailEnabled": True,
                "smtpServer": "smtp.example.com",
                "smtpPort": 587,
                "smtpUsername": "admin@example.com",
                "smtpPassword": "",
                "senderEmail": "admin@example.com",
                "recipients": "user1@example.com,user2@example.com",
                "smsEnabled": False,
                "smsGateway": "",
                "smsApiKey": "",
                "smsSignature": ""
            }
        
        logger.info(f"用户 {username} 获取通知设置")
        return notification_settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取通知设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取通知设置失败")

@router.put("/notification", response_model=Dict[str, Any])
def update_notification_settings(
    settings: NotificationSettings,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新通知设置
    
    参数:
        settings: 通知设置数据
    
    返回:
        更新结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 保存设置到数据库（密码需要加密）
        settings_dict = settings.dict()
        
        # 如果密码为空或未更改，从数据库获取旧值
        current_setting = get_setting(db, "notification_settings")
        if current_setting:
            current_data = json.loads(current_setting.setting_value)
            if not settings_dict['smtpPassword'] or settings_dict['smtpPassword'] == current_data.get('smtpPassword', ''):
                settings_dict['smtpPassword'] = current_data.get('smtpPassword', '')
        
        set_setting(
            db, 
            "notification_settings", 
            json.dumps(settings_dict, ensure_ascii=False), 
            "通知设置"
        )
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 更新了通知设置",
            user_id=None,  # 后续可从token中获取用户ID
            device_id=None
        )
        
        logger.info(f"用户 {username} 更新通知设置成功")
        return {"message": "通知设置更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新通知设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新通知设置失败")

@router.post("/notification/test", response_model=Dict[str, Any])
def test_notifications(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """测试通知功能
    
    返回:
        测试结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 获取通知设置
        notification_setting = get_setting(db, "notification_settings")
        if notification_setting:
            notification_settings = json.loads(notification_setting.setting_value)
        else:
            notification_settings = {}
        
        # 模拟发送测试通知
        # 这里应该实现实际的邮件/短信发送逻辑
        logger.info(f"用户 {username} 执行通知测试")
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 执行了通知测试",
            user_id=None,
            device_id=None
        )
        
        return {
            "message": "通知测试已发送",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行通知测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail="执行通知测试失败")

@router.post("/maintenance/cleanup-logs", response_model=Dict[str, Any])
def cleanup_logs(
    days: int = 30,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """清理日志数据
    
    参数:
        days: 保留天数
    
    返回:
        清理结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 这里应该实现实际的日志清理逻辑
        # 目前只是模拟操作
        logger.info(f"用户 {username} 执行日志清理操作，保留 {days} 天")
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 执行了日志清理，保留 {days} 天",
            user_id=None,
            device_id=None
        )
        
        return {
            "message": f"日志清理操作已提交，将保留最近 {days} 天的日志",
            "status": "submitted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行日志清理操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail="执行日志清理操作失败")

@router.post("/maintenance/backup-system", response_model=Dict[str, Any])
def backup_system(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """备份系统数据
    
    返回:
        备份结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 这里应该实现实际的系统备份逻辑
        # 目前只是模拟操作
        logger.info(f"用户 {username} 执行系统备份操作")
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 执行了系统备份",
            user_id=None,
            device_id=None
        )
        
        return {
            "message": "系统备份操作已提交",
            "status": "submitted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行系统备份操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail="执行系统备份操作失败")

@router.post("/maintenance/restart", response_model=Dict[str, Any])
def restart_system(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """重启系统服务
    
    返回:
        重启结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 这里应该实现实际的系统重启逻辑
        # 目前只是模拟操作
        logger.info(f"用户 {username} 执行系统重启操作")
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 执行了系统重启",
            user_id=None,
            device_id=None
        )
        
        return {
            "message": "系统重启操作已提交",
            "status": "submitted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行系统重启操作失败: {str(e)}")
        raise HTTPException(status_code=500, detail="执行系统重启操作失败")

@router.post("/scan/discover", response_model=Dict[str, Any])
def scan_network_hosts(
    ip_range: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """扫描网络发现主机
    
    参数:
        ip_range: 要扫描的IP范围，例如 "192.168.1.0/24"
    
    返回:
        扫描结果，包括发现的主机和与现有设备的比对
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        import subprocess
        import ipaddress
        import threading
        import time
        import platform
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 获取所有现有设备的IP
        existing_devices = db.query(Device).all()
        existing_ips = {device.management_ip for device in existing_devices}
        
        discovered_hosts = []
        
        # 解析IP范围
        try:
            network = ipaddress.IPv4Network(ip_range, strict=False)
        except ValueError:
            logger.error(f"无效的IP范围: {ip_range}")
            raise HTTPException(status_code=400, detail="无效的IP范围格式")
        
        # 根据操作系统确定ping命令参数
        is_windows = platform.system().lower() == "windows"
        
        def ping_host(ip):
            try:
                if is_windows:
                    # Windows下使用ping命令
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "1000", str(ip)],  # Windows: -n次数 -w超时(毫秒)
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2
                    )
                else:
                    # Linux/Unix下使用ping命令
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", "1", str(ip)],  # Linux: -c次数 -W超时(秒)
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2
                    )
                return str(ip) if result.returncode == 0 else None
            except subprocess.TimeoutExpired:
                return None
        
        # 扫描网络中的主机
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(ping_host, ip): ip for ip in network}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    discovered_hosts.append(result)
        
        # 对比发现的主机和现有设备
        new_hosts = [host for host in discovered_hosts if host not in existing_ips]
        existing_hosts = [host for host in discovered_hosts if host in existing_ips]
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SCAN",
            message=f"用户 {username} 执行了网络扫描，发现 {len(discovered_hosts)} 个主机，其中 {len(new_hosts)} 个为新主机",
            user_id=None,
            device_id=None
        )
        
        logger.info(f"用户 {username} 执行网络扫描，发现 {len(discovered_hosts)} 个主机，其中 {len(new_hosts)} 个新主机")
        
        return {
            "message": f"网络扫描完成，发现 {len(discovered_hosts)} 个主机",
            "total_discovered": len(discovered_hosts),
            "new_hosts": new_hosts,
            "existing_hosts": existing_hosts,
            "new_count": len(new_hosts),
            "existing_count": len(existing_hosts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行网络扫描失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行网络扫描失败: {str(e)}")

@router.get("/system-info", response_model=Dict[str, Any])
def get_system_info(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取系统信息
    
    返回:
        系统信息
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 获取系统信息
        device_count = db.query(Device).count()
        
        # 记录系统日志
        create_system_log(
            db=db,
            level="INFO",
            module="SETTINGS",
            message=f"用户 {username} 查看了系统信息",
            user_id=None,
            device_id=None
        )
        
        logger.info(f"用户 {username} 获取系统信息")
        return {
            "version": "1.0.0",
            "database_url": DATABASE_URL,
            "redis_url": REDIS_URL,
            "device_count": device_count,
            "system_name": "NetMgr 网络管理系统",
            "uptime": "N/A"  # 实际部署时应从系统启动时间计算
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统信息失败")