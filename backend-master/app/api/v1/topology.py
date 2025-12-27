import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.services.db import get_db
from app.services.models import Device, InterfaceStatus
from app.api.v1.auth import oauth2_scheme, decode_access_token
from app.services.adapter_manager import AdapterManager
from app.services.encryption import decrypt_device_password

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

# 创建线程池用于执行耗时的设备数据收集任务
executor = ThreadPoolExecutor(max_workers=3)

def collect_interface_data_sync(db: Session):
    """同步收集设备接口数据并存储到数据库"""
    try:
        logger.info("开始收集设备接口数据...")
        
        # 删除现有的接口状态数据
        db.query(InterfaceStatus).delete()
        
        # 获取所有设备
        devices = db.query(Device).all()
        
        # 收集每个设备的接口信息
        for device in devices:
            try:
                # 解密设备密码
                decrypted_password = decrypt_device_password(device.password)
                decrypted_enable_password = (
                    decrypt_device_password(device.enable_password) 
                    if device.enable_password else None
                )

                # 创建设备连接信息字典
                device_info = {
                    'management_ip': device.management_ip,
                    'vendor': device.vendor,
                    'username': device.username,
                    'password': decrypted_password,
                    'port': device.port
                }
                
                # 如果有enable密码，也添加进去
                if decrypted_enable_password:
                    device_info['enable_password'] = decrypted_enable_password
                
                # 创建适配器
                adapter = AdapterManager.get_adapter(device_info)
                
                # 获取接口信息
                interfaces = adapter.get_interfaces()
                adapter.disconnect()
                
                # 将接口信息存储到数据库
                if interfaces:
                    for interface in interfaces:
                        # 解析接口信息
                        interface_name = interface.get('name', '')
                        admin_status = interface.get('admin_status', 'unknown')
                        operational_status = interface.get('oper_status', 'unknown')
                        mac_address = interface.get('mac_address')
                        ip_address = interface.get('ip_address')
                        speed = interface.get('speed')
                        description = interface.get('description')
                        
                        # 创建接口状态记录
                        interface_status = InterfaceStatus(
                            device_id=device.id,
                            interface_name=interface_name,
                            admin_status=admin_status,
                            operational_status=operational_status,
                            mac_address=mac_address,
                            ip_address=ip_address,
                            speed=speed,
                            description=description
                        )
                        
                        db.add(interface_status)
                
            except Exception as e:
                logger.error(f"收集设备 {device.id} 接口数据失败: {str(e)}")
                continue
        
        # 提交更改
        db.commit()
        logger.info("接口数据收集完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"收集接口数据失败: {str(e)}")

@router.get("/devices", response_model=Dict[str, Any])
def get_topology_devices(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取拓扑图中的设备列表
    
    返回:
        设备列表及其基本信息
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return {"error": "无效的访问令牌"}
        
        # 查询所有设备
        devices = db.query(Device).all()
        
        # 格式化设备信息
        device_list = []
        for device in devices:
            device_info = {
                "id": device.id,
                "name": device.name,
                "management_ip": device.management_ip,
                "vendor": device.vendor,
                "model": device.model,
                "status": device.status,
                "location": device.location,
                "device_type": device.device_type
            }
            device_list.append(device_info)
        
        logger.info(f"用户 {username} 获取拓扑设备列表，共 {len(device_list)} 台设备")
        return {
            "devices": device_list
        }
        
    except Exception as e:
        logger.error(f"获取拓扑设备列表失败: {str(e)}")
        return {
            "error": "获取拓扑设备列表失败",
            "devices": []
        }

@router.get("/links", response_model=Dict[str, Any])
def get_topology_links(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取设备间的连接关系
    
    返回:
        设备连接关系列表
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return {"error": "无效的访问令牌"}
        
        # 检查是否有接口数据，如果没有则在后台收集
        interface_count = db.query(InterfaceStatus).count()
        if interface_count == 0:
            logger.info("未检测到接口数据，将在后台收集...")
            # 在后台执行数据收集任务，不阻塞当前请求
            asyncio.create_task(run_in_thread(collect_interface_data_sync, db))
            # 返回空的连接列表而不是等待数据收集完成
            return {"links": []}
        
        # 查询所有接口状态信息
        interfaces = db.query(InterfaceStatus).all()
        
        # 根据MAC地址建立连接映射
        mac_to_interface = {}  # MAC地址到接口的映射
        device_interfaces = defaultdict(list)  # 设备ID到接口列表的映射
        device_map = {}  # 设备ID到设备对象的映射
        
        # 建立MAC地址与接口的映射关系
        for interface in interfaces:
            # 存储接口信息
            if interface.mac_address:
                mac_to_interface[interface.mac_address] = interface
            device_interfaces[interface.device_id].append(interface)
        
        # 建立设备映射
        devices = db.query(Device).all()
        for device in devices:
            device_map[device.id] = device
        
        # 构建连接关系
        links = []
        processed_pairs = set()  # 避免重复连接
        
        # 方法1: 基于connected_to_mac字段的连接关系
        for interface in interfaces:
            # 只处理有MAC地址和连接信息的接口
            if not interface.mac_address or not interface.connected_to_mac:
                continue
                
            # 查找连接的目标接口
            target_interface = mac_to_interface.get(interface.connected_to_mac)
            if not target_interface:
                continue
                
            # 创建连接对标识，避免重复
            pair_id = tuple(sorted([interface.id, target_interface.id]))
            if pair_id in processed_pairs:
                continue
                
            processed_pairs.add(pair_id)
            
            # 创建连接信息
            link_info = {
                "id": f"{interface.id}-{target_interface.id}",
                "source_device_id": interface.device_id,
                "target_device_id": target_interface.device_id,
                "source_interface": interface.interface_name,
                "target_interface": target_interface.interface_name,
                "status": interface.operational_status if interface.operational_status == target_interface.operational_status else "down",
                "source_ip": interface.ip_address,
                "target_ip": target_interface.ip_address
            }
            links.append(link_info)
        
        # 方法2: 基于MAC地址表的连接关系（补充方法）
        # 通过匹配源接口的MAC地址和目标接口的connected_to_mac字段建立连接
        for interface in interfaces:
            # 只处理有MAC地址的接口
            if not interface.mac_address:
                continue
            
            # 查找哪个接口连接到了当前接口的MAC地址
            target_interfaces = db.query(InterfaceStatus).filter(
                InterfaceStatus.connected_to_mac == interface.mac_address
            ).all()
            
            for target_interface in target_interfaces:
                # 避免自己连接自己
                if target_interface.id == interface.id:
                    continue
                    
                # 创建连接对标识，避免重复
                pair_id = tuple(sorted([interface.id, target_interface.id]))
                if pair_id in processed_pairs:
                    continue
                    
                processed_pairs.add(pair_id)
                
                # 创建连接信息
                link_info = {
                    "id": f"{interface.id}-{target_interface.id}",
                    "source_device_id": interface.device_id,
                    "target_device_id": target_interface.device_id,
                    "source_interface": interface.interface_name,
                    "target_interface": target_interface.interface_name,
                    "status": interface.operational_status if interface.operational_status == target_interface.operational_status else "down",
                    "source_ip": interface.ip_address,
                    "target_ip": target_interface.ip_address
                }
                links.append(link_info)
        
        # 方法3: 基于端口描述的连接关系（补充方法）
        # 遍历所有接口，查找基于描述信息的连接关系
        for interface in interfaces:
            # 检查接口描述中是否包含连接信息
            if interface.description and "TO_" in interface.description.upper():
                # 解析描述信息，查找目标设备
                desc_parts = interface.description.split("_")
                if len(desc_parts) >= 2:
                    target_device_name = desc_parts[1]  # 例如: TO_TuanWei-B 中的 TuanWei-B
                    
                    # 查找目标设备
                    target_device = None
                    for device in devices:
                        # 使用更宽松的匹配方式
                        if target_device_name in device.name or device.name in target_device_name:
                            target_device = device
                            break
                    
                    # 如果找到目标设备，查找对应的接口
                    if target_device:
                        # 查找目标设备的接口，看是否有相互的描述
                        target_interfaces = device_interfaces.get(target_device.id, [])
                        for target_interface in target_interfaces:
                            # 检查目标接口是否指向当前接口所在的设备
                            if (target_interface.description and 
                                "TO_" in target_interface.description.upper()):
                                # 解析目标接口的描述信息
                                target_desc_parts = target_interface.description.split("_")
                                if len(target_desc_parts) >= 2:
                                    source_device_name = target_desc_parts[1]
                                    # 检查是否指向源设备
                                    if (source_device_name in device_map[interface.device_id].name or 
                                        device_map[interface.device_id].name in source_device_name):
                                        
                                        # 创建唯一的连接对标识，避免重复
                                        pair_id = tuple(sorted([interface.id, target_interface.id]))
                                        if pair_id in processed_pairs:
                                            continue
                                            
                                        processed_pairs.add(pair_id)
                                        
                                        # 创建连接信息
                                        link_info = {
                                            "id": f"{interface.id}-{target_interface.id}",
                                            "source_device_id": interface.device_id,
                                            "target_device_id": target_interface.device_id,
                                            "source_interface": interface.interface_name,
                                            "target_interface": target_interface.interface_name,
                                            "status": interface.operational_status if interface.operational_status == target_interface.operational_status else "down",
                                            "source_ip": interface.ip_address,
                                            "target_ip": target_interface.ip_address
                                        }
                                        links.append(link_info)
                                        break
    
        logger.info(f"用户 {username} 获取拓扑连接关系，共 {len(links)} 条连接")
        return {
            "links": links
        }
        
    except Exception as e:
        logger.error(f"获取拓扑连接关系失败: {str(e)}")
        return {
            "error": "获取拓扑连接关系失败",
            "links": []
        }

async def run_in_thread(func, *args):
    """在线程池中运行同步函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)

@router.get("/layout", response_model=Dict[str, Any])
def get_topology_layout(
    token: str = Depends(oauth2_scheme)
):
    """获取拓扑图布局信息
    
    返回:
        拓扑图节点坐标等布局信息
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return {"error": "无效的访问令牌"}
        
        # 返回默认布局（实际应用中可以从数据库或配置文件中读取）
        layout = {
            "nodes": [],  # 节点坐标信息
            "positions": {},  # 节点位置映射
            "groups": []  # 节点分组信息
        }
        
        logger.info(f"用户 {username} 获取拓扑图布局信息")
        return layout
        
    except Exception as e:
        logger.error(f"获取拓扑图布局信息失败: {str(e)}")
        return {
            "error": "获取拓扑图布局信息失败",
            "nodes": [],
            "positions": {},
            "groups": []
        }

@router.post("/layout/save", response_model=Dict[str, Any])
def save_topology_layout(
    layout_data: Dict[str, Any],
    token: str = Depends(oauth2_scheme)
):
    """保存拓扑图布局信息
    
    参数:
        layout_data: 布局数据
    
    返回:
        保存结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return {"error": "无效的访问令牌"}
        
        # 在实际应用中，这里应该将布局信息保存到数据库或文件中
        # 目前只是简单记录日志
        logger.info(f"用户 {username} 保存拓扑图布局信息: {layout_data}")
        
        return {
            "message": "拓扑图布局保存成功"
        }
        
    except Exception as e:
        logger.error(f"保存拓扑图布局信息失败: {str(e)}")
        return {
            "error": "保存拓扑图布局信息失败"
        }

@router.post("/refresh", response_model=Dict[str, Any])
def refresh_topology(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """刷新拓扑图数据
    
    返回:
        刷新结果
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            return {"error": "无效的访问令牌"}
        
        # 异步执行数据收集任务
        asyncio.create_task(run_in_thread(collect_interface_data_sync, db))
        
        logger.info(f"用户 {username} 触发拓扑图数据刷新")
        
        return {
            "message": "拓扑图数据刷新任务已启动",
            "timestamp": "2023-01-01T00:00:00Z"  # 示例时间戳
        }
        
    except Exception as e:
        logger.error(f"刷新拓扑图数据失败: {str(e)}")
        return {
            "error": "刷新拓扑图数据失败"
        }