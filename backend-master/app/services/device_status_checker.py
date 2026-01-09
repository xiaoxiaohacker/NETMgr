import asyncio
import logging
import time
import os  # 添加缺失的os模块导入
from typing import Dict, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.models import Device as DeviceModel, DeviceStatusHistory, DevicePerformance
from app.services.db import get_db, DATABASE_URL, SessionLocal
from app.api.v1.websocket import send_batch_device_status_update, send_device_status_update
import subprocess
import platform
import threading
from datetime import datetime
from app.adapters.snmp import SNMPAdapter
from app.services.adapter_manager import AdapterManager  # 导入AdapterManager替代AdapterFactory
from app.services.encryption import decrypt_device_password
import concurrent.futures

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeviceStatusChecker:
    def __init__(self):
        self.is_running = False
        self.check_interval = 300  # 检查间隔（秒），300秒 = 5分钟，使状态更新更及时

    # 使用全局的SessionLocal，避免重复创建会话工厂
    def ping_host(self, ip: str) -> Dict[str, any]:
        """检查主机连通性，使用多次尝试机制确保准确性"""
        import re
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 根据操作系统选择ping参数
                param = '-n 1' if platform.system().lower() == 'windows' else '-c 1'
                
                if platform.system().lower() == 'windows':
                    # 在Windows上，整个命令作为一个字符串传递
                    command = f'ping {param} {ip}'
                    result = subprocess.run(
                        command,  # 整个命令作为一个字符串
                        shell=True,  # 使用shell执行
                        capture_output=True,
                        text=True,
                        timeout=10,  # 增加超时时间
                        # 设置环境变量确保输出使用UTF-8编码
                        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                    )
                else:
                    # 在Linux/macOS上，参数拆分成列表项
                    command_parts = ['ping', param, ip]
                    result = subprocess.run(
                        command_parts,
                        capture_output=True,
                        text=True,
                        timeout=10  # 增加超时时间
                    )

                # 检查ping是否成功
                is_reachable = False
                if platform.system().lower() == 'windows':
                    # Windows的ping命令输出中包含"来自 xxx.xxx.xxx.xxx 的回复"表示成功
                    is_reachable = "来自" in result.stdout and "的回复" in result.stdout
                    # 也支持英文版Windows
                    if not is_reachable:
                        is_reachable = "Reply from" in result.stdout
                else:
                    # Linux/macOS使用返回码判断
                    is_reachable = result.returncode == 0

                # 尝试提取响应时间
                response_time = None
                if is_reachable:
                    # 匹配Windows和Linux/macOS的ping输出格式
                    if platform.system().lower() == 'windows':
                        # Windows格式: "时间<1ms" 或 "时间=32ms"
                        match = re.search(r'时间[<|=](\d+\.?\d*)ms', result.stdout)
                        # 英文版Windows格式: "time<1ms" or "time=32ms"
                        if not match:
                            match = re.search(r'time[<|=](\d+\.?\d*)ms', result.stdout)
                    else:
                        # Linux/macOS格式: "time=32 ms" or "time=32.456 ms"
                        match = re.search(r'time=(\d+\.?\d*)\s*ms', result.stdout)

                    if match:
                        response_time = float(match.group(1))

                return {
                    "ip": ip,
                    "is_reachable": is_reachable,
                    "response_time": response_time
                }
            except subprocess.TimeoutExpired:
                logger.debug(f"尝试 {attempt + 1}/{max_retries} ping {ip} 超时")
                if attempt == max_retries - 1:  # 如果是最后一次尝试
                    logger.warning(f"经过 {max_retries} 次尝试后，ping {ip} 仍超时")
            except Exception as e:
                logger.error(f"检查主机 {ip} 连通性时出错 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:  # 如果是最后一次尝试
                    logger.warning(f"经过 {max_retries} 次尝试后，检查主机 {ip} 连通性失败")

        # 所有重试都失败，返回不可达
        return {
            "ip": ip,
            "is_reachable": False,
            "response_time": None
        }

    def check_device_connectivity(self, device) -> Dict[str, any]:
        """检查设备连通性，使用多种方法确保准确性"""
        import re

        # 输入参数验证
        if not device or not device.management_ip:
            logger.error(f"无效的设备对象或管理IP为空: {getattr(device, 'name', 'Unknown')}")
            return {
                "is_reachable": False,
                "response_time": None,
                "method": "invalid_device"
            }

        logger.info(f"开始检查设备 {device.name} ({device.management_ip}) 的连通性")

        # 首先尝试ping检测
        ping_result = self.ping_host(device.management_ip)

        # 记录ping结果详情
        if ping_result["is_reachable"]:
            logger.debug(f"设备 {device.management_ip} Ping检测成功，响应时间: {ping_result['response_time']}ms")

            # 如果ping成功，再尝试使用设备凭据连接（根据设备类型）
            try:
                # 解密设备密码
                decrypted_password = decrypt_device_password(device.password)
                decrypted_enable_password = (
                    decrypt_device_password(device.enable_password) 
                    if device.enable_password else None
                )

                # 构建设备连接信息
                device_info = {
                    "management_ip": device.management_ip,
                    "vendor": device.vendor,
                    "username": device.username,
                    "password": decrypted_password,
                    "port": device.port or (22 if device.device_type == "ssh" else 23),
                    "device_type": device.device_type or "ssh",
                    "enable_password": decrypted_enable_password
                }

                # 参数验证
                required_fields = ["management_ip", "username", "password"]
                missing_fields = [field for field in required_fields if not device_info.get(field)]

                if missing_fields:
                    logger.warning(f"设备 {device.name} 缺少必要连接字段: {missing_fields}")

                    # 如果ping成功但缺少凭据，尝试SNMP连接
                    snmp_result = self._try_snmp_connection(device)
                    if snmp_result["is_reachable"]:
                        logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                        return snmp_result
                    else:
                        return {
                            "is_reachable": True,
                            "response_time": ping_result["response_time"],
                            "method": "ping_only_missing_credentials"
                        }

                # 尝试创建适配器并连接
                adapter = AdapterManager.get_adapter(device_info)
                if not adapter:
                    logger.error(f"无法为设备 {device.name} 创建适配器，设备类型: {device.device_type}")

                    # 如果ping成功但无法创建适配器，尝试SNMP连接
                    snmp_result = self._try_snmp_connection(device)
                    if snmp_result["is_reachable"]:
                        logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                        return snmp_result
                    else:
                        return {
                            "is_reachable": True,
                            "response_time": ping_result["response_time"],
                            "method": "ping_only_adapter_creation_failed"
                        }

                connect_start_time = time.time()
                if adapter.connect():
                    connect_duration = time.time() - connect_start_time
                    logger.info(f"设备 {device.name} ({device.management_ip}) 凭据验证成功，连接耗时: {connect_duration:.2f}秒")

                    # 连接成功后立即断开
                    try:
                        adapter.disconnect()
                        logger.debug(f"设备 {device.name} 连接会话已正常断开")
                    except Exception as e:
                        logger.warning(f"断开设备 {device.name} 连接时出现异常: {str(e)}")

                    return {
                        "is_reachable": True,
                        "response_time": ping_result["response_time"],
                        "method": "credentials",
                        "connection_time": connect_duration
                    }
                else:
                    connect_duration = time.time() - connect_start_time
                    logger.warning(f"设备 {device.name} ({device.management_ip}) 凭据验证失败，连接耗时: {connect_duration:.2f}秒")

                    # 如果凭据验证失败，尝试SNMP连接
                    snmp_result = self._try_snmp_connection(device)
                    if snmp_result["is_reachable"]:
                        logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                        return snmp_result
                    else:
                        return {
                            "is_reachable": True,
                            "response_time": ping_result["response_time"],
                            "method": "ping_only_credentials_failed"
                        }
            except ConnectionRefusedError as e:
                logger.error(f"设备 {device.name} ({device.management_ip}) 连接被拒绝: {str(e)}")

                # 如果连接被拒绝，尝试SNMP连接
                snmp_result = self._try_snmp_connection(device)
                if snmp_result["is_reachable"]:
                    logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                    return snmp_result
                else:
                    return {
                        "is_reachable": True,
                        "response_time": ping_result["response_time"],
                        "method": "ping_only_connection_refused"
                    }
            except TimeoutError as e:
                logger.error(f"设备 {device.name} ({device.management_ip}) 连接超时: {str(e)}")

                # 如果连接超时，尝试SNMP连接
                snmp_result = self._try_snmp_connection(device)
                if snmp_result["is_reachable"]:
                    logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                    return snmp_result
                else:
                    return {
                        "is_reachable": True,
                        "response_time": ping_result["response_time"],
                        "method": "ping_only_timeout"
                    }
            except PermissionError as e:
                logger.error(f"设备 {device.name} ({device.management_ip}) 权限不足: {str(e)}")

                # 如果权限不足，尝试SNMP连接
                snmp_result = self._try_snmp_connection(device)
                if snmp_result["is_reachable"]:
                    logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                    return snmp_result
                else:
                    return {
                        "is_reachable": True,
                        "response_time": ping_result["response_time"],
                        "method": "ping_only_permission_denied"
                    }
            except Exception as e:
                logger.exception(f"检查设备 {device.name} ({device.management_ip}) 连通性时发生未预期的异常")

                # 如果出现异常，尝试SNMP连接
                snmp_result = self._try_snmp_connection(device)
                if snmp_result["is_reachable"]:
                    logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                    return snmp_result
                else:
                    return {
                        "is_reachable": True,
                        "response_time": ping_result["response_time"],
                        "method": "ping_only_unexpected_error",
                        "error": str(e)
                    }
        else:
            # ping失败，尝试SNMP连接作为备选方案
            logger.warning(f"设备 {device.name} ({device.management_ip}) Ping检测失败，尝试SNMP连接...")
            snmp_result = self._try_snmp_connection(device)
            if snmp_result["is_reachable"]:
                logger.info(f"设备 {device.name} 通过SNMP连接验证可达")
                return snmp_result
            else:
                # ping和SNMP都失败，设备不可达
                logger.warning(f"设备 {device.name} ({device.management_ip}) Ping和SNMP检测都失败")
                return {
                    "is_reachable": False,
                    "response_time": None,
                    "method": "unreachable_ping_and_snmp_failed"
                }

    def _try_snmp_connection(self, device):
        """尝试通过SNMP连接验证设备是否在线"""
        try:
            # 构建设备信息用于SNMP连接
            device_info = {
                'management_ip': device.management_ip,
                'snmp_community': device.snmp_community or 'public',  # 从设备表获取SNMP配置，如果不存在则使用默认值
                'snmp_version': device.snmp_version or 2,
                'snmp_port': device.snmp_port or 161
            }

            # 尝试通过SNMP获取基本系统信息
            adapter = SNMPAdapter(device_info)

            # 尝试连接设备
            if adapter.connect():
                # 获取系统信息验证连接
                sys_info = adapter.get_device_info()
                adapter.disconnect()

                if sys_info:
                    logger.debug(f"设备 {device.management_ip} SNMP连接成功，获取到系统信息")
                    return {
                        "is_reachable": True,
                        "response_time": None,  # SNMP连接不记录ping响应时间
                        "method": "snmp"
                    }
                else:
                    logger.debug(f"设备 {device.management_ip} SNMP连接成功，但无法获取系统信息")
                    return {
                        "is_reachable": True,
                        "response_time": None,
                        "method": "snmp_no_sysinfo"
                    }
            else:
                logger.debug(f"设备 {device.management_ip} SNMP连接失败")
                return {
                    "is_reachable": False,
                    "response_time": None,
                    "method": "snmp_failed"
                }
        except Exception as e:
            logger.debug(f"设备 {device.management_ip} SNMP连接异常: {str(e)}")
            return {
                "is_reachable": False,
                "response_time": None,
                "method": "snmp_exception"
            }

    def get_device_performance(self, device):
        """获取设备性能数据，包括CPU、内存使用率等"""
        try:
            # 构建设备信息用于SNMP连接
            device_info = {
                'management_ip': device.management_ip,
                'snmp_community': device.snmp_community or 'public',
                'snmp_version': device.snmp_version or 2,
                'snmp_port': device.snmp_port or 161
            }

            # 尝试通过SNMP获取性能数据
            adapter = SNMPAdapter(device_info)

            cpu_usage = None
            memory_usage = None
            
            # 尝试获取CPU使用率 - 根据厂商使用不同OID
            if device.vendor and device.vendor.lower() == 'cisco':
                # Cisco CPU OID
                cpu_oid = '.1.3.6.1.4.1.9.9.109.1.1.1.1.7.0'
                cpu_result = adapter.get_snmp_value(cpu_oid)
                if cpu_result and cpu_result.isdigit():
                    cpu_usage = int(cpu_result)
                else:
                    # 如果Cisco专用OID失败，尝试通用OID
                    cpu_result = adapter.get_snmp_value(adapter.HOST_RESOURCES_CPULOAD1)
                    if cpu_result and cpu_result.isdigit():
                        cpu_usage = int(cpu_result)
            elif device.vendor and device.vendor.lower() == 'huawei':
                # Huawei CPU OID
                cpu_oid = '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5.0'
                cpu_result = adapter.get_snmp_value(cpu_oid)
                if cpu_result and cpu_result.isdigit():
                    cpu_usage = int(cpu_result)
                else:
                    # 如果Huawei专用OID失败，尝试通用OID
                    cpu_result = adapter.get_snmp_value(adapter.HOST_RESOURCES_CPULOAD1)
                    if cpu_result and cpu_result.isdigit():
                        cpu_usage = int(cpu_result)
            else:
                # 尝试标准CPU OID
                cpu_result = adapter.get_snmp_value(adapter.HOST_RESOURCES_CPULOAD1)
                if cpu_result and cpu_result.isdigit():
                    cpu_usage = int(cpu_result)

            # 获取内存使用率
            total_mem_result = adapter.get_snmp_value(adapter.HOST_RESOURCES_MEM_TOTAL)
            used_mem_result = adapter.get_snmp_value(adapter.HOST_RESOURCES_MEM_USED)

            if total_mem_result and used_mem_result:
                try:
                    total_mem = int(total_mem_result)
                    used_mem = int(used_mem_result)
                    if total_mem > 0:
                        memory_usage = int((used_mem / total_mem) * 100)
                except ValueError:
                    pass

            # 获取接口流量信息
            interfaces = adapter.get_interfaces()
            inbound_bandwidth = 0
            outbound_bandwidth = 0

            if interfaces:
                # 取第一个接口的流量信息
                first_interface = interfaces[0]
                inbound_octets = first_interface.get('in_octets', 0)
                outbound_octets = first_interface.get('out_octets', 0)

                inbound_bandwidth = int(inbound_octets) if inbound_octets else 0
                outbound_bandwidth = int(outbound_octets) if outbound_octets else 0

            # 返回性能数据
            return {
                'cpu_usage': cpu_usage if cpu_usage is not None else 0,
                'memory_usage': memory_usage if memory_usage is not None else 0,
                'inbound_bandwidth': inbound_bandwidth,
                'outbound_bandwidth': outbound_bandwidth
            }
            
        except Exception as e:
            logger.error(f"获取设备性能数据失败 {device.management_ip}: {str(e)}")
            # 返回默认值
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'inbound_bandwidth': 0,
                'outbound_bandwidth': 0
            }

    def start(self):
        """启动设备状态检查器"""
        if self.is_running:
            logger.warning("设备状态检查器已在运行中")
            return

        self.is_running = True
        logger.info(f"启动设备状态检查器，检查间隔: {self.check_interval}秒")

        # 在新线程中运行检查任务
        thread = threading.Thread(target=self._checking_loop, daemon=True)
        thread.start()

    def stop(self):
        """停止设备状态检查器"""
        self.is_running = False
        logger.info("设备状态检查器已停止")

    def _checking_loop(self):
        """运行检查循环"""
        logger.info(f"设备状态检查循环已启动，检查间隔: {self.check_interval}秒")
        while self.is_running:
            try:
                logger.debug("开始执行设备状态检查...")
                start_time = time.time()
                self._check_all_devices()
                elapsed_time = time.time() - start_time
                logger.debug(f"设备状态检查完成，耗时: {elapsed_time:.2f}秒")
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"设备状态检查循环出错: {e}")
                time.sleep(self.check_interval)

    def _check_all_devices(self):
        """检查所有设备的状态"""
        # 使用独立的数据库会话
        db = SessionLocal()
        start_time = time.time()
        try:
            logger.info("开始批量检查所有设备状态...")
            devices = db.query(DeviceModel).all()
            if not devices:
                logger.warning("数据库中未找到任何设备")
                return

            status_changes = []
            check_results = {
                'total': len(devices),
                'checked': 0,
                'online': 0,
                'offline': 0,
                'errors': 0,
                'methods': {}
            }

            logger.info(f"共找到 {check_results['total']} 个设备需要检查")

            # 使用线程池并发检查设备状态
            max_workers = min(10, len(devices))  # 最大并发数不超过10或设备总数
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有设备检查任务
                future_to_device = {
                    executor.submit(self.check_device_connectivity, device): device 
                    for device in devices
                }
                
                # 收集检查结果
                for future in concurrent.futures.as_completed(future_to_device):
                    device = future_to_device[future]
                    try:
                        result = future.result()
                        method = result["method"]

                        # 统计检测方法使用次数
                        check_results['methods'][method] = check_results['methods'].get(method, 0) + 1

                        # 根据检测结果确定设备状态
                        new_status = "online" if result["is_reachable"] else "offline"
                        if result["is_reachable"]:
                            check_results['online'] += 1
                        else:
                            check_results['offline'] += 1
                        check_results['checked'] += 1

                        # 检查状态是否发生变化
                        if device.status != new_status:
                            old_status = device.status or "unknown"
                            logger.info(f"设备 {device.name} ({device.management_ip}) 状态从 '{old_status}' 变为 '{new_status}'")

                            # 更新数据库中的设备状态
                            device.status = new_status
                            db.add(device)

                            # 记录状态变化，稍后发送WebSocket通知
                            status_changes.append({
                                'device_id': device.id,
                                'status': new_status,
                                'message': f"设备 {device.name} 状态更新为 {new_status}",
                                'name': device.name,
                                'previous_status': old_status,
                                'response_time': result.get('response_time'),
                                'method': method
                            })
                        else:
                            logger.debug(f"设备 {device.name} ({device.management_ip}) 状态未变: {device.status}")

                        # 记录详细的检测结果
                        logger.info(f"设备 {device.name} 检测完成 - "
                                  f"可达性: {result['is_reachable']}, "
                                  f"响应时间: {result.get('response_time', 'N/A')}ms, "
                                  f"检测方法: {method}")

                    except Exception as device_error:
                        check_results['errors'] += 1
                        logger.exception(f"检查单个设备 {getattr(device, 'name', 'Unknown')} 时发生异常: {device_error}")
                        continue

            # 提交数据库更改
            db.commit()
            
            # 记录设备状态到历史表
            online_count = db.query(DeviceModel).filter(DeviceModel.status == "online").count()
            offline_count = db.query(DeviceModel).filter(DeviceModel.status == "offline").count()
            warning_count = db.query(DeviceModel).filter(DeviceModel.status == "warning").count()
            unknown_count = db.query(DeviceModel).filter(DeviceModel.status == "unknown").count()
            
            # 创建状态历史记录
            status_history = DeviceStatusHistory(
                timestamp=datetime.now(),
                online_count=online_count,
                offline_count=offline_count,
                warning_count=warning_count,
                unknown_count=unknown_count
            )
            db.add(status_history)
            
            # 为每个设备收集并存储性能数据
            for device in devices:
                if not device.management_ip:  # 即使离线设备也要尝试收集性能数据
                    continue
                
                # 检查设备是否在线，如果在线则收集性能数据
                is_device_online = device.status == "online"
                
                if is_device_online:
                    performance_data = self.get_device_performance(device)
                    
                    # 创建性能记录
                    perf_record = DevicePerformance(
                        device_id=device.id,
                        cpu_usage=performance_data['cpu_usage'],
                        memory_usage=performance_data['memory_usage'],
                        inbound_bandwidth=performance_data['inbound_bandwidth'],
                        outbound_bandwidth=performance_data['outbound_bandwidth']
                    )
                    db.add(perf_record)
                    
                    # 检查性能阈值并触发告警
                    self._check_performance_thresholds(device, performance_data)
                else:
                    # 设备离线，记录0值性能数据
                    perf_record = DevicePerformance(
                        device_id=device.id,
                        cpu_usage=0,
                        memory_usage=0,
                        inbound_bandwidth=0,
                        outbound_bandwidth=0
                    )
                    db.add(perf_record)
            
            db.commit()
            execution_time = time.time() - start_time
            logger.info(f"设备状态检查完成，总执行时间: {execution_time:.2f}秒")
            logger.info(f"检查统计 - 总数: {check_results['total']}, "
                       f"已检查: {check_results['checked']}, "
                       f"在线: {check_results['online']}, "
                       f"离线: {check_results['offline']}, "
                       f"错误: {check_results['errors']}")
            logger.info(f"检测方法分布: {check_results['methods']}")

            # 发送WebSocket通知
            if status_changes:
                logger.info(f"准备发送 {len(status_changes)} 个设备状态更新通知")

                # 为每个状态变更发送独立的WebSocket通知
                for update in status_changes:
                    try:
                        # 创建新线程发送WebSocket通知，避免阻塞
                        import asyncio
                        from threading import Thread

                        def run_async_func(device_id, status, message, previous_status=None):
                            # 创建新的事件循环
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(send_device_status_update(
                                device_id, status, message
                            ))

                        thread = Thread(
                            target=run_async_func,
                            args=(update['device_id'], update['status'], update['message'], update.get('previous_status'))
                        )
                        thread.start()
                        logger.debug(f"已启动线程发送设备 {update['name']} 的状态更新通知")
                    except Exception as notify_error:
                        logger.error(f"发送WebSocket通知失败: {notify_error}")

            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="INFO",
                    module="MONITOR",
                    message=f"设备状态检查任务完成，总数: {check_results['total']}, 在线: {check_results['online']}, 离线: {check_results['offline']}, 状态变化: {len(status_changes)}, 耗时: {execution_time:.2f}秒",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")

        except Exception as e:
            logger.exception(f"检查所有设备状态时出错: {e}")
            db.rollback()
            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="ERROR",
                    module="MONITOR",
                    message=f"设备状态检查任务执行失败: {str(e)}",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")
            raise
        finally:
            db.close()
            logger.debug("数据库会话已关闭")

    def _check_performance_thresholds(self, device, performance_data):
        """检查设备性能阈值并触发告警"""
        try:
            # 定义性能阈值（可从配置文件中读取）
            CPU_THRESHOLD = 80  # CPU使用率阈值
            MEMORY_THRESHOLD = 85  # 内存使用率阈值
            
            # 检查CPU使用率
            if performance_data['cpu_usage'] is not None and performance_data['cpu_usage'] > CPU_THRESHOLD:
                self._create_performance_alert(
                    device=device,
                    alert_type="high_cpu",
                    message=f"设备 {device.name} CPU使用率过高: {performance_data['cpu_usage']}%"
                )
            
            # 检查内存使用率
            if performance_data['memory_usage'] is not None and performance_data['memory_usage'] > MEMORY_THRESHOLD:
                self._create_performance_alert(
                    device=device,
                    alert_type="high_memory", 
                    message=f"设备 {device.name} 内存使用率过高: {performance_data['memory_usage']}%"
                )
                
        except Exception as e:
            logger.error(f"检查性能阈值时出错 {device.management_ip}: {str(e)}")

    def _create_performance_alert(self, device, alert_type, message):
        """创建性能告警"""
        try:
            from app.services.db import SessionLocal
            from app.services.models import Alert
            from datetime import datetime
            
            db = SessionLocal()
            try:
                # 创建告警记录
                alert = Alert(
                    device_id=device.id,
                    device_name=device.name,
                    alert_type=alert_type,
                    message=message,
                    severity="high",  # 可以根据阈值超过程度设置不同级别
                    status="active",
                    created_at=datetime.now(),
                    acknowledged_at=None,
                    acknowledged_by=None
                )
                
                db.add(alert)
                db.commit()
                
                logger.info(f"创建性能告警: {message}")
                
                # 发送WebSocket通知（如果系统中有WebSocket连接）
                # 这里可以扩展发送通知到前端
                from app.main import send_alert_notification
                send_alert_notification(alert)
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"创建性能告警失败 {device.management_ip}: {str(e)}")

# 全局设备状态检查器实例
device_status_checker = DeviceStatusChecker()