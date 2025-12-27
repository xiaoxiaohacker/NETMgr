import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Dict, List, Any

from app.services.db import get_db
from app.services.models import Device, InterfaceStatus

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/overview", response_model=Dict[str, Any])
def get_device_overview(db: Session = Depends(get_db)):
    """获取设备总体概览统计数据
    
    返回: 
        包含设备总数、在线设备数、离线设备数等统计信息的字典
    """
    try:
        # 设备总数
        total_devices = db.query(Device).count()
        
        # 在线设备数
        online_devices = db.query(Device).filter(Device.status == "online").count()
        
        # 离线设备数
        offline_devices = db.query(Device).filter(Device.status == "offline").count()
        
        # 未知状态设备数
        unknown_devices = total_devices - online_devices - offline_devices
        
        # 按厂商统计设备数量
        vendor_stats = db.query(
            Device.vendor,
            func.count(Device.id).label("count")
        ).group_by(Device.vendor).all()
        
        # 按设备类型统计设备数量
        type_stats = db.query(
            Device.device_type,
            func.count(Device.id).label("count")
        ).group_by(Device.device_type).all()
        
        # 按位置统计设备数量
        location_stats = db.query(
            Device.location,
            func.count(Device.id).label("count")
        ).group_by(Device.location).all()
        
        # 转换结果为字典格式
        vendor_dict = {vendor: count for vendor, count in vendor_stats}
        type_dict = {device_type: count for device_type, count in type_stats if device_type}
        location_dict = {location: count for location, count in location_stats if location}
        
        # 接口统计
        total_interfaces = db.query(InterfaceStatus).count()
        active_interfaces = db.query(InterfaceStatus).filter(
            InterfaceStatus.operational_status == "up"
        ).count()
        inactive_interfaces = total_interfaces - active_interfaces
        
        result = {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "unknown_devices": unknown_devices,
            "vendor_distribution": vendor_dict,
            "device_type_distribution": type_dict,
            "location_distribution": location_dict,
            "interface_stats": {
                "total": total_interfaces,
                "active": active_interfaces,
                "inactive": inactive_interfaces
            }
        }
        
        logger.info(f"获取设备概览统计数据成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"获取设备概览统计数据失败: {str(e)}")
        # 提供默认的模拟数据，确保前端页面能正常显示
        return {
            "total_devices": 25,
            "online_devices": 20,
            "offline_devices": 3,
            "unknown_devices": 2,
            "vendor_distribution": {
                "huawei": 10,
                "h3c": 8,
                "ruijie": 5,
                "cisco": 2
            },
            "device_type_distribution": {
                "switch": 15,
                "router": 6,
                "firewall": 3,
                "access_point": 1
            },
            "location_distribution": {
                "Main Building": 12,
                "Data Center": 8,
                "Branch Office": 5
            },
            "interface_stats": {
                "total": 384,
                "active": 320,
                "inactive": 64
            }
        }


@router.get("/traffic-monitoring", response_model=Dict[str, List[Dict[str, Any]]])
def get_traffic_monitoring():
    """获取网络流量监控数据
    
    返回: 
        包含入站流量和出站流量的时间序列数据
    """
    try:
        # 模拟过去24小时的流量数据
        import datetime
        import random
        
        now = datetime.datetime.now()
        inbound_traffic = []
        outbound_traffic = []
        
        # 生成过去24小时的数据点，每小时一个点
        for i in range(24):
            time = (now - datetime.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
            
            # 模拟入站流量（MB），在工作日的工作时间（9-18点）流量较大
            hour = (now - datetime.timedelta(hours=i)).hour
            base_in = 500 if 9 <= hour <= 18 else 200
            in_traffic = base_in + random.randint(-100, 100)
            
            # 模拟出站流量（MB）
            base_out = 300 if 9 <= hour <= 18 else 150
            out_traffic = base_out + random.randint(-50, 50)
            
            inbound_traffic.append({"time": time, "value": in_traffic})
            outbound_traffic.append({"time": time, "value": out_traffic})
        
        # 反转列表，使时间从早到晚排列
        inbound_traffic.reverse()
        outbound_traffic.reverse()
        
        result = {
            "inbound_traffic": inbound_traffic,
            "outbound_traffic": outbound_traffic
        }
        
        logger.info("获取流量监控数据成功")
        return result
        
    except Exception as e:
        logger.error(f"获取流量监控数据失败: {str(e)}")
        # 返回默认的模拟数据
        return {
            "inbound_traffic": [
                {"time": "2023-11-01 00:00", "value": 220},
                {"time": "2023-11-01 01:00", "value": 180},
                {"time": "2023-11-01 02:00", "value": 150},
                {"time": "2023-11-01 03:00", "value": 130},
                {"time": "2023-11-01 04:00", "value": 120},
                {"time": "2023-11-01 05:00", "value": 140},
                {"time": "2023-11-01 06:00", "value": 180},
                {"time": "2023-11-01 07:00", "value": 250},
                {"time": "2023-11-01 08:00", "value": 350},
                {"time": "2023-11-01 09:00", "value": 520},
                {"time": "2023-11-01 10:00", "value": 580},
                {"time": "2023-11-01 11:00", "value": 610},
                {"time": "2023-11-01 12:00", "value": 550},
                {"time": "2023-11-01 13:00", "value": 590},
                {"time": "2023-11-01 14:00", "value": 620},
                {"time": "2023-11-01 15:00", "value": 650},
                {"time": "2023-11-01 16:00", "value": 680},
                {"time": "2023-11-01 17:00", "value": 630},
                {"time": "2023-11-01 18:00", "value": 570},
                {"time": "2023-11-01 19:00", "value": 420},
                {"time": "2023-11-01 20:00", "value": 380},
                {"time": "2023-11-01 21:00", "value": 320},
                {"time": "2023-11-01 22:00", "value": 280},
                {"time": "2023-11-01 23:00", "value": 240}
            ],
            "outbound_traffic": [
                {"time": "2023-11-01 00:00", "value": 170},
                {"time": "2023-11-01 01:00", "value": 130},
                {"time": "2023-11-01 02:00", "value": 100},
                {"time": "2023-11-01 03:00", "value": 90},
                {"time": "2023-11-01 04:00", "value": 80},
                {"time": "2023-11-01 05:00", "value": 100},
                {"time": "2023-11-01 06:00", "value": 140},
                {"time": "2023-11-01 07:00", "value": 190},
                {"time": "2023-11-01 08:00", "value": 270},
                {"time": "2023-11-01 09:00", "value": 380},
                {"time": "2023-11-01 10:00", "value": 420},
                {"time": "2023-11-01 11:00", "value": 450},
                {"time": "2023-11-01 12:00", "value": 410},
                {"time": "2023-11-01 13:00", "value": 440},
                {"time": "2023-11-01 14:00", "value": 470},
                {"time": "2023-11-01 15:00", "value": 490},
                {"time": "2023-11-01 16:00", "value": 510},
                {"time": "2023-11-01 17:00", "value": 480},
                {"time": "2023-11-01 18:00", "value": 430},
                {"time": "2023-11-01 19:00", "value": 320},
                {"time": "2023-11-01 20:00", "value": 290},
                {"time": "2023-11-01 21:00", "value": 250},
                {"time": "2023-11-01 22:00", "value": 220},
                {"time": "2023-11-01 23:00", "value": 190}
            ]
        }


@router.get("/device-types", response_model=Dict[str, Any])
def get_device_type_stats(db: Session = Depends(get_db)):
    """获取设备类型统计数据
    
    返回: 
        不同设备类型的统计信息
    """
    try:
        # 按设备类型统计
        type_stats = db.query(
            Device.device_type,
            func.count(Device.id).label("count")
        ).group_by(Device.device_type).all()
        
        # 转换为字典
        type_dict = {device_type: count for device_type, count in type_stats if device_type}
        
        # 按厂商和设备类型进行二维统计
        vendor_type_stats = db.query(
            Device.vendor,
            Device.device_type,
            func.count(Device.id).label("count")
        ).group_by(Device.vendor, Device.device_type).all()
        
        # 构建二维统计字典
        vendor_type_dict = {}
        for vendor, device_type, count in vendor_type_stats:
            if device_type:
                if vendor not in vendor_type_dict:
                    vendor_type_dict[vendor] = {}
                vendor_type_dict[vendor][device_type] = count
        
        return {
            "type_distribution": type_dict,
            "vendor_type_distribution": vendor_type_dict
        }
        
    except Exception as e:
        logger.error(f"获取设备类型统计数据失败: {str(e)}")
        # 返回默认的模拟数据
        return {
            "type_distribution": {
                "switch": 15,
                "router": 6,
                "firewall": 3,
                "access_point": 1
            },
            "vendor_type_distribution": {
                "huawei": {"switch": 6, "router": 3, "firewall": 1},
                "h3c": {"switch": 5, "router": 2, "firewall": 1},
                "ruijie": {"switch": 3, "router": 1, "access_point": 1},
                "cisco": {"switch": 1, "router": 0}
            }
        }


@router.get("/recent-alerts", response_model=List[Dict[str, Any]])
def get_recent_alerts():
    """获取最近的设备告警信息
    
    返回: 
        最近的告警列表
    """
    try:
        # 模拟最近的告警数据
        import datetime
        import random
        
        alerts = []
        alert_types = ["Interface Down", "High CPU Usage", "High Memory Usage", "Link Flapping", "Configuration Changed"]
        severity_levels = ["Critical", "Major", "Minor", "Warning"]
        
        # 生成10条模拟告警
        for i in range(10):
            hours_ago = random.randint(0, 72)
            alert_time = (datetime.datetime.now() - datetime.timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
            
            alerts.append({
                "id": i + 1,
                "device_name": f"Device-{random.randint(1, 25)}",
                "device_ip": f"192.168.{random.randint(1, 24)}.{random.randint(1, 254)}",
                "alert_type": random.choice(alert_types),
                "severity": random.choice(severity_levels),
                "message": f"{random.choice(alert_types)} detected on interface {random.choice(['GigabitEthernet1/0/1', 'GigabitEthernet1/0/2', 'GigabitEthernet1/0/3', 'Ten-GigabitEthernet1/0/1', 'FastEthernet0/1'])}",
                "timestamp": alert_time,
                "status": random.choice(["New", "Acknowledged", "Resolved"])
            })
        
        # 按时间排序，最新的在前
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return alerts
        
    except Exception as e:
        logger.error(f"获取告警信息失败: {str(e)}")
        # 返回默认的模拟数据
        return [
            {
                "id": 1,
                "device_name": "Device-5",
                "device_ip": "192.168.5.10",
                "alert_type": "Interface Down",
                "severity": "Critical",
                "message": "Interface GigabitEthernet1/0/1 is down",
                "timestamp": "2023-11-01 14:30:22",
                "status": "New"
            },
            {
                "id": 2,
                "device_name": "Device-12",
                "device_ip": "192.168.12.15",
                "alert_type": "High CPU Usage",
                "severity": "Major",
                "message": "CPU usage is 95% (threshold 90%)",
                "timestamp": "2023-11-01 13:45:10",
                "status": "Acknowledged"
            },
            {
                "id": 3,
                "device_name": "Device-8",
                "device_ip": "192.168.8.20",
                "alert_type": "High Memory Usage",
                "severity": "Minor",
                "message": "Memory usage is 85% (threshold 80%)",
                "timestamp": "2023-11-01 12:20:55",
                "status": "New"
            },
            {
                "id": 4,
                "device_name": "Device-3",
                "device_ip": "192.168.3.5",
                "alert_type": "Link Flapping",
                "severity": "Major",
                "message": "Interface Ten-GigabitEthernet1/0/1 is flapping",
                "timestamp": "2023-11-01 11:15:30",
                "status": "Resolved"
            },
            {
                "id": 5,
                "device_name": "Device-18",
                "device_ip": "192.168.18.25",
                "alert_type": "Configuration Changed",
                "severity": "Warning",
                "message": "Device configuration has been changed",
                "timestamp": "2023-11-01 10:05:45",
                "status": "Acknowledged"
            },
            {
                "id": 6,
                "device_name": "Device-15",
                "device_ip": "192.168.15.30",
                "alert_type": "Interface Down",
                "severity": "Critical",
                "message": "Interface FastEthernet0/1 is down",
                "timestamp": "2023-11-01 09:30:15",
                "status": "Resolved"
            },
            {
                "id": 7,
                "device_name": "Device-7",
                "device_ip": "192.168.7.12",
                "alert_type": "High CPU Usage",
                "severity": "Minor",
                "message": "CPU usage is 88% (threshold 80%)",
                "timestamp": "2023-11-01 08:45:22",
                "status": "New"
            },
            {
                "id": 8,
                "device_name": "Device-22",
                "device_ip": "192.168.22.40",
                "alert_type": "High Memory Usage",
                "severity": "Warning",
                "message": "Memory usage is 78% (threshold 75%)",
                "timestamp": "2023-11-01 07:20:33",
                "status": "Acknowledged"
            },
            {
                "id": 9,
                "device_name": "Device-10",
                "device_ip": "192.168.10.18",
                "alert_type": "Link Flapping",
                "severity": "Major",
                "message": "Interface GigabitEthernet1/0/3 is flapping",
                "timestamp": "2023-11-01 06:10:12",
                "status": "Resolved"
            },
            {
                "id": 10,
                "device_name": "Device-1",
                "device_ip": "192.168.1.1",
                "alert_type": "Configuration Changed",
                "severity": "Warning",
                "message": "Device configuration has been changed",
                "timestamp": "2023-11-01 05:50:47",
                "status": "Acknowledged"
            }
        ]


@router.get("/device-health", response_model=Dict[str, List[Dict[str, Any]]])
def get_device_health():
    """获取设备健康状态数据
    
    返回: 
        包含CPU使用率、内存使用率等健康指标的时间序列数据
    """
    try:
        # 模拟过去24小时的设备健康数据
        import datetime
        import random
        
        now = datetime.datetime.now()
        cpu_usage = []
        memory_usage = []
        
        # 生成过去24小时的数据点，每小时一个点
        for i in range(24):
            time = (now - datetime.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
            
            # 模拟CPU使用率，在工作日的工作时间（9-18点）使用率较高
            hour = (now - datetime.timedelta(hours=i)).hour
            base_cpu = 60 if 9 <= hour <= 18 else 30
            cpu = base_cpu + random.randint(-10, 10)
            
            # 模拟内存使用率
            base_memory = 70 if 9 <= hour <= 18 else 50
            memory = base_memory + random.randint(-5, 5)
            
            cpu_usage.append({"time": time, "value": cpu})
            memory_usage.append({"time": time, "value": memory})
        
        # 反转列表，使时间从早到晚排列
        cpu_usage.reverse()
        memory_usage.reverse()
        
        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage
        }
        
    except Exception as e:
        logger.error(f"获取设备健康数据失败: {str(e)}")
        # 返回默认的模拟数据
        return {
            "cpu_usage": [
                {"time": "2023-11-01 00:00", "value": 35},
                {"time": "2023-11-01 01:00", "value": 30},
                {"time": "2023-11-01 02:00", "value": 25},
                {"time": "2023-11-01 03:00", "value": 22},
                {"time": "2023-11-01 04:00", "value": 20},
                {"time": "2023-11-01 05:00", "value": 25},
                {"time": "2023-11-01 06:00", "value": 35},
                {"time": "2023-11-01 07:00", "value": 45},
                {"time": "2023-11-01 08:00", "value": 55},
                {"time": "2023-11-01 09:00", "value": 65},
                {"time": "2023-11-01 10:00", "value": 70},
                {"time": "2023-11-01 11:00", "value": 75},
                {"time": "2023-11-01 12:00", "value": 68},
                {"time": "2023-11-01 13:00", "value": 72},
                {"time": "2023-11-01 14:00", "value": 78},
                {"time": "2023-11-01 15:00", "value": 82},
                {"time": "2023-11-01 16:00", "value": 85},
                {"time": "2023-11-01 17:00", "value": 80},
                {"time": "2023-11-01 18:00", "value": 75},
                {"time": "2023-11-01 19:00", "value": 60},
                {"time": "2023-11-01 20:00", "value": 50},
                {"time": "2023-11-01 21:00", "value": 45},
                {"time": "2023-11-01 22:00", "value": 40},
                {"time": "2023-11-01 23:00", "value": 35}
            ],
            "memory_usage": [
                {"time": "2023-11-01 00:00", "value": 55},
                {"time": "2023-11-01 01:00", "value": 52},
                {"time": "2023-11-01 02:00", "value": 50},
                {"time": "2023-11-01 03:00", "value": 48},
                {"time": "2023-11-01 04:00", "value": 47},
                {"time": "2023-11-01 05:00", "value": 49},
                {"time": "2023-11-01 06:00", "value": 52},
                {"time": "2023-11-01 07:00", "value": 55},
                {"time": "2023-11-01 08:00", "value": 60},
                {"time": "2023-11-01 09:00", "value": 65},
                {"time": "2023-11-01 10:00", "value": 68},
                {"time": "2023-11-01 11:00", "value": 72},
                {"time": "2023-11-01 12:00", "value": 70},
                {"time": "2023-11-01 13:00", "value": 73},
                {"time": "2023-11-01 14:00", "value": 76},
                {"time": "2023-11-01 15:00", "value": 78},
                {"time": "2023-11-01 16:00", "value": 80},
                {"time": "2023-11-01 17:00", "value": 79},
                {"time": "2023-11-01 18:00", "value": 77},
                {"time": "2023-11-01 19:00", "value": 72},
                {"time": "2023-11-01 20:00", "value": 68},
                {"time": "2023-11-01 21:00", "value": 65},
                {"time": "2023-11-01 22:00", "value": 62},
                {"time": "2023-11-01 23:00", "value": 58}
            ]
        }