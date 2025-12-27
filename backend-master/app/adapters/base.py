from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, List, Optional
from netmiko import ConnectHandler
# 适配 netmiko 4.6.0 版本的异常处理导入
try:
    from netmiko import NetmikoTimeoutException, NetmikoAuthenticationException
    from paramiko.ssh_exception import SSHException
except ImportError:
    from netmiko.ssh_exception import NetmikoTimeoutException, NetmikoAuthenticationException
    from paramiko.ssh_exception import SSHException

import time

# 配置日志记录器
logger = logging.getLogger(__name__)

class BaseAdapter(ABC):
    """设备适配器基类"""
    
    def __init__(self, device_info: Dict[str, Any]):
        """初始化适配器
        
        Args:
            device_info: 设备连接信息字典，包含:
                - management_ip: 管理IP地址
                - username: 用户名
                - password: 密码
                - port: 端口号
                - enable_password: 特权密码（可选）
        """
        self.device_info = device_info
        self.connection = None
        self.connection_status = False
    
    def connect(self) -> bool:
        """建立设备连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if self.connection_status:
                logger.debug("设备已连接，无需重新连接")
                return True
            
            # 准备连接参数
            connection_params = {
                'device_type': self.get_device_type(),
                'host': self.device_info['management_ip'],
                'username': self.device_info['username'],
                'password': self.device_info['password'],
                'port': self.device_info.get('port', 22),
                'timeout': 20,  # 连接超时时间
            }
            
            # 如果提供了enable密码，则添加
            if self.device_info.get('enable_password'):
                connection_params['secret'] = self.device_info['enable_password']
            
            logger.info(f"正在连接设备 {self.device_info['management_ip']}")
            
            # 建立连接
            self.connection = ConnectHandler(**connection_params)
            self.connection_status = True
            
            # 如果需要进入特权模式
            if self.device_info.get('enable_password'):
                self.connection.enable()
            
            logger.info(f"成功连接到设备 {self.device_info['management_ip']}")
            return True
            
        except NetmikoTimeoutException:
            logger.error(f"连接设备超时: {self.device_info['management_ip']}")
            self.connection_status = False
            return False
        except NetmikoAuthenticationException:
            logger.error(f"设备认证失败: {self.device_info['management_ip']}")
            self.connection_status = False
            return False
        except SSHException as e:
            logger.error(f"SSH连接错误 {self.device_info['management_ip']}: {str(e)}")
            self.connection_status = False
            return False
        except Exception as e:
            logger.error(f"连接设备时发生未知错误 {self.device_info['management_ip']}: {str(e)}")
            self.connection_status = False
            return False
    
    def _check_connection(self) -> bool:
        """检查连接状态，如果未连接则尝试连接
        
        Returns:
            bool: 连接是否可用
        """
        if not self.connection or not self.connection_status:
            return self.connect()
        return True
    
    def disconnect(self):
        """断开设备连接"""
        try:
            if self.connection and self.connection_status:
                self.connection.disconnect()
                logger.info(f"已断开设备连接 {self.device_info['management_ip']}")
        except Exception as e:
            logger.error(f"断开设备连接时发生错误 {self.device_info['management_ip']}: {str(e)}")
        finally:
            self.connection = None
            self.connection_status = False
    
    def execute_command(self, command: str, use_textfsm: bool = False) -> str:
        """执行命令
        
        Args:
            command: 要执行的命令
            use_textfsm: 是否使用TextFSM解析输出
            
        Returns:
            str: 命令执行结果
        """
        if not self._check_connection():
            raise Exception("无法连接到设备")
        
        try:
            logger.debug(f"在设备 {self.device_info['management_ip']} 上执行命令: {command}")
            output = self.connection.send_command(command, use_textfsm=use_textfsm)
            logger.debug(f"命令执行完成: {command}")
            return output
        except Exception as e:
            logger.error(f"执行命令失败 {self.device_info['management_ip']}: {command}, 错误: {str(e)}")
            raise
    
    @abstractmethod
    def get_device_type(self) -> str:
        """获取设备类型字符串（用于Netmiko）
        
        Returns:
            str: Netmiko设备类型字符串
        """
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息
        
        Returns:
            Dict[str, Any]: 设备信息字典
        """
        pass
    
    @abstractmethod
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取接口列表
        
        Returns:
            List[Dict[str, Any]]: 接口信息列表
        """
        pass
    
    @abstractmethod
    def get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """获取指定接口状态
        
        Args:
            interface_name: 接口名称
            
        Returns:
            Dict[str, Any]: 接口状态信息
        """
        pass
    
    @abstractmethod
    def get_config(self) -> str:
        """获取设备配置
        
        Returns:
            str: 设备配置文本
        """
        pass
    
    @abstractmethod
    def save_config(self) -> bool:
        """保存设备配置
        
        Returns:
            bool: 是否保存成功
        """
        pass