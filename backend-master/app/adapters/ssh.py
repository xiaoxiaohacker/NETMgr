    def check_security_issues(self):
        """检查设备的安全问题"""
        try:
            if not self.connection:
                if not self.connect():
                    return ["无法连接到设备"]
            
            issues = []
            
            # 检查弱密码（示例）
            # 这里可以添加更复杂的检查逻辑
            weak_passwords = ["admin", "password", "123456", "default", "000000"]
            if self.device_info.get('password', '').lower() in weak_passwords:
                issues.append("使用了弱密码")
            
            # 检查默认配置
            output = self._execute_command("show running-config")
            if output:
                # 检查是否有未配置的SNMP
                if "snmp-server community" not in output.lower():
                    issues.append("未配置SNMP访问控制")
                
                # 检查是否有未使用的端口开放
                if "no shutdown" in output.lower():
                    # 这里可以添加更具体的检查逻辑
                    pass
                
                # 检查是否启用了服务密码恢复
                if "service password-recovery" in output.lower():
                    issues.append("启用了服务密码恢复功能")
            
            return issues
        except Exception as e:
            logger.error(f"检查安全问题时出错: {str(e)}")
            return [f"检查安全问题时出错: {str(e)}"]

    def check_config_compliance(self, config):
        """检查配置合规性"""
        try:
            issues = []
            
            # 检查是否包含合规性要求
            # 示例：检查是否配置了访问控制列表
            if "access-list" not in config.lower() and "ip access-list" not in config.lower():
                issues.append("未配置访问控制列表")
            
            # 检查日志配置
            if "logging" not in config.lower():
                issues.append("未配置日志记录")
            
            # 检查NTP配置
            if "ntp" not in config.lower():
                issues.append("未配置NTP时间同步")
            
            # 检查AAA配置
            if "aaa" not in config.lower():
                issues.append("未配置AAA认证")
            
            # 检查密码加密
            if "service password-encryption" not in config.lower():
                issues.append("未启用密码加密")
            
            return issues
        except Exception as e:
            logger.error(f"检查配置合规性时出错: {str(e)}")
            return [f"检查配置合规性时出错: {str(e)}"]