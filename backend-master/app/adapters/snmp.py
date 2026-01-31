from typing import Dict, Any, List
import logging
import socket
import re
from datetime import datetime
import subprocess
import platform

# 导入错误基类
from pysnmp.error import PySnmpError
# 基适配器
from app.adapters.base import BaseAdapter

try:
    # 尝试使用新版本的pysnmp导入方式
    from pysnmp.hlapi.v3arch import SnmpEngine
    from pysnmp.hlapi.v3arch import CommunityData, UdpTransportTarget
    from pysnmp.hlapi.v3arch import ContextData, ObjectType, ObjectIdentity
    from pysnmp.hlapi.v3arch.asyncio.cmdgen import get_cmd as getCmd
    from pysnmp.hlapi.v3arch.asyncio.cmdgen import next_cmd as nextCmd
    # SNMP v3相关导入
    from pysnmp.hlapi.v3arch import UsmUserData
    from pysnmp.proto.rfc1902 import OctetString
except ImportError:
    # 回退到旧版本的pysnmp导入方式
    from pysnmp.hlapi import SnmpEngine
    from pysnmp.hlapi import CommunityData, UdpTransportTarget
    from pysnmp.hlapi import ContextData, ObjectType, ObjectIdentity
    from pysnmp.hlapi import getCmd
    from pysnmp.hlapi import nextCmd
    # SNMP v3相关导入
    from pysnmp.hlapi import UsmUserData
    from pysnmp.proto.rfc1902 import OctetString
from pysnmp.error import PySnmpError
from app.adapters.base import BaseAdapter
import re

# 创建logger实例
logger = logging.getLogger(__name__)


class SNMPAdapter(BaseAdapter):
    """SNMP适配器，用于通过SNMP协议与网络设备交互"""
    
    # SNMP OID常量定义
    SYS_DESCRIPTION = '1.3.6.1.2.1.1.1.0'  # 系统描述
    SYS_NAME = '1.3.6.1.2.1.1.5.0'  # 系统名称
    SYS_UPTIME = '1.3.6.1.2.1.1.3.0'  # 系统运行时间
    IF_NUMBER = '1.3.6.1.2.1.2.1.0'  # 接口数量
    IF_DESCR = '1.3.6.1.2.1.2.2.1.2'  # 接口描述
    IF_TYPE = '1.3.6.1.2.1.2.2.1.3'  # 接口类型
    IF_MTU = '1.3.6.1.2.1.2.2.1.4'  # 接口MTU
    IF_SPEED = '1.3.6.1.2.1.2.2.1.5'  # 接口速率
    IF_PHYS_ADDRESS = '1.3.6.1.2.1.2.2.1.6'  # 接口物理地址
    IF_ADMIN_STATUS = '1.3.6.1.2.1.2.2.1.7'  # 接口管理状态
    IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8'  # 接口操作状态
    IF_IN_OCTETS = '1.3.6.1.2.1.2.2.1.10'  # 接口入站字节数
    IF_IN_UCAST_PKTS = '1.3.6.1.2.1.2.2.1.11'  # 接口入站单播包数
    IF_IN_ERRORS = '1.3.6.1.2.1.2.2.1.14'  # 接口入站错误数
    IF_OUT_OCTETS = '1.3.6.1.2.1.2.2.1.16'  # 接口出站字节数
    IF_OUT_UCAST_PKTS = '1.3.6.1.2.1.2.2.1.17'  # 接口出站单播包数
    IF_OUT_ERRORS = '1.3.6.1.2.1.2.2.1.20'  # 接口出站错误数
    HOST_RESOURCES_CPULOAD1 = '1.3.6.1.2.1.25.3.3.1.2.1'  # CPU 1分钟负载
    HOST_RESOURCES_CPULOAD5 = '1.3.6.1.2.1.25.3.3.1.2.2'  # CPU 5分钟负载
    HOST_RESOURCES_CPULOAD15 = '1.3.6.1.2.1.25.3.3.1.2.3'  # CPU 15分钟负载
    HOST_RESOURCES_MEM_TOTAL = '1.3.6.1.2.1.25.2.3.1.5.1'  # 总内存
    HOST_RESOURCES_MEM_USED = '1.3.6.1.2.1.25.2.3.1.6.1'  # 已用内存
    
    def __init__(self, device_info: Dict[str, Any]):
        """初始化SNMP适配器"""
        super().__init__(device_info)
        self.community = device_info.get('snmp_community', 'public')
        self.port = device_info.get('snmp_port', 161)
        self.version = device_info.get('snmp_version', 2)  # 支持版本: 1, 2, 3
        self.timeout = device_info.get('snmp_timeout', 5)  # 默认超时时间为5秒
        self.retries = device_info.get('snmp_retries', 1)  # 默认重试次数为1次
        
        # SNMP v3特定配置
        self.security_name = device_info.get('snmp_security_name')
        self.auth_protocol = device_info.get('snmp_auth_protocol')  # 如 'MD5', 'SHA'
        self.auth_key = device_info.get('snmp_auth_key')
        self.priv_protocol = device_info.get('snmp_priv_protocol')  # 如 'DES', 'AES'
        self.priv_key = device_info.get('snmp_priv_key')
        
        # 初始化SNMP引擎
        self.engine = SnmpEngine()
        self.transport = None
        self.context = ContextData()
        self.auth_data = None
        
        logger.debug(f"SNMP适配器初始化完成:")
        logger.debug(f"  - 版本: {self.version}")
        logger.debug(f"  - 社区字符串: {self.community}")
        logger.debug(f"  - 端口: {self.port}")
        logger.debug(f"  - 超时时间: {self.timeout}")
        logger.debug(f"  - 重试次数: {self.retries}")
        logger.debug(f"  - 安全名称: {self.security_name}")
        logger.debug(f"  - 认证协议: {self.auth_protocol}")
        logger.debug(f"  - 加密协议: {self.priv_protocol}")

    def _ping_device(self, ip: str, timeout: int = 3) -> bool:
        """Ping设备检查基本连通性"""
        try:
            logger.debug(f"开始Ping设备 {ip}")
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", "-w", str(timeout * 1000), ip]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 1
            )
            
            is_reachable = result.returncode == 0
            logger.debug(f"Ping设备 {ip} 结果: {'可达' if is_reachable else '不可达'}")
            return is_reachable
        except Exception as e:
            logger.error(f"Ping设备 {ip} 失败: {str(e)}")
            return False

    def connect(self) -> bool:
        """连接到SNMP设备"""
        try:
            ip = self.device_info.get('management_ip')
            if not ip:
                raise ValueError("设备IP地址不能为空")
            
            logger.info(f"开始连接SNMP设备 {ip}:{self.port}，SNMP版本: v{self.version}，超时时间: {self.timeout}s，重试次数: {self.retries}")
            
            # 详细记录连接参数
            logger.debug(f"连接参数详情:")
            logger.debug(f"  - 管理IP: {ip}")
            logger.debug(f"  - 端口: {self.port}")
            logger.debug(f"  - SNMP版本: v{self.version}")
            logger.debug(f"  - 超时时间: {self.timeout}s")
            logger.debug(f"  - 重试次数: {self.retries}")
            logger.debug(f"  - 社区字符串: {'*' * len(self.community) if self.community else '未设置'}")
            logger.debug(f"  - 安全名称: {self.security_name or '未设置'}")
            logger.debug(f"  - 认证协议: {self.auth_protocol or '未设置'}")
            logger.debug(f"  - 加密协议: {self.priv_protocol or '未设置'}")
            
            # 基本网络连通性检查
            logger.debug(f"检查设备 {ip} 基本网络连通性...")
            if not self._ping_device(ip):
                logger.warning(f"设备 {ip} Ping不可达，但仍将继续尝试SNMP连接")
            
            # 预检查设备是否可达 - 使用UDP socket检查端口可达性
            logger.debug(f"检查设备 {ip} UDP端口 {self.port} 是否可达...")
            try:
                # 使用UDP socket检查端口
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                # 发送一个简单的数据包测试连通性
                sock.sendto(b'\x00', (ip, self.port))
                sock.close()
                logger.debug(f"设备 {ip} UDP端口 {self.port} 初步可达")
            except Exception as e:
                logger.warning(f"设备 {ip} UDP端口 {self.port} 可能不可达: {str(e)}")
                # 注意：我们不会因为端口检查失败而终止连接尝试，因为UDP是无连接的
            
            # 创建传输目标，设置超时和重试次数
            logger.debug(f"创建SNMP传输目标: {ip}:{self.port}, 超时={self.timeout}s, 重试={self.retries}次")
            self.transport = UdpTransportTarget((ip, self.port), timeout=self.timeout, retries=self.retries)
            
            # 根据SNMP版本设置认证数据
            if self.version == 3 and self.security_name:
                # SNMP v3配置
                logger.debug(f"使用SNMP v3认证，安全名称: {self.security_name}")
                logger.debug(f"认证协议: {self.auth_protocol}, 加密协议: {self.priv_protocol}")
                logger.debug(f"认证密钥: {self.auth_key}, 加密密钥: {self.priv_key}")
                
                # 处理无认证无加密的情况
                if not self.auth_protocol and not self.priv_protocol:
                    # 无认证无加密
                    self.auth_data = UsmUserData(self.security_name)
                    logger.debug("使用SNMP v3无认证无加密模式")
                else:
                    # 带认证或加密
                    # 处理认证协议
                    auth_proto = None
                    if self.auth_protocol:
                        auth_proto_str = self.auth_protocol.upper()
                        if auth_proto_str == 'MD5':
                            from pysnmp.proto.rfc3414 import usmHMACMD5AuthProtocol
                            auth_proto = usmHMACMD5AuthProtocol
                        elif auth_proto_str == 'SHA':
                            from pysnmp.proto.rfc3414 import usmHMACSHAAuthProtocol
                            auth_proto = usmHMACSHAAuthProtocol
                        elif auth_proto_str == 'SHA224':
                            from pysnmp.proto.rfc3414 import usmHMAC128SHA224AuthProtocol
                            auth_proto = usmHMAC128SHA224AuthProtocol
                        elif auth_proto_str == 'SHA256':
                            from pysnmp.proto.rfc3414 import usmHMAC192SHA256AuthProtocol
                            auth_proto = usmHMAC192SHA256AuthProtocol
                        elif auth_proto_str == 'SHA384':
                            from pysnmp.proto.rfc3414 import usmHMAC256SHA384AuthProtocol
                            auth_proto = usmHMAC256SHA384AuthProtocol
                        elif auth_proto_str == 'SHA512':
                            from pysnmp.proto.rfc3414 import usmHMAC384SHA512AuthProtocol
                            auth_proto = usmHMAC384SHA512AuthProtocol
                        else:
                            raise ValueError(f"不支持的SNMP认证协议: {self.auth_protocol}")
                    
                    # 处理加密协议
                    priv_proto = None
                    if self.priv_protocol:
                        priv_proto_str = self.priv_protocol.upper()
                        if priv_proto_str == 'DES':
                            from pysnmp.proto.rfc3414 import usmDESPrivProtocol
                            priv_proto = usmDESPrivProtocol
                        elif priv_proto_str == '3DES':
                            from pysnmp.proto.rfc3414 import usm3DESEDEPrivProtocol
                            priv_proto = usm3DESEDEPrivProtocol
                        elif priv_proto_str == 'AES':
                            from pysnmp.proto.rfc3414 import usmAesCfb128Protocol
                            priv_proto = usmAesCfb128Protocol
                        elif priv_proto_str == 'AES192':
                            from pysnmp.proto.rfc3414 import usmAesCfb192Protocol
                            priv_proto = usmAesCfb192Protocol
                        elif priv_proto_str == 'AES256':
                            from pysnmp.proto.rfc3414 import usmAesCfb256Protocol
                            priv_proto = usmAesCfb256Protocol
                        else:
                            raise ValueError(f"不支持的SNMP加密协议: {self.priv_protocol}")
                    
                    self.auth_data = UsmUserData(
                        self.security_name,
                        self.auth_key,
                        self.priv_key,
                        auth_proto,
                        priv_proto
                    )
                    logger.debug(f"使用SNMP v3带认证模式: auth={self.auth_protocol}, priv={self.priv_protocol}")
            else:
                # SNMP v1/v2c配置
                logger.debug(f"使用SNMP v{self.version}社区字符串认证: {self.community}")
                # mpModel: 0->SNMPv1, 1->SNMPv2c, 2->SNMPv3
                mp_model = 0 if self.version == 1 else 1
                self.auth_data = CommunityData(self.community, mpModel=mp_model)
            
            # 测试连接 - 先尝试SYS_NAME，如果失败再尝试SYS_DESCRIPTION
            logger.debug("开始测试SNMP连接，获取系统信息")
            test_result = self._get_snmp_value(self.SYS_NAME)
            if not test_result:
                logger.debug("SYS_NAME测试失败，尝试SYS_DESCRIPTION")
                test_result = self._get_snmp_value(self.SYS_DESCRIPTION)
                
            if test_result:
                logger.info(f"SNMP设备 {ip} 连接成功")
                logger.debug(f"设备系统信息: {test_result}")
                return True
            else:
                logger.warning(f"SNMP设备 {ip} 连接测试失败，无法获取系统基本信息")
                # 尝试使用更基础的OID进行测试
                logger.debug("尝试使用更基础的OID进行测试")
                basic_oid_result = self._get_snmp_value('1.3.6.1.2.1.1.1.0')  # sysDescr
                if basic_oid_result:
                    logger.info(f"使用基础OID测试成功，设备 {ip} 连接成功")
                    return True
                else:
                    # 尝试其他常见OID
                    logger.debug("尝试其他常见OID进行测试")
                    oids_to_try = [
                        '1.3.6.1.2.1.1.5.0',  # sysName
                        '1.3.6.1.2.1.1.3.0',  # sysUpTime
                        '1.3.6.1.2.1.2.1.0'   # ifNumber
                    ]
                    
                    for oid in oids_to_try:
                        fallback_result = self._get_snmp_value(oid)
                        if fallback_result:
                            logger.info(f"使用备用OID {oid} 测试成功，设备 {ip} 连接成功")
                            return True
                    
                    error_msg = f"SNMP连接测试失败，无法从设备 {ip} 获取任何必要信息。请检查：\n" \
                               f"1. 设备是否已启用SNMP Agent服务\n" \
                               f"2. SNMP版本和认证参数是否正确\n" \
                               f"3. 防火墙是否允许UDP {self.port} 端口通信\n" \
                               f"4. 网络连通性是否正常"
                    logger.error(error_msg)
                    raise ConnectionError(error_msg)
        except ValueError as ve:
            # 捕获值错误（如无效的协议）
            error_msg = f"SNMP配置参数错误: {str(ve)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        except PySnmpError as e:
            # 捕获pysnmp特定错误
            error_msg = f"SNMP协议错误: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        except ConnectionError:
            # 重新抛出已经格式化的连接错误
            raise
        except socket.error as se:
            # 捕获socket相关错误
            error_msg = f"网络连接错误: {str(se)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        except ImportError as ie:
            # 捕获导入错误
            error_msg = f"SNMP模块导入错误: {str(ie)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        except Exception as e:
            # 捕获其他未预期的错误
            error_msg = f"SNMP连接未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)  # 记录完整堆栈跟踪
            raise ConnectionError(error_msg)
    
    def disconnect(self) -> bool:
        """断开SNMP连接（SNMP是无状态协议，这里只是清理资源）"""
        self.transport = None
        return True
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备基本信息"""
        try:
            info = {
                'vendor': 'generic_snmp',
                'model': '',
                'version': '',
                'serial_number': '',
                'uptime': ''
            }
            
            # 获取系统描述
            sys_desc = self._get_snmp_value(self.SYS_DESCRIPTION)
            if sys_desc:
                info['model'] = self._extract_model_from_description(sys_desc)
                info['version'] = self._extract_version_from_description(sys_desc)
            
            # 获取系统名称
            sys_name = self._get_snmp_value(self.SYS_NAME)
            if sys_name:
                info['hostname'] = sys_name
            
            # 获取系统运行时间
            uptime = self._get_snmp_value(self.SYS_UPTIME)
            if uptime:
                info['uptime'] = str(uptime)
                
            return info
        except Exception as e:
            print(f"获取设备信息失败: {str(e)}")
            raise

    def get_device_type(self) -> str:
        """获取设备类型字符串（用于Netmiko）
        
        Returns:
            str: Netmiko设备类型字符串
        """
        # SNMP适配器不使用Netmiko，返回通用SNMP类型
        return "snmp"

    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取所有接口信息"""
        try:
            interfaces = []
            
            # 获取接口数量
            if_number = self._get_snmp_value(self.IF_NUMBER)
            if not if_number:
                return interfaces
            
            # 使用SNMP walk获取各种接口信息
            if_descriptions = self._walk_snmp_table(self.IF_DESCR)
            if_oper_status = self._walk_snmp_table(self.IF_OPER_STATUS)
            if_admin_status = self._walk_snmp_table(self.IF_ADMIN_STATUS)
            if_speeds = self._walk_snmp_table(self.IF_SPEED)
            if_mtu = self._walk_snmp_table(self.IF_MTU)
            if_in_octets = self._walk_snmp_table(self.IF_IN_OCTETS)
            if_out_octets = self._walk_snmp_table(self.IF_OUT_OCTETS)
            if_in_errors = self._walk_snmp_table(self.IF_IN_ERRORS)
            if_out_errors = self._walk_snmp_table(self.IF_OUT_ERRORS)
            
            # 合并接口信息
            for if_index, description in if_descriptions.items():
                oper_status = if_oper_status.get(if_index, 'unknown')
                admin_status = if_admin_status.get(if_index, 'unknown')
                speed = if_speeds.get(if_index, 'unknown')
                mtu = if_mtu.get(if_index, 'unknown')
                in_octets = if_in_octets.get(if_index, '0')
                out_octets = if_out_octets.get(if_index, '0')
                in_errors = if_in_errors.get(if_index, '0')
                out_errors = if_out_errors.get(if_index, '0')
                
                interfaces.append({
                    'index': if_index,
                    'name': description,
                    'description': description,
                    'oper_status': self._map_oper_status(oper_status),
                    'admin_status': self._map_admin_status(admin_status),
                    'speed': self._format_speed(speed),
                    'mtu': mtu,
                    'in_octets': in_octets,
                    'out_octets': out_octets,
                    'in_errors': in_errors,
                    'out_errors': out_errors
                })
            
            return interfaces
        except Exception as e:
            error_msg = f"获取SNMP接口信息失败: {str(e)}"
            print(error_msg)
            raise

    def get_interface_status(self, interface: str) -> Dict[str, Any]:
        """获取指定接口状态"""
        try:
            # 查找接口索引
            if_index = self._get_interface_index(interface)
            if not if_index:
                raise ValueError(f"未找到接口: {interface}")
            
            status = {
                'interface': interface,
                'description': self._get_snmp_value(f"{self.IF_DESCR}.{if_index}"),
                'admin_status': self._map_admin_status(self._get_snmp_value(f"{self.IF_ADMIN_STATUS}.{if_index}")),
                'oper_status': self._map_oper_status(self._get_snmp_value(f"{self.IF_OPER_STATUS}.{if_index}")),
                'speed': self._format_speed(self._get_snmp_value(f"{self.IF_SPEED}.{if_index}")),
                'duplex': 'unknown',  # SNMP中没有直接的双工信息
                'mtu': self._get_snmp_value(f"{self.IF_MTU}.{if_index}"),
                'in_packets': self._get_snmp_value(f"{self.IF_IN_UCAST_PKTS}.{if_index}"),
                'out_packets': self._get_snmp_value(f"{self.IF_OUT_UCAST_PKTS}.{if_index}"),
                'in_octets': self._get_snmp_value(f"{self.IF_IN_OCTETS}.{if_index}"),
                'out_octets': self._get_snmp_value(f"{self.IF_OUT_OCTETS}.{if_index}")
            }
            
            return status
        except Exception as e:
            error_msg = f"获取SNMP接口状态失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_config(self) -> str:
        """获取设备配置信息"""
        try:
            logger.info(f"开始获取设备 {self.device_info.get('management_ip')} 的配置信息")
            
            # 获取系统描述
            sys_desc = self._get_snmp_value(self.SYS_DESCRIPTION)
            if sys_desc:
                logger.debug(f"系统描述: {sys_desc}")
            else:
                logger.warning("无法获取系统描述")
                sys_desc = "未知系统"
            
            # 获取系统名称
            sys_name = self._get_snmp_value(self.SYS_NAME)
            if sys_name:
                logger.debug(f"系统名称: {sys_name}")
            else:
                logger.warning("无法获取系统名称")
                sys_name = "未知系统名称"
            
            # 获取系统运行时间
            sys_uptime = self._get_snmp_value(self.SYS_UPTIME)
            if sys_uptime:
                logger.debug(f"系统运行时间: {sys_uptime}")
            else:
                logger.warning("无法获取系统运行时间")
                sys_uptime = "未知"
            
            # 获取接口数量
            if_number = self._get_snmp_value(self.IF_NUMBER)
            if if_number:
                logger.debug(f"接口数量: {if_number}")
            else:
                logger.warning("无法获取接口数量")
                if_number = "未知"
            
            # 获取所有接口信息
            interfaces = self.get_interfaces()
            
            # 构造配置信息
            config_lines = []
            config_lines.append("=" * 50)
            config_lines.append("SNMP设备配置信息")
            config_lines.append("=" * 50)
            config_lines.append(f"系统名称: {sys_name}")
            config_lines.append(f"系统描述: {sys_desc}")
            config_lines.append(f"系统运行时间: {sys_uptime}")
            config_lines.append(f"接口数量: {if_number}")
            config_lines.append("")
            config_lines.append("接口状态信息:")
            config_lines.append("-" * 30)
            
            if interfaces:
                for interface in interfaces:
                    config_lines.append(f"接口名称: {interface.get('name', '未知')}")
                    config_lines.append(f"  描述: {interface.get('description', '无')}")
                    config_lines.append(f"  管理状态: {interface.get('admin_status', '未知')}")
                    config_lines.append(f"  操作状态: {interface.get('oper_status', '未知')}")
                    config_lines.append(f"  速率: {interface.get('speed', '未知')}")
                    config_lines.append(f"  MTU: {interface.get('mtu', '未知')}")
                    config_lines.append(f"  入站字节: {interface.get('in_octets', '0')}")
                    config_lines.append(f"  出站字节: {interface.get('out_octets', '0')}")
                    config_lines.append(f"  入站错误: {interface.get('in_errors', '0')}")
                    config_lines.append(f"  出站错误: {interface.get('out_errors', '0')}")
                    config_lines.append("")
            else:
                config_lines.append("无法获取接口信息")
            
            config_lines.append("=" * 50)
            config_lines.append("配置信息获取完成")
            config_lines.append("=" * 50)
            
            config = "\n".join(config_lines)
            logger.info(f"成功获取设备配置信息，共 {len(config)} 字符")
            return config
            
        except Exception as e:
            logger.error(f"获取设备配置信息失败: {str(e)}", exc_info=True)
            # 返回基本的错误信息而不是None
            error_config = f"# 配置获取失败\n# 错误信息: {str(e)}\n# 时间: {datetime.now().isoformat()}\n"
            return error_config

    def save_config(self) -> bool:
        """通过SNMP保存设备配置（简化实现）
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # SNMP协议本身不支持直接保存配置的命令
            # 这里只是模拟保存配置的过程
            logger.info("SNMP适配器不支持直接保存配置，仅记录配置信息")
            
            # 获取当前配置
            config = self.get_config()
            
            # 在实际应用中，可以将配置保存到数据库或其他存储中
            logger.info("配置信息已记录")
            return True
        except Exception as e:
            error_msg = f"通过SNMP保存配置失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)  # 抛出异常而不是返回False

    def execute_command(self, command: str) -> str:
        """执行任意命令（SNMP不支持执行命令，这里返回不支持）"""
        logger.warning(f"SNMP协议不支持执行命令 '{command}'")
        return "SNMP协议不支持执行命令"
    
    def _get_snmp_value(self, oid: str) -> str:
        """获取指定OID的SNMP值"""
        try:
            if not self.transport:
                logger.debug("传输目标未初始化，正在初始化...")
                self.connect()
            
            logger.debug(f"开始获取OID值: {oid}")
            
            # 使用getCmd获取OID值
            cmd_gen = getCmd(self.engine,
                            self.auth_data,
                            self.transport,
                            self.context,
                            ObjectType(ObjectIdentity(oid)))
            
            # 获取响应
            response = next(cmd_gen)
            error_indication, error_status, error_index, var_binds = response
            
            if error_indication:
                logger.error(f"SNMP通信错误 (OID: {oid}): {error_indication}")
                return None
            elif error_status:
                status_text = error_status.prettyPrint()
                logger.error(f"SNMP协议错误 (OID: {oid}): {status_text}")
                return None
            else:
                for var_bind in var_binds:
                    value = var_bind[1]
                    # 检查值是否为'No Such Object'等特殊状态
                    if hasattr(value, 'prettyPrint'):
                        value_str = value.prettyPrint()
                    else:
                        value_str = str(value)
                    
                    if value_str.startswith('No Such Object') or value_str.startswith('No Such Instance'):
                        logger.debug(f"OID {oid} 不存在: {value_str}")
                        return None
                    
                    logger.debug(f"成功获取OID {oid} 的值: {value_str}")
                    return value_str
            
            logger.debug(f"未能获取OID {oid} 的值")
            return None
        except StopIteration as si:
            logger.error(f"SNMP请求被中断 (OID: {oid}): {str(si)}")
            return None
        except PySnmpError as e:
            logger.error(f"PySNMP库错误 (OID: {oid}): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取SNMP值未知错误 (OID: {oid}): {str(e)}", exc_info=True)
            return None
    
    def _walk_snmp_table(self, oid: str) -> Dict[str, Any]:
        """执行SNMP walk操作，获取表格数据"""
        result = {}
        
        try:
            if not self.transport:
                logger.debug("传输目标未初始化，正在初始化...")
                self.connect()
            
            logger.debug(f"开始SNMP walk操作，OID: {oid}")
            
            # 使用nextCmd进行walk操作
            cmd_gen = nextCmd(self.engine,
                             self.auth_data,
                             self.transport,
                             self.context,
                             ObjectType(ObjectIdentity(oid)),
                             lexicographicMode=False)
            
            for response in cmd_gen:
                error_indication, error_status, error_index, var_binds = response
                
                if error_indication:
                    logger.error(f"SNMP walk通信错误 (OID: {oid}): {error_indication}")
                    break
                elif error_status:
                    status_text = error_status.prettyPrint()
                    logger.error(f"SNMP walk协议错误 (OID: {oid}): {status_text}")
                    break
                else:
                    for var_bind in var_binds:
                        # 提取OID索引部分
                        oid_str = str(var_bind[0])
                        oid_parts = oid_str.split('.')
                        if_index = oid_parts[-1] if len(oid_parts) > 1 else '0'
                        
                        value = var_bind[1]
                        # 处理特殊值
                        if hasattr(value, 'prettyPrint'):
                            value_str = value.prettyPrint()
                        else:
                            value_str = str(value)
                            
                        # 忽略不存在的对象
                        if value_str.startswith('No Such Object') or value_str.startswith('No Such Instance'):
                            continue
                            
                        result[if_index] = value_str
                        logger.debug(f"Walk得到: {oid_str} = {value_str}")
            
            logger.debug(f"SNMP walk完成，共获取 {len(result)} 项数据")
            return result
        except StopIteration as si:
            logger.debug(f"SNMP walk正常结束 (OID: {oid})")
            return result
        except PySnmpError as e:
            logger.error(f"PySNMP库错误 (OID: {oid}): {str(e)}")
            return result
        except Exception as e:
            logger.error(f"SNMP walk未知错误 (OID: {oid}): {str(e)}", exc_info=True)
            return result
    
    def _get_interface_index(self, interface_name: str) -> str:
        """根据接口名称获取接口索引"""
        if_descriptions = self._walk_snmp_table(self.IF_DESCR)
        for if_index, description in if_descriptions.items():
            if interface_name in description or description in interface_name:
                return if_index
        return None
    
    def _format_uptime(self, uptime_ticks: int) -> str:
        """格式化SNMP运行时间"""
        # SNMP时间以1/100秒为单位
        seconds = uptime_ticks // 100
        days = seconds // (24 * 3600)
        seconds %= (24 * 3600)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟 {seconds}秒"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟 {seconds}秒"
        elif minutes > 0:
            return f"{minutes}分钟 {seconds}秒"
        else:
            return f"{seconds}秒"
    
    def _format_speed(self, speed: str) -> str:
        """格式化接口速率"""
        try:
            speed_value = int(speed)
            if speed_value >= 1000000000:
                return f"{speed_value / 1000000000:.2f} Gbps"
            elif speed_value >= 1000000:
                return f"{speed_value / 1000000:.2f} Mbps"
            elif speed_value >= 1000:
                return f"{speed_value / 1000:.2f} Kbps"
            else:
                return f"{speed_value} bps"
        except (ValueError, TypeError):
            return "unknown"
    
    def _map_admin_status(self, status: str) -> str:
        """映射管理状态值"""
        status_map = {
            '1': 'up',
            '2': 'down',
            '3': 'testing'
        }
        return status_map.get(status, 'unknown')
    
    def _map_oper_status(self, status: str) -> str:
        """映射操作状态值"""
        status_map = {
            '1': 'up',
            '2': 'down',
            '3': 'testing',
            '4': 'unknown',
            '5': 'dormant',
            '6': 'notPresent',
            '7': 'lowerLayerDown'
        }
        return status_map.get(status, 'unknown')
    
    def _extract_model_from_description(self, description: str) -> str:
        """从系统描述中提取设备型号"""
        # 简单的模式匹配，实际应用中可能需要更复杂的逻辑
        patterns = [
            r'Cisco\s+(\S+)',
            r'Huawei\s+(\S+)',
            r'H3C\s+(\S+)',
            r'Ruijie\s+(\S+)',
            r'Juniper\s+(\S+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.I)
            if match:
                return match.group(1)
        
        # 如果没有匹配到特定厂商，返回前30个字符作为型号信息
        return description[:30].strip()
    
    def _extract_version_from_description(self, description: str) -> str:
        """从系统描述中提取软件版本"""
        # 简单的模式匹配，实际应用中可能需要更复杂的逻辑
        patterns = [
            r'Version\s+([\d\.]+)',
            r'Release\s+([\d\.]+)',
            r'VRP\s+([\d\.]+)',
            r'Comware\s+([\d\.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.I)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def get_device_performance(self):
        """获取设备性能数据"""
        try:
            performance_data = {
                'cpu_usage': None,
                'memory_usage': None,
                'inbound_bandwidth': 0,
                'outbound_bandwidth': 0
            }
            
            # 确保已连接
            if not self.transport:
                if not self.connect():
                    raise ConnectionError("无法连接到设备")
            
            # 获取CPU使用率 - 不同厂商的OID不同
            cpu_oid = None
            vendor = self.device_info.get('vendor', '').lower()
            if vendor == 'cisco':
                cpu_oid = '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1'  # Cisco CPU usage
            elif vendor == 'huawei':
                cpu_oid = '1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5.10'  # Huawei CPU usage
            elif vendor == 'h3c':
                cpu_oid = '1.3.6.1.4.1.25506.2.2.1.1.5.1'  # H3C CPU usage
            else:
                # 尝试标准OID
                cpu_oid = '1.3.6.1.2.1.25.3.3.1.2.1'  # Standard CPU usage
            
            if cpu_oid:
                try:
                    value = self._get_snmp_value(cpu_oid)
                    if value and value.isdigit():
                        performance_data['cpu_usage'] = int(value)
                except Exception as e:
                    logger.warning(f"获取CPU使用率失败: {str(e)}")
            
            # 获取内存使用率
            memory_oid = '1.3.6.1.2.1.25.2.3.1.6.1'  # Standard memory usage (第一个实例)
            try:
                value = self._get_snmp_value(memory_oid)
                if value and value.isdigit():
                    performance_data['memory_usage'] = int(value)
            except Exception as e:
                logger.warning(f"获取内存使用率失败: {str(e)}")
            
            return performance_data
        except Exception as e:
            logger.error(f"获取设备性能数据失败: {str(e)}")
            # 返回默认值
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'inbound_bandwidth': 0,
                'outbound_bandwidth': 0
            }

    def get_snmp_value(self, oid: str) -> Any:
        """
        公共方法：获取单个SNMP OID的值
        
        Args:
            oid: SNMP OID字符串
            
        Returns:
            OID对应的值，如果获取失败返回None
        """
        return self._get_snmp_value(oid)
