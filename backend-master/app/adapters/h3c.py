import re
import logging
from typing import Dict, Any, List
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.adapters.base import BaseAdapter

# 配置日志记录器
logger = logging.getLogger(__name__)


class H3CAdapter(BaseAdapter):
    """华三交换机适配器"""
    
    def connect(self) -> bool:
        """连接到华三交换机"""
        try:
            # 根据协议选择设备类型
            protocol = self.device_info.get('protocol', 'telnet').lower()
            
            if protocol == 'ssh':
                device_type = 'hp_comware'
                port = self.device_info.get('port', 22)
            else:
                device_type = 'hp_comware_telnet'
                port = self.device_info.get('port', 23)
            
            device_params = {
                'device_type': device_type,
                'host': self.device_info.get('management_ip'),
                'username': self.device_info.get('username'),
                'password': self.device_info.get('password'),
                'port': port,
                'timeout': 30,
                'session_log': None
            }
            
            self.connection = ConnectHandler(**device_params)
            logger.info(f"成功连接到华三设备 {self.device_info.get('management_ip')}")
            return True
        except NetMikoTimeoutException as e:
            error_msg = f"华三交换机连接超时: {str(e)}"
            logger.error(error_msg)
            self.connection = None
            raise ConnectionError(error_msg)
        except NetMikoAuthenticationException as e:
            error_msg = f"华三交换机认证失败: {str(e)}"
            logger.error(error_msg)
            self.connection = None
            raise ConnectionError(error_msg)
        except Exception as e:
            error_msg = f"华三交换机连接异常: {str(e)}"
            logger.error(error_msg)
            self.connection = None
            raise ConnectionError(error_msg)
    
    def disconnect(self) -> bool:
        """断开连接"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            return True
        return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        if not self._check_connection():
            error_msg = "设备未连接"
            logger.error(error_msg)
            return {"vendor": "H3C", "error": error_msg}
        
        try:
            # 执行命令获取设备信息
            output = self.execute_command("display version")
            
            # 初始化信息字典
            info = {"vendor": "H3C"}
            
            # 提取型号
            model_match = re.search(r'^.*?(\S+) Device', output, re.MULTILINE)
            if model_match:
                info["model"] = model_match.group(1)
            
            # 提取版本信息
            version_match = re.search(r'^Comware Software, Version (.+)$', output, re.MULTILINE)
            if version_match:
                info["os_version"] = version_match.group(1)
            
            # 提取序列号
            sn_match = re.search(r'^.*?Serial Number\s*:\s*(.+)$', output, re.MULTILINE)
            if sn_match:
                info["serial_number"] = sn_match.group(1).strip()
            
            # 提取运行时间
            uptime_match = re.search(r'^.*?Uptime is (.+)$', output, re.MULTILINE)
            if uptime_match:
                info["uptime"] = uptime_match.group(1)
            
            logger.debug(f"获取华三设备信息成功: {info}")
            return info
        except Exception as e:
            error_msg = f"获取华三设备信息失败: {str(e)}"
            logger.error(error_msg)
            return {"vendor": "H3C", "error": str(e)}
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取接口列表"""
        if not self._check_connection():
            logger.error("设备未连接")
            return []
        
        try:
            # 执行命令获取接口简要信息
            output = self.execute_command("display interface brief")
            
            interfaces = []
            # 解析接口信息
            lines = output.split('\n')
            # 跳过标题行，从第2行开始处理
            for line in lines[1:]:
                # 匹配接口行（示例：Vlan-interface1 UP UP 0.00% 0.00% 0 0）
                parts = line.strip().split()
                if len(parts) >= 3:
                    interface_name = parts[0]
                    admin_status = parts[1]
                    oper_status = parts[2]
                    
                    interfaces.append({
                        "interface_name": interface_name,
                        "admin_status": admin_status,
                        "operational_status": oper_status
                    })
            
            logger.debug(f"获取华三设备接口列表成功，共 {len(interfaces)} 个接口")
            return interfaces
        except Exception as e:
            logger.error(f"获取华三设备接口列表失败: {str(e)}")
            return []
    
    def get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """获取指定接口状态"""
        if not self._check_connection():
            error_msg = "设备未连接"
            logger.error(error_msg)
            return {"interface_name": interface_name, "error": error_msg}
        
        try:
            # 执行命令获取接口详细信息
            output = self.execute_command(f"display interface {interface_name}")
            
            status = {"interface_name": interface_name}
            
            # 提取管理状态和操作状态
            status_match = re.search(r'current state: (\S+)', output)
            if status_match:
                status["admin_status"] = status_match.group(1)
                status["operational_status"] = status_match.group(1)
            
            # 提取MAC地址
            mac_match = re.search(r'Hardware Address is ([0-9a-fA-F\-]+)', output)
            if mac_match:
                status["mac_address"] = mac_match.group(1)
            
            # 提取IP地址
            ip_match = re.search(r'Internet Address is ([0-9\.]+)', output)
            if ip_match:
                status["ip_address"] = ip_match.group(1)
            
            # 提取速率
            speed_match = re.search(r'Port hardware type is (.+?), bandwidth (.+?),', output)
            if speed_match:
                status["speed"] = speed_match.group(2)
            
            # 提取MTU
            mtu_match = re.search(r'Maximum Transmit Unit is (\d+)', output)
            if mtu_match:
                status["mtu"] = int(mtu_match.group(1))
            
            # 提取描述信息
            desc_match = re.search(r'Description:\s*(.*)', output)
            if desc_match:
                status["description"] = desc_match.group(1)
            
            logger.debug(f"获取华三设备接口状态成功: {interface_name}")
            return status
        except Exception as e:
            logger.error(f"获取华三设备接口状态失败 {interface_name}: {str(e)}")
            return {"interface_name": interface_name, "error": str(e)}
    
    def get_config(self) -> str:
        """获取设备配置"""
        if not self._check_connection():
            error_msg = "设备未连接"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        
        try:
            # 执行命令获取当前配置
            config = self.execute_command("display current-configuration")
            if not config:
                error_msg = "未获取到设备配置内容"
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.debug("获取华三设备配置成功")
            return config
        except Exception as e:
            logger.error(f"获取华三设备配置失败: {str(e)}")
            raise
    
    def save_config(self) -> bool:
        """保存设备配置"""
        if not self._check_connection():
            logger.error("设备未连接")
            return False
        
        try:
            # 执行保存配置命令
            output = self.execute_command("save force")
            # 检查是否保存成功
            if "successfully" in output.lower() or "saved" in output.lower():
                logger.info("华三设备配置保存成功")
                return True
            else:
                logger.warning("华三设备配置保存可能失败")
                return False
        except Exception as e:
            logger.error(f"保存华三设备配置失败: {str(e)}")
            return False
    
    def execute_command(self, command: str) -> str:
        """执行任意命令"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            result = self.connection.send_command(command)
            return result
        except Exception as e:
            error_msg = f"执行华三设备命令失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)