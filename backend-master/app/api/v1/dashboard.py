from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.db import get_db
from app.services.models import Device, InterfaceStatus
import logging
import random

# 尝试导入psutil库，如果不存在则记录警告
try:
    import psutil  # 添加psutil库来获取系统资源使用情况
    PSUTIL_AVAILABLE = True
except ImportError:
    logging.warning("psutil库未安装，将无法获取系统性能数据。请运行 'pip install psutil' 安装。")
    PSUTIL_AVAILABLE = False

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test", response_model=Dict[str, Any])
def test_endpoint():
    """测试端点"""
    return {"message": "测试成功"}

@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表板统计数据
    
    返回:
        仪表板统计数据
    """
    try:
        # 使用单个查询获取所有设备状态统计
        from sqlalchemy import func
        status_counts = db.query(
            Device.status,
            func.count(Device.id)
        ).group_by(Device.status).all()
        
        # 初始化状态计数
        status_map = {status: count for status, count in status_counts}
        online_devices = status_map.get("online", 0)
        offline_devices = status_map.get("offline", 0)
        unknown_devices = status_map.get("unknown", 0)
        warning_devices = status_map.get("warning", 0)
        total_devices = sum(status_map.values())
        
        # 使用单个查询获取所有接口状态统计
        interface_status_counts = db.query(
            InterfaceStatus.operational_status,
            func.count(InterfaceStatus.id)
        ).group_by(InterfaceStatus.operational_status).all()
        
        # 初始化接口状态计数
        interface_status_map = {status: count for status, count in interface_status_counts}
        up_ports = interface_status_map.get("up", 0)
        down_ports = interface_status_map.get("down", 0)
        warning_ports = interface_status_map.get("warning", 0)
        total_ports = sum(interface_status_map.values())
        
        # 查询告警数据 - 使用设备状态作为告警来源
        total_alarms = warning_devices + unknown_devices
        unhandled_alarms = total_alarms  # 实际中应该有专门的告警状态字段
        
        # 查询用户数据 - 从设备表中获取基本用户信息
        # 这里假设每台在线设备代表一个活跃的"用户"或服务
        total_users = total_devices
        active_users = online_devices
        
        # 获取系统性能数据
        if PSUTIL_AVAILABLE:
            try:
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                memory_usage = memory_info.percent
                uptime = int(psutil.boot_time())
            except Exception as e:
                logger.warning(f"获取系统性能数据失败: {str(e)}，使用默认值")
                cpu_usage = 30
                memory_usage = 65
                uptime = 86400
        else:
            # 如果psutil不可用，使用默认值
            cpu_usage = 0
            memory_usage = 0
            uptime = 86400
        
        # 获取网络带宽使用情况（这里只是估算，实际应用中需要更精确的方法）
        if PSUTIL_AVAILABLE:
            try:
                net_io = psutil.net_io_counters()
                # 这里只是模拟带宽使用情况，实际应用中需要更精确的计算方式
                bandwidth_usage = min(100, int((net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024) % 100)
            except Exception as e:
                logger.warning(f"获取网络带宽数据失败: {str(e)}，使用默认值")
                bandwidth_usage = 45
        else:
            bandwidth_usage = 45
        
        stats = {
            "totalDevices": total_devices,
            "onlineDevices": online_devices,
            "offlineDevices": offline_devices,
            "unknownDevices": unknown_devices,
            "warningDevices": warning_devices,
            "totalPorts": total_ports,
            "upPorts": up_ports,
            "downPorts": down_ports,
            "warningPorts": warning_ports,
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalAlarms": total_alarms,
            "unhandledAlarms": unhandled_alarms,
            "bandwidthUsage": bandwidth_usage,
            "cpuUsage": cpu_usage,
            "memoryUsage": memory_usage,
            "uptime": int(uptime)
        }
        
        logger.debug(f"获取仪表板统计数据成功: {stats}")
        return stats
    except Exception as e:
        logger.error(f"获取仪表板统计数据失败: {str(e)}")
        # 出错时返回基本数据结构，但仍尝试从数据库获取关键信息
        try:
            # 使用聚合查询获取设备状态统计
            status_counts = db.query(
                Device.status,
                func.count(Device.id)
            ).group_by(Device.status).all()
            
            # 初始化状态计数
            status_map = {status: count for status, count in status_counts}
            online_devices = status_map.get("online", 0)
            offline_devices = status_map.get("offline", 0)
            warning_devices = status_map.get("warning", 0)
            unknown_devices = status_map.get("unknown", 0)
            total_devices = sum(status_map.values())
            
            # 计算告警数量
            total_alarms = warning_devices + unknown_devices
        except:
            # 如果数据库查询也失败，则使用安全的默认值
            total_devices = 0
            online_devices = 0
            offline_devices = 0
            unknown_devices = 0
            warning_devices = 0
            total_alarms = 0
            
        return {
            "totalDevices": total_devices,
            "onlineDevices": online_devices,
            "offlineDevices": offline_devices,
            "unknownDevices": unknown_devices,
            "warningDevices": warning_devices,
            "totalPorts": 0,
            "upPorts": 0,
            "downPorts": 0,
            "warningPorts": 0,
            "totalAlarms": total_alarms,
            "unhandledAlarms": total_alarms,
            "totalUsers": total_devices,
            "activeUsers": online_devices,
            "bandwidthUsage": 0,
            "cpuUsage": 0,
            "memoryUsage": 0,
            "uptime": 0
        }

@router.get("/performance", response_model=Dict[str, Any])
def get_performance_data(db: Session = Depends(get_db)):
    """获取设备性能数据
    
    返回:
        设备性能数据
    """
    try:
        from app.services.models import DevicePerformance
        import datetime
        
        # 查询最近24小时的性能数据
        start_time = datetime.datetime.now() - datetime.timedelta(hours=24)
        performance_records = db.query(
            DevicePerformance
        ).filter(
            DevicePerformance.timestamp >= start_time
        ).order_by(DevicePerformance.timestamp).all()
        
        # 初始化返回数据结构
        cpu_data = []
        memory_data = []
        bandwidth_data = []
        
        # 如果有历史性能数据，使用它们
        if performance_records:
            # 按时间分组数据
            time_map = {}
            for record in performance_records:
                time_key = record.timestamp.strftime("%H:%M")
                if time_key not in time_map:
                    time_map[time_key] = {
                        'cpu_usage': [],
                        'memory_usage': [],
                        'inbound_bandwidth': [],
                        'outbound_bandwidth': []
                    }
                
                if record.cpu_usage is not None:
                    time_map[time_key]['cpu_usage'].append(record.cpu_usage)
                if record.memory_usage is not None:
                    time_map[time_key]['memory_usage'].append(record.memory_usage)
                if record.inbound_bandwidth is not None:
                    time_map[time_key]['inbound_bandwidth'].append(record.inbound_bandwidth)
                if record.outbound_bandwidth is not None:
                    time_map[time_key]['outbound_bandwidth'].append(record.outbound_bandwidth)
            
            # 计算每小时的平均值
            for time_key in sorted(time_map.keys()):
                data = time_map[time_key]
                
                # 计算CPU平均使用率
                if data['cpu_usage']:
                    avg_cpu = sum(data['cpu_usage']) / len(data['cpu_usage'])
                    cpu_data.append({
                        "time": time_key,
                        "usage": round(avg_cpu, 2)
                    })
                
                # 计算内存平均使用率
                if data['memory_usage']:
                    avg_memory = sum(data['memory_usage']) / len(data['memory_usage'])
                    memory_data.append({
                        "time": time_key,
                        "usage": round(avg_memory, 2)
                    })
                
                # 计算带宽平均值
                if data['inbound_bandwidth'] or data['outbound_bandwidth']:
                    avg_in = sum(data['inbound_bandwidth']) / len(data['inbound_bandwidth']) if data['inbound_bandwidth'] else 0
                    avg_out = sum(data['outbound_bandwidth']) / len(data['outbound_bandwidth']) if data['outbound_bandwidth'] else 0
                    bandwidth_data.append({
                        "time": time_key,
                        "in": round(avg_in, 2),
                        "out": round(avg_out, 2)
                    })
        else:
            # 如果没有历史数据，生成模拟数据以供展示
            logger.info("没有找到性能历史数据，生成模拟数据")
            
            import datetime
            now = datetime.datetime.now()
            for i in range(24):
                time_point = (now - datetime.timedelta(hours=23-i)).strftime("%H:%M")
                
                # 生成模拟的性能数据
                import random
                cpu_usage = random.randint(10, 80)  # CPU使用率在10%-80%之间
                memory_usage = random.randint(20, 70)  # 内存使用率在20%-70%之间
                inbound_bw = random.randint(100, 1000)  # 入站带宽在100-1000之间
                outbound_bw = random.randint(50, 500)   # 出站带宽在50-500之间
                
                cpu_data.append({
                    "time": time_point,
                    "usage": cpu_usage
                })
                
                memory_data.append({
                    "time": time_point,
                    "usage": memory_usage
                })
                
                bandwidth_data.append({
                    "time": time_point,
                    "in": inbound_bw,
                    "out": outbound_bw
                })
        
        performance = {
            "cpu": cpu_data,
            "memory": memory_data,
            "bandwidth": bandwidth_data
        }
        
        logger.debug(f"获取设备性能数据成功，CPU数据点: {len(cpu_data)}, 内存数据点: {len(memory_data)}, 带宽数据点: {len(bandwidth_data)}")
        return performance
    except Exception as e:
        logger.error(f"获取设备性能数据失败: {str(e)}")
        # 返回默认的性能数据
        return {
            "cpu": [],
            "memory": [],
            "bandwidth": []
        }

@router.get("/warnings", response_model=List[Dict[str, Any]])
def get_warning_devices(db: Session = Depends(get_db)):
    """获取警告设备信息
    
    返回:
        警告设备列表
    """
    try:
        # 查询状态为warning的设备
        warning_devices = db.query(Device).filter(Device.status == "warning").all()
        
        # 如果没有warning设备，查询unknown设备作为备选
        if not warning_devices:
            warning_devices = db.query(Device).filter(Device.status == "unknown").all()
        
        result = []
        for device in warning_devices:
            result.append({
                "id": device.id,
                "name": device.name,
                "managementIp": device.management_ip,
                "vendor": device.vendor,
                "location": device.location,
                "status": device.status,
                "updatedAt": device.updated_at.isoformat() if device.updated_at else None
            })
        
        logger.debug(f"获取警告设备信息成功，共 {len(result)} 台设备")
        return result
    except Exception as e:
        logger.error(f"获取警告设备信息失败: {str(e)}")
        return []

@router.get("/dashboard-data", response_model=Dict[str, Any])
def get_dashboard_data(db: Session = Depends(get_db)):
    """获取仪表盘所需的所有数据（设备状态趋势、健康状况、网络流量）
    
    返回:
        包含设备状态趋势、健康状况和网络流量数据的字典
    """
    try:
        # 1. 获取设备状态分布和趋势数据
        status_counts = {
            "online": db.query(Device).filter(Device.status == "online").count(),
            "offline": db.query(Device).filter(Device.status == "offline").count(),
            "unknown": db.query(Device).filter(Device.status == "unknown").count(),
            "warning": db.query(Device).filter(Device.status == "warning").count()
        }
        
        # 查询最近7天的设备状态历史趋势数据
        import datetime
        from app.services.models import DeviceStatusHistory
        
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=6)  # 获取最近7天的数据（包括今天）
        
        # 查询历史数据
        history_records = db.query(DeviceStatusHistory).filter(
            DeviceStatusHistory.timestamp >= start_date
        ).order_by(DeviceStatusHistory.timestamp).all()
        
        # 构建趋势数据
        status_trend = {
            "dates": [],
            "online": [],
            "offline": []
        }
        
        # 如果有历史数据，使用真实数据
        if history_records:
            for record in history_records:
                # 格式化日期为 MM-DD
                date_str = record.timestamp.strftime("%m-%d")
                status_trend["dates"].append(date_str)
                status_trend["online"].append(record.online_count)
                status_trend["offline"].append(record.offline_count)
        else:
            # 如果没有历史数据，返回空数组，不生成模拟数据
            logger.info("没有找到设备状态历史数据，返回空数组")
            for i in range(7):
                date = (now - datetime.timedelta(days=6-i)).strftime("%m-%d")
                status_trend["dates"].append(date)
                status_trend["online"].append(0)
                status_trend["offline"].append(0)
        
        # 2. 获取设备健康数据
        from app.services.models import DevicePerformance
        import datetime
        
        # 查询最近24小时的性能数据
        start_time = datetime.datetime.now() - datetime.timedelta(hours=24)
        performance_records = db.query(
            DevicePerformance
        ).filter(
            DevicePerformance.timestamp >= start_time
        ).order_by(DevicePerformance.timestamp).all()
        
        # 初始化返回数据结构
        cpu_data = []
        memory_data = []
        bandwidth_data = []
        
        # 如果有历史性能数据，使用它们
        if performance_records:
            # 按时间分组数据
            time_map = {}
            for record in performance_records:
                time_key = record.timestamp.strftime("%H:%M")
                if time_key not in time_map:
                    time_map[time_key] = {
                        'cpu_usage': [],
                        'memory_usage': [],
                        'inbound_bandwidth': [],
                        'outbound_bandwidth': []
                    }
                
                if record.cpu_usage is not None:
                    time_map[time_key]['cpu_usage'].append(record.cpu_usage)
                if record.memory_usage is not None:
                    time_map[time_key]['memory_usage'].append(record.memory_usage)
                if record.inbound_bandwidth is not None:
                    time_map[time_key]['inbound_bandwidth'].append(record.inbound_bandwidth)
                if record.outbound_bandwidth is not None:
                    time_map[time_key]['outbound_bandwidth'].append(record.outbound_bandwidth)
            
            # 计算每小时的平均值
            for time_key in sorted(time_map.keys()):
                data = time_map[time_key]
                
                # 计算CPU平均使用率
                if data['cpu_usage']:
                    avg_cpu = sum(data['cpu_usage']) / len(data['cpu_usage'])
                    cpu_data.append({
                        "time": time_key,
                        "usage": round(avg_cpu, 2)
                    })
                
                # 计算内存平均使用率
                if data['memory_usage']:
                    avg_memory = sum(data['memory_usage']) / len(data['memory_usage'])
                    memory_data.append({
                        "time": time_key,
                        "usage": round(avg_memory, 2)
                    })
                
                # 计算带宽平均值
                if data['inbound_bandwidth'] or data['outbound_bandwidth']:
                    avg_in = sum(data['inbound_bandwidth']) / len(data['inbound_bandwidth']) if data['inbound_bandwidth'] else 0
                    avg_out = sum(data['outbound_bandwidth']) / len(data['outbound_bandwidth']) if data['outbound_bandwidth'] else 0
                    bandwidth_data.append({
                        "time": time_key,
                        "in": round(avg_in, 2),
                        "out": round(avg_out, 2)
                    })
        else:
            # 如果没有历史性能数据，获取最新的性能数据作为单个数据点
            logger.info("没有找到性能历史数据，获取最新的性能数据")
            
            # 获取所有设备的最新性能数据
            latest_performance = db.query(DevicePerformance).filter(
                DevicePerformance.timestamp >= datetime.datetime.now() - datetime.timedelta(minutes=5)  # 最近5分钟的数据
            ).order_by(DevicePerformance.timestamp.desc()).first()
            
            if latest_performance:
                # 使用最新性能数据作为单个数据点
                current_time = latest_performance.timestamp.strftime("%H:%M")
                
                if latest_performance.cpu_usage is not None:
                    cpu_data.append({
                        "time": current_time,
                        "usage": latest_performance.cpu_usage
                    })
                
                if latest_performance.memory_usage is not None:
                    memory_data.append({
                        "time": current_time,
                        "usage": latest_performance.memory_usage
                    })
                
                if latest_performance.inbound_bandwidth is not None or latest_performance.outbound_bandwidth is not None:
                    bandwidth_data.append({
                        "time": current_time,
                        "in": latest_performance.inbound_bandwidth or 0,
                        "out": latest_performance.outbound_bandwidth or 0
                    })
        
        # 3. 构建并返回完整的仪表盘数据
        dashboard_data = {
            "status_distribution": {
                "status": status_counts,
                "trend": status_trend
            },
            "health_data": {
                "cpu_usage": cpu_data,
                "memory_usage": memory_data
            },
            "traffic_data": {
                "bandwidth_usage": bandwidth_data
            }
        }
        
        logger.debug(f"获取仪表盘数据成功: {dashboard_data}")
        return dashboard_data
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {str(e)}")
        # 返回默认的仪表盘数据
        return {
            "status_distribution": {
                "status": {"online": 0, "offline": 0, "unknown": 0, "warning": 0},
                "trend": {
                    "dates": ["00:00"],
                    "online": [0],
                    "offline": [0]
                }
            },
            "health_data": {
                "cpu_usage": [],
                "memory_usage": []
            },
            "traffic_data": {
                "bandwidth_usage": []
            }
        }

@router.get("/device-status", response_model=Dict[str, Any])
def get_device_status_distribution(db: Session = Depends(get_db)):
    """获取设备状态分布
    
    返回:
        设备状态分布数据
    """
    try:
        # 查询各状态的设备数量
        status_counts = {
            "online": db.query(Device).filter(Device.status == "online").count(),
            "offline": db.query(Device).filter(Device.status == "offline").count(),
            "unknown": db.query(Device).filter(Device.status == "unknown").count(),
            "warning": db.query(Device).filter(Device.status == "warning").count()
        }
        
        # 查询最近7天的设备状态历史趋势数据
        import datetime
        from app.services.models import DeviceStatusHistory
        
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(days=6)  # 获取最近7天的数据（包括今天）
        
        # 查询历史数据
        history_records = db.query(DeviceStatusHistory).filter(
            DeviceStatusHistory.timestamp >= start_date
        ).order_by(DeviceStatusHistory.timestamp).all()
        
        # 构建趋势数据
        status_trend = {
            "dates": [],
            "online": [],
            "offline": []
        }
        
        # 如果有历史数据，使用真实数据
        if history_records:
            for record in history_records:
                # 格式化日期为 MM-DD
                date_str = record.timestamp.strftime("%m-%d")
                status_trend["dates"].append(date_str)
                status_trend["online"].append(record.online_count)
                status_trend["offline"].append(record.offline_count)
        else:
            # 如果没有历史数据，生成模拟数据
            logger.info("没有找到设备状态历史数据，生成模拟趋势数据")
            for i in range(7):
                date = (now - datetime.timedelta(days=6-i)).strftime("%m-%d")
                status_trend["dates"].append(date)
                # 使用当前状态作为基础，添加一些变化
                online_count = status_counts["online"] + random.randint(-2, 2)
                offline_count = status_counts["offline"] + random.randint(-2, 2)
                status_trend["online"].append(max(0, online_count))  # 确保不为负数
                status_trend["offline"].append(max(0, offline_count))  # 确保不为负数
        
        # 查询各厂商的设备数量
        vendor_counts = {}
        vendors = db.query(Device.vendor).distinct().all()
        for vendor in vendors:
            vendor_name = vendor[0]
            vendor_counts[vendor_name] = db.query(Device).filter(Device.vendor == vendor_name).count()
        
        # 查询各类型的设备数量
        type_counts = {}
        device_types = db.query(Device.device_type).distinct().all()
        for device_type in device_types:
            type_name = device_type[0] if device_type[0] else "Unknown"
            type_counts[type_name] = db.query(Device).filter(Device.device_type == device_type[0]).count()
        
        result = {
            "status": status_counts,
            "vendor": vendor_counts,
            "type": type_counts,
            "trend": status_trend
        }
        
        logger.debug(f"获取设备状态分布成功: {result}")
        return result
    except Exception as e:
        logger.error(f"获取设备状态分布失败: {str(e)}")
        # 返回默认的状态分布
        import random
        return {
            "status": {"online": 0, "offline": 0, "unknown": 0, "warning": 0},
            "vendor": {},
            "type": {},
            "trend": {
                "dates": [],
                "online": [],
                "offline": []
            }
        }
