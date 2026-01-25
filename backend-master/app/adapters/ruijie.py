import time
import re
import logging
from typing import Dict, Any, List
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.adapters.base import BaseAdapter

# 配置日志记录器
logger = logging.getLogger(__name__)

class RuijieAdapter(BaseAdapter):
    """锐捷设备适配器"""
    
    def __init__(self, device_info: Dict[str, Any]):
        """初始化锐捷设备适配器"""
        super().__init__(device_info)
        self.connected = False
        self.start_time = None
        self.connection_time = None
        self.in_privileged_mode = False
        
    def get_device_type(self) -> str:
        """获取设备类型"""
        return "ruijie"

    def connect(self) -> bool:
        """连接到锐捷交换机"""
        try:
            if self.connected:
                logger.warning("已经连接到设备，不需要重新连接")
                return True
            
            # 从device_info中获取连接信息
            ip = self.device_info.get('management_ip')
            username = self.device_info.get('username', '')
            password = self.device_info.get('password', '')
            
            # 验证必要的连接信息
            if not ip:
                raise ValueError("设备IP地址不能为空")
            if not username:
                raise ValueError("设备用户名不能为空")
            
            self.ip = ip
            self.port = 23  # 强制使用telnet端口
            self.username = username
            self.password = password
            self.start_time = time.time()  # 记录开始时间
            logger.info(f"尝试连接锐捷设备 {self.ip}:{self.port}")
            
            # 使用generic_telnet设备类型
            device_type = 'generic_telnet'
            
            # 基础连接参数
            params = {
                'ip': self.ip,
                'port': self.port,
                'username': self.username,
                'password': self.password,
                'device_type': device_type,
                'timeout': 20,
                'verbose': False
            }
            
            # 建立连接
            self.connection = ConnectHandler(**params)
            
            # 记录连接时间
            self.connection_time = time.time() - self.start_time
            self.connected = True
            self.in_privileged_mode = False  # 重置特权模式状态
            
            logger.info(f"成功连接到锐捷设备 {self.ip}，连接耗时: {self.connection_time:.2f}秒")
            return True
            
        except NetMikoTimeoutException:
            error_msg = f"连接锐捷设备超时: {self.ip}:{self.port}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except NetMikoAuthenticationException:
            error_msg = f"连接锐捷设备认证失败: {self.ip}:{self.port}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"连接锐捷设备时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def disconnect(self) -> bool:
        """断开与锐捷设备的连接"""
        try:
            if self.connected and self.connection:
                self.connection.disconnect()
                self.connected = False
                self.in_privileged_mode = False
                logger.info(f"已断开与锐捷设备的连接: {self.ip}")
                return True
            return False
        except Exception as e:
            logger.error(f"断开连接时发生错误: {str(e)}")
            return False

    def _enter_privileged_mode(self) -> bool:
        """进入特权模式"""
        # 检查连接状态
        if not self._check_connection():
            logger.error("设备连接不可用，无法进入特权模式")
            return False
        
        if self.in_privileged_mode:
            # 再次确认是否真的在特权模式
            try:
                self.connection.write_channel("\n")
                time.sleep(0.5)
                prompt_output = self.connection.read_channel()
                if "#" in prompt_output:
                    return True
                else:
                    # 状态不一致，重新检查
                    self.in_privileged_mode = False
            except Exception as e:
                logger.warning(f"检查特权模式状态时出错: {str(e)}")
                self.in_privileged_mode = False
        
        try:
            # 获取登录凭据
            enable_password = self.device_info.get('enable_password', '')
            username = self.device_info.get('username', '')
            password = self.device_info.get('password', '')
            # 修复：处理enable_password为None的情况
            enable_password_len = len(enable_password) if enable_password else 0
            logger.debug(f"使用的用户名: {username}, enable密码长度: {enable_password_len}")
            
            # 发送换行符并读取当前提示符
            self.connection.write_channel("\n")
            time.sleep(0.5)
            prompt_output = self.connection.read_channel()
            logger.debug(f"当前提示符: {repr(prompt_output)}")
            
            # 标准锐捷登录流程处理
            # 如果出现Username提示，说明需要重新登录
            if "Username" in prompt_output or "username" in prompt_output or "login" in prompt_output.lower():
                logger.info("检测到需要重新登录，执行标准登录流程")
                # 1. 输入用户名
                self.connection.write_channel(username + "\n")
                time.sleep(0.5)
                output = self.connection.read_channel()
                logger.debug(f"输入用户名后输出: {repr(output)}")
                
                # 2. 等待密码提示并输入密码
                if "Password" in output or "password" in output or ":" in output:
                    self.connection.write_channel(password + "\n")
                    time.sleep(1)
                    output = self.connection.read_channel()
                    logger.debug(f"输入密码后输出: {repr(output)}")
                    
                    # 3. 检查是否成功登录到用户模式
                    if ">" in output and not ("%" in output or "denied" in output.lower()):
                        logger.info("登录成功，进入用户模式")
                        # 获取登录后的提示符
                        self.connection.write_channel("\n")
                        time.sleep(0.5)
                        prompt_output = self.connection.read_channel()
                        logger.debug(f"登录后提示符: {repr(prompt_output)}")
                    else:
                        logger.error("登录失败")
                        return False
                else:
                    logger.error("登录过程异常，未提示输入密码")
                    return False
            
            # 再次检查提示符状态
            self.connection.write_channel("\n")
            time.sleep(0.5)
            prompt_output = self.connection.read_channel()
            logger.debug(f"当前提示符状态: {repr(prompt_output)}")
            
            # 如果仍然需要登录，再次处理
            if "Username" in prompt_output or "username" in prompt_output or "login" in prompt_output.lower():
                logger.info("仍需登录，重新执行登录流程")
                # 1. 输入用户名
                self.connection.write_channel(username + "\n")
                time.sleep(0.5)
                output = self.connection.read_channel()
                logger.debug(f"输入用户名后输出: {repr(output)}")
                
                # 2. 等待密码提示并输入密码
                if "Password" in output or "password" in output or ":" in output:
                    self.connection.write_channel(password + "\n")
                    time.sleep(1)
                    output = self.connection.read_channel()
                    logger.debug(f"输入密码后输出: {repr(output)}")
                    
                    # 3. 检查是否成功登录到用户模式
                    if ">" in output and not ("%" in output or "denied" in output.lower()):
                        logger.info("登录成功，进入用户模式")
                        # 获取登录后的提示符
                        self.connection.write_channel("\n")
                        time.sleep(0.5)
                        prompt_output = self.connection.read_channel()
                        logger.debug(f"登录后提示符: {repr(prompt_output)}")
                    else:
                        logger.error("登录失败")
                        return False
                else:
                    logger.error("登录过程异常，未提示输入密码")
                    return False
            
            # 检查当前模式
            if "#" in prompt_output and not ("%" in prompt_output or "denied" in prompt_output.lower()):
                # 已经在特权模式
                self.in_privileged_mode = True
                logger.info("设备已经处于特权模式")
                return True
            elif ">" in prompt_output:
                # 在用户模式，需要进入特权模式
                logger.info("设备处于用户模式，执行进入特权模式流程")
                # 1. 发送enable命令
                self.connection.write_channel("enable\n")
                time.sleep(0.5)
                output = self.connection.read_channel()
                logger.debug(f"发送enable命令后输出: {repr(output)}")
                
                # 2. 检查是否需要输入特权密码
                if "Password" in output or "password" in output or ":" in output:
                    # 3. 输入特权密码
                    self.connection.write_channel(enable_password + "\n")  # 注意：这里如果enable_password为None会出错
                    time.sleep(1)
                    output = self.connection.read_channel()
                    logger.debug(f"输入特权密码后输出: {repr(output)}")
                    
                    # 4. 检查是否成功进入特权模式
                    if "#" in output and not ("%" in output or "denied" in output.lower()):
                        self.in_privileged_mode = True
                        logger.info("成功进入特权模式")
                        return True
                    else:
                        logger.error(f"进入特权模式失败，输出: {repr(output)}")
                        return False
                else:
                    # 可能不需要密码
                    self.connection.write_channel("\n")
                    time.sleep(0.5)
                    output = self.connection.read_channel()
                    if "#" in output and not ("%" in output or "denied" in output.lower()):
                        self.in_privileged_mode = True
                        logger.info("成功进入特权模式（无需密码）")
                        return True
                    else:
                        logger.error(f"进入特权模式失败，输出: {repr(output)}")
                        return False
            else:
                # 提示符为空或其他异常情况
                if not prompt_output.strip():
                    logger.error("无法获取设备提示符，连接可能已断开")
                    return False
                else:
                    # 尝试通用方法
                    logger.info("尝试通用进入特权模式方法")
                    # 发送enable命令
                    self.connection.write_channel("enable\n")
                    time.sleep(0.5)
                    output = self.connection.read_channel()
                    logger.debug(f"发送enable命令后输出: {repr(output)}")
                    
                    # 检查是否需要输入特权密码
                    if "Password" in output or "password" in output or ":" in output:
                        # 输入特权密码
                        # 修复：处理enable_password为None的情况
                        if enable_password:
                            self.connection.write_channel(enable_password + "\n")
                        else:
                            # 如果没有enable密码，则发送回车
                            self.connection.write_channel("\n")
                        time.sleep(1)
                        output = self.connection.read_channel()
                        logger.debug(f"输入特权密码后输出: {repr(output)}")
                        
                        # 检查是否成功进入特权模式
                        if "#" in output and not ("%" in output or "denied" in output.lower()):
                            self.in_privileged_mode = True
                            logger.info("成功进入特权模式")
                            return True
                        else:
                            logger.error(f"进入特权模式失败，输出: {repr(output)}")
                            return False
                    elif "#" in output and not ("%" in output or "denied" in output.lower()):
                        self.in_privileged_mode = True
                        logger.info("成功进入特权模式（无需密码）")
                        return True
                    else:
                        logger.error(f"无法识别的设备状态，输出: {repr(output)}")
                        return False
                        
        except Exception as e:
            logger.error(f"进入特权模式时发生错误: {str(e)}")
            return False

    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        try:
            # 确保在特权模式下执行命令
            if not self._enter_privileged_mode():
                raise Exception("无法进入特权模式")
            
            # 执行命令获取设备信息
            output = self.execute_command("show version")
            
            # 解析设备信息
            info = {"vendor": "Ruijie"}
            
            # 提取型号
            model_match = re.search(r'^Model\s*:\s*(.+)$', output, re.MULTILINE)
            if model_match:
                info["model"] = model_match.group(1).strip()
            
            # 提取版本信息
            version_match = re.search(r'^Software Version\s*:\s*(.+)$', output, re.MULTILINE)
            if version_match:
                info["os_version"] = version_match.group(1).strip()
            
            # 提取序列号
            sn_match = re.search(r'^Serial Number\s*:\s*(.+)$', output, re.MULTILINE)
            if sn_match:
                info["serial_number"] = sn_match.group(1).strip()
            
            # 提取运行时间 - 尝试多种可能的格式
            uptime_patterns = [
                r'(?i)(uptime is .+?|up time.*?|\d+ days?, \d+ hours?, \d+ minutes?)',
                r'(?i)(\d+ weeks?, )?\s*(\d+ days?, )?\s*(\d+ hours?, )?\s*(\d+ minutes?)',
                r'(?i)uptime:?\s*(.+?)(?:\n|$)',
                r'(?i)system uptime\s*:?\s*(.+?)(?:\n|$)',
                r'(?i)(\d+\s+(?:weeks|days|hours|minutes|seconds).*)'
            ]
            
            uptime = None
            for pattern in uptime_patterns:
                uptime_match = re.search(pattern, output, re.MULTILINE | re.DOTALL)
                if uptime_match:
                    uptime = uptime_match.group(1).strip()
                    break
            
            if uptime:
                info["uptime"] = uptime.replace("Uptime is ", "").replace("up time ", "").replace("Uptime:", "").strip()
            else:
                info["uptime"] = "N/A"
            
            logger.debug(f"获取锐捷设备信息成功: {info}")
            return info
        except Exception as e:
            error_msg = f"获取锐捷设备信息失败: {str(e)}"
            logger.error(error_msg)
            return {"vendor": "Ruijie", "error": str(e)}

    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取接口列表"""
        try:
            # 确保在特权模式下执行命令
            if not self._enter_privileged_mode():
                raise Exception("无法进入特权模式")
            
            # 执行命令获取接口简要信息
            output = self.execute_command("show interface status")
            
            interfaces = []
            # 解析接口信息
            lines = output.split('\n')
            for line in lines:
                # 跳过空行和标题行
                line = line.strip()
                if not line or line.startswith('-') or 'port' in line.lower():
                    continue
                    
                # 匹配接口行（示例：Gi0/1  connected    100  full  a-half  1000  Tpe）
                # 改进的正则表达式，更好地匹配接口信息
                parts = line.split()
                if len(parts) >= 2:
                    interface_name = parts[0]
                    status = parts[1] if len(parts) > 1 else "unknown"
                    speed = parts[2] if len(parts) > 2 else "unknown"
                    
                    interfaces.append({
                        "interface_name": interface_name,
                        "admin_status": status,
                        "operational_status": status,
                        "speed": f"{speed} Mbps" if speed.isdigit() else speed
                    })
            
            logger.debug(f"获取锐捷设备接口列表成功，共 {len(interfaces)} 个接口")
            return interfaces
        except Exception as e:
            error_msg = f"获取锐捷设备接口列表失败: {str(e)}"
            logger.error(error_msg)
            # 即使获取接口列表失败，也尝试返回部分结果或空列表而不是抛出异常
            return []

    def get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """获取指定接口状态"""
        try:
            # 确保在特权模式下执行命令
            if not self._enter_privileged_mode():
                raise Exception("无法进入特权模式")
            
            # 执行命令获取接口详细信息
            output = self.execute_command(f"show interface {interface_name}")
            
            status = {"interface_name": interface_name}
            
            # 提取管理状态和操作状态
            status_match = re.search(r'line protocol is (\S+)', output)
            if status_match:
                status["admin_status"] = status_match.group(1)
                status["operational_status"] = status_match.group(1)
            
            # 提取MAC地址
            mac_match = re.search(r'address is ([0-9a-fA-F\-]+)', output)
            if mac_match:
                status["mac_address"] = mac_match.group(1)
            
            # 提取IP地址
            ip_match = re.search(r'Internet address is ([0-9\.]+)', output)
            if ip_match:
                status["ip_address"] = ip_match.group(1)
            
            # 提取速率
            speed_match = re.search(r'(\d+) Mbps', output)
            if speed_match:
                status["speed"] = f"{speed_match.group(1)} Mbps"
            
            logger.debug(f"获取锐捷设备接口状态成功: {interface_name}")
            return status
        except Exception as e:
            error_msg = f"获取锐捷设备接口状态失败 {interface_name}: {str(e)}"
            logger.error(error_msg)
            return {"interface_name": interface_name, "error": str(e)}

    def get_config(self) -> str:
        """获取设备配置"""
        try:
            # 确保在特权模式下执行命令
            if not self._enter_privileged_mode():
                raise Exception("无法进入特权模式")
            
            # 执行命令获取当前配置
            config = self.execute_command("show running-config")
            logger.debug("获取锐捷设备配置成功")
            return config
        except Exception as e:
            logger.error(f"获取锐捷设备配置失败: {str(e)}")
            return ""

    def save_config(self) -> bool:
        """保存设备配置"""
        try:
            # 确保在特权模式下执行命令
            if not self._enter_privileged_mode():
                raise Exception("无法进入特权模式")
            
            # 执行保存配置命令
            output = self.execute_command("write")
            # 检查是否保存成功
            if "OK" in output or "successfully" in output.lower():
                logger.info("锐捷设备配置保存成功")
                return True
            else:
                logger.warning("锐捷设备配置保存可能失败")
                return False
        except Exception as e:
            logger.error(f"保存锐捷设备配置失败: {str(e)}")
            return False

    def execute_command(self, command: str) -> str:
        """在设备上执行任意命令"""
        if not self._check_connection():
            raise Exception("设备未连接")
        
        try:
            # 使用备用方法作为主要方法，因为它在我们的场景中更可靠
            # 清除缓冲区
            self.connection.clear_buffer()
            
            # 发送命令
            self.connection.write_channel(command + "\n")
            time.sleep(1)  # 初始等待
            
            # 循环读取输出直到获得稳定的输出
            output = ""
            consecutive_empty_reads = 0
            max_empty_reads = 5
            
            while consecutive_empty_reads < max_empty_reads:
                new_output = self.connection.read_channel()
                if new_output:
                    output += new_output
                    # 检查是否有分页提示，如果有则发送空格继续
                    if "--More--" in new_output or "-- more --" in new_output:
                        self.connection.write_channel(" ")
                        time.sleep(0.5)
                        continue  # 继续读取，不清除计数器
                    
                    consecutive_empty_reads = 0  # 重置计数器
                    time.sleep(1)  # 继续等待更多输出
                else:
                    consecutive_empty_reads += 1
                    time.sleep(1)  # 等待更长时间
            
            logger.debug(f"执行命令 '{command}' 的完整输出: {repr(output)}")
            
            # 清理输出，移除命令回显和提示符
            lines = output.split('\n')
            cleaned_lines = []
            
            # 找到命令回显的位置并跳过它以及之前的行
            command_found_index = -1
            for i, line in enumerate(lines):
                if command in line:
                    command_found_index = i
                    break
            
            # 从命令回显之后开始收集输出
            start_index = command_found_index + 1 if command_found_index >= 0 else 0
            
            for i in range(start_index, len(lines)):
                line = lines[i].strip()
                # 跳过空行、命令回显行和提示符行
                if line and not re.match(r'^[A-Za-z0-9\-_]+[#>]', line) and command not in line:
                    # 移除分页提示
                    cleaned_line = re.sub(r'--More--.*$', '', line)
                    cleaned_line = re.sub(r'-- more --.*$', '', cleaned_line)
                    if cleaned_line.strip():  # 只添加非空行
                        cleaned_lines.append(lines[i])  # 保持原始格式，只是做选择性添加
            
            # 移除末尾的提示符行和分页提示
            while cleaned_lines and (re.match(r'^[A-Za-z0-9\-_]+[#>]', cleaned_lines[-1].strip()) or 
                                   "--More--" in cleaned_lines[-1] or 
                                   "-- more --" in cleaned_lines[-1]):
                cleaned_lines.pop()
            
            result = '\n'.join(cleaned_lines).strip()
            logger.debug(f"清理后的输出: {repr(result)}")
            return result
            
        except Exception as e:
            logger.error(f"执行命令 '{command}' 时发生错误: {str(e)}")
            raise Exception(f"执行命令失败: {str(e)}")

    def get_mac_table(self) -> List[Dict[str, Any]]:
        """获取MAC地址表"""
        try:
            # 确保在特权模式下执行命令
            if not self._enter_privileged_mode():
                raise Exception("无法进入特权模式")
            
            # 执行命令获取MAC地址表
            output = self.execute_command("show mac-address")
            
            mac_entries = []
            lines = output.split('\n')
            
            # 解析MAC地址表
            for line in lines:
                line = line.strip()
                # 匹配MAC地址表行 (例如: 0012.0001.0001   100     Gi0/1)
                # 或者 (例如: 100    0012.0001.0001    dynamic   Gi0/1)
                # 根据锐捷设备常见的MAC地址表格式进行解析
                match = re.match(r'^(\d+)\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+\w+\s+(\S+)$', line)
                if not match:
                    # 尝试另一种格式
                    match = re.match(r'^([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+(\d+)\s+(\S+)$', line)
                
                if match:
                    if len(match.groups()) == 3:
                        # 第一种格式: VLAN MAC TYPE INTERFACE
                        if match.group(1).isdigit():  # VLAN在第一列
                            vlan = int(match.group(1))
                            mac = match.group(2)
                            interface = match.group(3)
                        else:  # MAC在第一列
                            mac = match.group(1)
                            vlan = int(match.group(2))
                            interface = match.group(3)
                        
                        mac_entries.append({
                            "mac_address": mac,
                            "vlan": vlan,
                            "interface": interface
                        })
            
            logger.debug(f"获取锐捷设备MAC地址表成功，共 {len(mac_entries)} 条记录")
            return mac_entries
        except Exception as e:
            error_msg = f"获取锐捷设备MAC地址表失败: {str(e)}"
            logger.error(error_msg)
            return []

    def get_device_performance(self) -> Dict[str, Any]:
        """获取设备性能数据，包括CPU、内存使用率等"""
        try:
            # 确保在特权模式下执行命令
            if not self._enter_privileged_mode():
                raise Exception("无法进入特权模式")
            
            # 获取CPU使用率
            cpu_output = self.execute_command("show cpu")
            cpu_usage = 0
            
            # 解析CPU使用率，锐捷设备的输出格式可能类似：
            # CPU utilization for five seconds: 11% / 0% max, one minute: 12% / 0% max, five minutes: 10% / 0% max
            import re
            cpu_match = re.search(r'five seconds: (\d+)%', cpu_output)
            if cpu_match:
                cpu_usage = int(cpu_match.group(1))
            else:
                # 尝试其他可能的格式
                cpu_matches = re.findall(r'(\d+)%', cpu_output)
                if cpu_matches:
                    # 取第一个数字作为CPU使用率
                    cpu_usage = int(cpu_matches[0])
            
            # 获取内存使用率
            memory_output = self.execute_command("show memory")
            memory_usage = 0
            
            # 解析内存使用率，锐捷设备的输出格式可能类似：
            # Memory Using Percentage Is: 33%
            memory_match = re.search(r'Memory Using Percentage Is:\s*(\d+)%', memory_output)
            if memory_match:
                memory_usage = int(memory_match.group(1))
            else:
                # 尝试其他可能的格式，如 "MemUsage = 33%"
                memory_match = re.search(r'MemUsage\s*=\s*(\d+)%', memory_output)
                if memory_match:
                    memory_usage = int(memory_match.group(1))
                else:
                    # 再尝试其他的匹配模式
                    memory_matches = re.findall(r'(\d+)%', memory_output)
                    if memory_matches:
                        # 取第一个匹配项作为内存使用率
                        memory_usage = int(memory_matches[0])
            
            # 获取接口流量信息（可选）
            inbound_bandwidth = 0
            outbound_bandwidth = 0
            
            logger.info(f"获取锐捷设备性能数据成功 - CPU: {cpu_usage}%, 内存: {memory_usage}%")
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'inbound_bandwidth': inbound_bandwidth,
                'outbound_bandwidth': outbound_bandwidth
            }
        except Exception as e:
            logger.error(f"获取锐捷设备性能数据失败: {str(e)}")
            # 返回默认值
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'inbound_bandwidth': 0,
                'outbound_bandwidth': 0
            }
