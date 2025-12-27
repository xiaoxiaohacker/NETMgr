import re
import logging
import time
from typing import Dict, Any, List
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.adapters.base import BaseAdapter

# 配置日志记录器
logger = logging.getLogger(__name__)


class HuaweiAdapter(BaseAdapter):
    """华为设备适配器"""

    def get_device_type(self) -> str:
        """获取设备类型"""
        # 根据端口判断使用SSH还是Telnet
        port = self.device_info.get('port', 22)
        if port == 22:
            return "huawei"  # SSH
        else:
            return "huawei_telnet"  # Telnet

    def connect(self) -> bool:
        """连接到华为设备"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 根据端口号自动判断协议类型
                port = self.device_info.get('port', 22)
                
                # 如果端口是22，使用SSH；否则使用Telnet
                if port == 22:
                    device_type = 'huawei'  # SSH
                else:
                    device_type = 'huawei_telnet'  # Telnet
                
                device_params = {
                    'device_type': device_type,
                    'host': self.device_info.get('management_ip'),
                    'username': self.device_info.get('username'),
                    'password': self.device_info.get('password'),
                    'port': port,
                    'timeout': 20,
                    'blocking_timeout': 8,  # 防止长时间阻塞
                    'session_log': None,  # 可以设置日志文件用于调试
                }
                
                # 如果提供了enable密码，则添加
                if self.device_info.get('enable_password'):
                    device_params['secret'] = self.device_info['enable_password']
                
                logger.info(f"第 {attempt + 1} 次尝试连接华为设备 {self.device_info.get('management_ip')}:{port} 使用 {device_type} 协议")
                logger.debug(f"连接参数: 用户名={self.device_info.get('username')}, 端口={port}")
                
                # 建立连接
                self.connection = ConnectHandler(**device_params)
                self.connection_status = True
                
                # 如果需要进入特权模式
                if self.device_info.get('enable_password'):
                    self.connection.enable()
                
                logger.info(f"成功连接到华为设备 {self.device_info.get('management_ip')}")
                return True
                
            except NetMikoTimeoutException as e:
                error_msg = f"华为设备连接超时: {self.device_info.get('management_ip')}:{port} (尝试 {attempt + 1}/{max_retries})"
                logger.error(error_msg)
                self.connection = None
                self.connection_status = False
                
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                continue
                
            except NetMikoAuthenticationException as e:
                error_msg = f"华为设备认证失败: {self.device_info.get('management_ip')}:{port} 用户名: {self.device_info.get('username')}"
                logger.error(error_msg)
                logger.debug(f"认证失败详细信息: {str(e)}")
                self.connection = None
                self.connection_status = False
                
                # 在认证失败的情况下也进行重试
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                continue
                
            except Exception as e:
                error_msg = f"连接华为设备时发生未知错误: {self.device_info.get('management_ip')}:{port} 错误: {str(e)} (尝试 {attempt + 1}/{max_retries})"
                logger.error(error_msg)
                self.connection = None
                self.connection_status = False
                
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                continue
        
        return False

    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        try:
            # 检查连接状态
            if not self._check_connection():
                return {"vendor": "Huawei", "error": "设备连接失败"}
            
            # 执行命令获取设备信息
            output = self.execute_command("display version")
            
            # 解析设备信息
            info = {"vendor": "Huawei"}
            
            # 提取型号
            model_match = re.search(r'^Huawei (.+?) Router', output, re.MULTILINE)
            if model_match:
                info["model"] = model_match.group(1)
            
            # 提取版本信息
            version_match = re.search(r'VRP.*?Software, Version (.+)', output)
            if version_match:
                info["os_version"] = version_match.group(1)
            
            # 提取序列号
            sn_match = re.search(r'^.*?DEVICE_SERIAL_NUMBER\s+(.+)$', output, re.MULTILINE)
            if sn_match:
                info["serial_number"] = sn_match.group(1)
            
            logger.debug(f"获取华为设备信息成功: {info}")
            return info
        except Exception as e:
            logger.error(f"获取华为设备信息失败: {str(e)}")
            return {"vendor": "Huawei", "error": str(e)}
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取接口列表"""
        try:
            # 检查连接状态
            if not self._check_connection():
                raise ConnectionError("设备连接失败")
            
            # 执行命令获取接口简要信息
            output = self.execute_command("display interface brief")
            
            interfaces = []
            # 解析接口信息
            lines = output.split('\n')
            for line in lines:
                # 匹配接口行（示例：GigabitEthernet0/0/1 up up 1000M(full) - - - -
                match = re.match(r'^(\S+)\s+(up|down)\s+(up|down)', line.strip())
                if match:
                    interface_name = match.group(1)
                    admin_status = match.group(2)
                    oper_status = match.group(3)
                    
                    interfaces.append({
                        "interface_name": interface_name,
                        "admin_status": admin_status,
                        "operational_status": oper_status
                    })
            
            logger.debug(f"获取华为设备接口列表成功，共 {len(interfaces)} 个接口")
            return interfaces
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"获取华为设备接口列表失败: {str(e)}")
            raise ConnectionError(f"设备连接失败: {str(e)}")
    
    def get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """获取指定接口状态"""
        try:
            # 检查连接状态
            if not self._check_connection():
                raise ConnectionError("设备连接失败")
            
            # 执行命令获取接口详细信息
            output = self.execute_command(f"display interface {interface_name}")
            
            status = {"interface_name": interface_name}
            
            # 提取管理状态
            admin_match = re.search(r'current state : (\S+)', output)
            if admin_match:
                status["admin_status"] = admin_match.group(1)
            
            # 提取操作状态
            oper_match = re.search(r'current state : (\S+)', output)
            if oper_match:
                status["operational_status"] = oper_match.group(1)
            
            # 提取MAC地址
            mac_match = re.search(r'address is ([0-9a-fA-F\-]+)', output)
            if mac_match:
                status["mac_address"] = mac_match.group(1)
            
            # 提取IP地址
            ip_match = re.search(r'Internet Address is ([0-9\.]+)', output)
            if ip_match:
                status["ip_address"] = ip_match.group(1)
            
            # 提取速率
            speed_match = re.search(r'Baudrate (\d+) Mbps', output)
            if speed_match:
                status["speed"] = f"{speed_match.group(1)} Mbps"
            
            logger.debug(f"获取华为设备接口状态成功: {interface_name}")
            return status
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"获取华为设备接口状态失败 {interface_name}: {str(e)}")
            raise ConnectionError(f"设备连接失败: {str(e)}")
    
    def get_config(self) -> str:
        """获取设备配置"""
        try:
            # 检查连接状态
            if not self._check_connection():
                raise ConnectionError("设备连接失败")
            
            # 执行命令获取当前配置，使用更长的超时时间（60秒）
            config = self.execute_command("display current-configuration", timeout=60)
            logger.debug("获取华为设备配置成功")
            return config
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"获取华为设备配置失败: {str(e)}")
            raise ConnectionError(f"设备连接失败: {str(e)}")
    
    def save_config(self) -> bool:
        """保存设备配置"""
        # 检查连接状态
        if not self._check_connection():
            logger.error("保存华为设备配置失败: 设备连接不可用")
            return False
            
        try:
            # 发送保存配置命令
            print("执行命令: save")
            
            # 清除可能的缓冲区内容
            try:
                self.connection.read_channel()
            except:
                pass
            
            # 发送保存命令
            self.connection.write_channel("save\n")
            time.sleep(1)
            
            # 读取设备响应
            output = ""
            timeout = time.time() + 10  # 10秒超时
            while time.time() < timeout:
                try:
                    chunk = self.connection.read_channel()
                    if chunk:
                        output += chunk
                        # 重置超时计时器
                        timeout = time.time() + 2
                        # 检查是否需要确认
                        if "[Y/N]" in output:
                            break
                    else:
                        time.sleep(0.1)
                except Exception as e:
                    print(f"读取响应时出错: {str(e)}")
                    break
            
            print(f"保存命令初始响应: {output}")
            
            # 如果看到确认提示，发送"y"确认
            if "[Y/N]" in output:
                print("检测到确认提示，发送确认...")
                self.connection.write_channel("y\n")
                time.sleep(2)  # 等待保存完成
                
                # 读取最终响应
                final_output = ""
                timeout = time.time() + 10
                while time.time() < timeout:
                    try:
                        chunk = self.connection.read_channel()
                        if chunk:
                            final_output += chunk
                            timeout = time.time() + 2
                            # 检查是否完成
                            if any(prompt in final_output for prompt in ['#', '>']):
                                break
                        else:
                            time.sleep(0.1)
                    except Exception as e:
                        print(f"读取最终响应时出错: {str(e)}")
                        break
                
                output += final_output
                print(f"保存命令最终响应: {final_output}")
            
            # 检查是否保存成功
            if "successfully" in output.lower() or "saved" in output.lower() or "completed" in output.lower():
                logger.info("华为设备配置保存成功")
                return True
            else:
                logger.warning(f"华为设备配置保存可能失败，响应内容: {output}")
                return False
        except Exception as e:
            logger.error(f"保存华为设备配置失败: {str(e)}")
            return False
    
    def execute_command(self, command: str, timeout: int = 30) -> str:
        """执行任意命令 - 增强版（支持可配置超时时间）
        
        Args:
            command: 要执行的命令
            timeout: 命令执行超时时间（秒），默认30秒
        """
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            print(f"执行命令: {command} (超时: {timeout}秒)")
            
            # 清除可能的缓冲区内容
            try:
                self.connection.read_channel()
            except:
                pass
            
            # 使用底层方法发送命令并读取响应
            self.connection.write_channel(command + '\n')
            
            # 等待命令执行完成
            time.sleep(2)  # 增加延迟以确保命令开始执行
            
            # 读取响应内容
            response = ""
            timeout_time = time.time() + timeout
            last_received_time = time.time()
            
            # 持续读取直到超时或检测到命令完成
            while time.time() < timeout_time:
                try:
                    chunk = self.connection.read_channel()
                    if chunk:
                        response += chunk
                        last_received_time = time.time()  # 更新最后接收时间
                        # 重置超时计时器
                        timeout_time = time.time() + min(timeout, 5)  # 最多延长5秒等待新数据
                    else:
                        # 如果一段时间内没有新数据，检查是否已完成
                        if time.time() - last_received_time > 3:  # 3秒内没有新数据
                            # 检查是否检测到命令提示符，认为命令执行完成
                            if any(prompt in response for prompt in ['#', '>', '$', '%', ']', '<']):
                                print("检测到命令提示符，认为命令执行完成")
                                break
                        # 短暂暂停以避免CPU占用过高
                        time.sleep(0.1)
                except Exception as chunk_error:
                    print(f"读取响应块错误: {str(chunk_error)}")
                    break
            
            # 清理响应内容
            if response:
                # 去除命令回显
                if response.startswith(command):
                    response = response[len(command):]
                response = response.strip()
                
                # 检查是否存在访问权限问题，尝试进入特权模式
                if any(deny_keyword in response.lower() for deny_keyword in ['access denied', '权限不足', '未授权', 'privilege denied']):
                    print(f"检测到访问权限问题，尝试进入特权模式...")
                    
                    # 尝试进入特权模式
                    self._enter_privileged_mode()
                    
                    # 清除缓冲区
                    try:
                        self.connection.read_channel()
                    except:
                        pass
                    
                    # 重新执行命令
                    print(f"重新执行命令: {command}")
                    self.connection.write_channel(command + '\n')
                    time.sleep(2)
                    
                    # 重新读取响应
                    response = ""
                    retry_timeout = time.time() + timeout
                    last_received_time = time.time()
                    while time.time() < retry_timeout:
                        try:
                            chunk = self.connection.read_channel()
                            if chunk:
                                response += chunk
                                last_received_time = time.time()
                                retry_timeout = time.time() + min(timeout, 5)
                                # 增加华为设备特定提示符格式 <hostname>
                                if any(prompt in response for prompt in ['#', '>', '$', '%', ']', '<']):
                                    print("检测到命令提示符，认为重试命令执行完成")
                                    break
                            else:
                                # 如果一段时间内没有新数据，检查是否已完成
                                if time.time() - last_received_time > 3:
                                    if any(prompt in response for prompt in ['#', '>', '$', '%', ']', '<']):
                                        print("检测到命令提示符，认为重试命令执行完成")
                                        break
                                time.sleep(0.1)
                        except:
                            break
                    
                    # 清理重新执行的响应
                    if response and response.startswith(command):
                        response = response[len(command):]
                    response = response.strip()
            
            print(f"命令执行结果长度: {len(response)} 字符")
            # 如果响应长度太短，打印前几个字符用于调试
            if len(response) < 100:
                print(f"命令执行结果: {response}")
            return response
        except ConnectionError:
            raise
        except Exception as e:
            error_msg = f"执行华为设备命令失败: {str(e)}"
            print(error_msg)
            raise ConnectionError(error_msg)

    def _check_connection(self) -> bool:
        """检查连接状态，如果未连接则尝试连接
        
        Returns:
            bool: 连接是否可用
        """
        # 检查连接是否仍然活跃
        if self.connection and self.connection_status:
            try:
                # 发送一个简单的命令来检查连接是否仍然有效
                self.connection.find_prompt()
                return True
            except Exception as e:
                logger.warning(f"连接已失效，需要重新连接: {str(e)}")
                # 连接已失效，重置连接状态
                self.connection = None
                self.connection_status = False
        
        # 如果没有活动连接，则尝试建立新连接
        if not self.connection or not self.connection_status:
            return self.connect()
        return True