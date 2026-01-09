from datetime import datetime
import re


class SNMPTrapParser:
    def __init__(self):
        # 定义OID映射表，包含华为、H3C和锐捷设备的OID
        self.oid_mapping = {
            # RFC 3418 MIB-II System Group OIDs
            '1.3.6.1.2.1.1.1.0': '设备描述(sysDescr)',
            '1.3.6.1.2.1.1.2.0': 'OID标识(sysObjectID)',
            '1.3.6.1.2.1.1.3.0': '系统运行时间(sysUptime)',
            '1.3.6.1.2.1.1.4.0': '系统联系人(sysContact)',
            '1.3.6.1.2.1.1.5.0': '系统名称(sysName)',
            '1.3.6.1.2.1.1.6.0': '系统位置(sysLocation)',
            
            # 标准TRAP OIDs
            '1.3.6.1.6.3.1.1.4.1.0': '告警类型标识(SNMPv2-MIB::snmpTrapOID.0)',
            '1.3.6.1.6.3.1.1.4.3.0': '告警类型标识(SNMPv2-MIB::snmpTrapEnterprise)',

            # 华为设备 OIDs
            '1.3.6.1.4.1.2011.5.25.123.1.28.1.0': '冲突MAC地址(hwEtherNetAddrConflictMacAddress)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.2.0': '冲突接口(hwEtherNetAddrConflictInterface)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.3.0': '冲突IP地址(hwEtherNetAddrConflictIpAddress)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.4.0': 'VLAN ID(hwEtherNetAddrConflictVlanId)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.5.0': '冲突探测次数(hwEtherNetAddrConflictDetectCount)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.6.0': '本地接口(hwEtherNetAddrConflictLocalInterface)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.7.0': '本地MAC地址(hwEtherNetAddrConflictLocalMacAddress)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.8.0': '本地VLAN ID(hwEtherNetAddrConflictLocalVlanId)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.9.0': '本地检测次数(hwEtherNetAddrConflictLocalDetectCount)',
            '1.3.6.1.4.1.2011.5.25.123.1.28.10.0': '告警描述(hwEtherNetAddrConflictDescr)',
            
            # H3C设备 OIDs
            '1.3.6.1.4.1.25506.4.1.1.1.1': 'H3C接口索引(hh3cIfIndex)',
            '1.3.6.1.4.1.25506.4.1.1.1.2': 'H3C接口名称(hh3cIfName)',
            '1.3.6.1.4.1.25506.4.1.1.1.3': 'H3C接口类型(hh3cIfType)',
            '1.3.6.1.4.1.25506.4.1.1.1.4': 'H3C接口状态(hh3cIfStatus)',
            '1.3.6.1.4.1.25506.4.1.1.1.5': 'H3C告警描述(hh3cAlarmDescription)',
            
            # 锐捷设备 OIDs
            '1.3.6.1.4.1.4881.1.1.10.2.105.2.1.0': '端口名称(ruijiePortName)',
            '1.3.6.1.4.1.4881.1.1.10.2.105.2.2.0': '端口MAC地址(ruijiePortMacAddress)',
            '1.3.6.1.4.1.4881.1.1.10.2.43.1.0.0': 'ARP攻击详细信息(ruijieArpAttackInfo)',
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.1.3.0': '登录IP地址(ruijieLoginIp)',
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.1.4.0': '登录用户ID(ruijieLoginUserId)',
            # 锐捷登录相关OIDs
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.2.2.0': '登录用户名(ruijieLoginUsername)',
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.2.3.0': '登录源IP(ruijieLoginSourceIp)',
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.2.6.0': '登录接口(ruijieLoginInterface)',
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.2.7.0': '登录会话ID(ruijieLoginSessionId)',
            
            # 标准接口相关 OIDs
            '1.3.6.1.2.1.2.2.1.1': '接口索引(ifIndex)',
            '1.3.6.1.2.1.2.2.1.2': '接口名称(ifDescr)',
            '1.3.6.1.2.1.2.2.1.7': '管理状态(ifAdminStatus)',
            '1.3.6.1.2.1.2.2.1.8': '操作状态(ifOperStatus)',
        }

        # 定义告警类型映射表
        self.alert_type_mapping = {
            # 华为IP冲突
            '1.3.6.1.4.1.2011.5.25.123.2.6': 'IP地址冲突告警',
            # 标准链路告警
            '1.3.6.1.6.3.1.1.5.3': '链路状态Down告警',      # Link Down
            '1.3.6.1.6.3.1.1.5.4': '链路状态Up告警',        # Link Up
            '1.3.6.1.6.3.1.1.5.5': '链路状态变化告警',      # Link Change
            # H3C链路告警
            '1.3.6.1.4.1.25506.2.4.1.2': 'H3C链路告警',
            # 华为用户登录
            '1.3.6.1.4.1.2011.5.25.207.2.2': '用户登录告警',  # User Login
            '1.3.6.1.4.1.2011.5.25.207.2.4': '用户登出告警',  # User Logout
            # 锐捷端口链路状态变化
            '1.3.6.1.4.1.4881.1.1.10.2.105.2.3': '端口链路状态变化告警',
            # 锐捷ARP DoS攻击
            '1.3.6.1.4.1.4881.1.1.10.2.43.2.0.1': 'ARP DoS攻击告警',
            # 锐捷登录事件
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.1.0.1': '设备登录事件告警',
            # 特定的锐捷登录事件OID
            '1.3.6.1.4.1.4881.1.1.10.2.87.1.2.0.3': '锐捷用户登录事件告警',
        }

    def parse_trap(self, trap_data):
        """解析SNMP Trap数据"""
        parsed_data = {
            'raw_data': trap_data.copy(),
            'parsed_fields': {},
            'alert_type': '未知告警类型',
            'sys_uptime': '',
            'severity': 'Warning',
            'alert_db_type': 'other'
        }

        # 获取告警类型OID
        alert_oid = trap_data.get('1.3.6.1.6.3.1.1.4.1.0', '')
        
        # 根据OID确定告警类型
        if alert_oid in self.alert_type_mapping:
            parsed_data['alert_type'] = self.alert_type_mapping[alert_oid]
            
            # 根据告警类型设定严重性
            if 'IP地址冲突' in parsed_data['alert_type']:
                parsed_data['severity'] = 'Critical'
                parsed_data['alert_db_type'] = 'ip_conflict'
            elif 'Down' in parsed_data['alert_type'] or '链路状态变化' in parsed_data['alert_type']:
                parsed_data['severity'] = 'Critical'
                parsed_data['alert_db_type'] = 'link_down'
            elif 'Up' in parsed_data['alert_type']:
                parsed_data['severity'] = 'Normal'
                parsed_data['alert_db_type'] = 'link_up'
            elif '登录' in parsed_data['alert_type'] or '登出' in parsed_data['alert_type']:
                parsed_data['severity'] = 'Info'
                parsed_data['alert_db_type'] = 'user_access'
            elif 'ARP' in parsed_data['alert_type']:
                parsed_data['severity'] = 'Critical'
                parsed_data['alert_db_type'] = 'arp_attack'
            elif '端口链路' in parsed_data['alert_type']:
                parsed_data['severity'] = 'Warning'
                parsed_data['alert_db_type'] = 'port_link_change'
        else:
            parsed_data['alert_type'] = '未知告警类型'

        # 解析各个字段
        for oid, value in trap_data.items():
            if oid in self.oid_mapping:
                field_name = self.oid_mapping[oid]
                parsed_data['parsed_fields'][field_name] = value
            else:
                # 尝试解析一些常见的未知OID
                if '.1.3.6.1.2.1.2.2.1.' in oid:
                    if '1.3.6.1.2.1.2.2.1.1' == oid:  # ifIndex
                        parsed_data['parsed_fields']['接口索引'] = value
                    elif '1.3.6.1.2.1.2.2.1.8' == oid:  # ifOperStatus
                        status_map = {'1': 'up', '2': 'down', '3': 'testing'}
                        parsed_data['parsed_fields']['接口状态'] = status_map.get(value, f'unknown({value})')
                    else:
                        parsed_data['parsed_fields'][f'未知接口相关OID({oid})'] = value
                else:
                    parsed_data['parsed_fields'][f'未知OID({oid})'] = value

        # 获取系统运行时间
        parsed_data['sys_uptime'] = parsed_data['parsed_fields'].get('系统运行时间(sysUptime)', '')

        return parsed_data

    def format_alert_message(self, parsed_data):
        """格式化告警消息"""
        message = []
        message.append("SNMP Trap告警")
        message.append("=" * 48)
        message.append(f"告警类型: {parsed_data['alert_type']}")
        message.append("")
        message.append("详细信息:")
        message.append("-" * 30)
        
        # 根据告警类型添加特定字段
        if parsed_data['alert_type'] == 'IP地址冲突告警':
            if '冲突接口(hwEtherNetAddrConflictInterface)' in parsed_data['parsed_fields']:
                message.append(f"冲突接口: {parsed_data['parsed_fields']['冲突接口(hwEtherNetAddrConflictInterface)']}")
            if '冲突IP地址(hwEtherNetAddrConflictIpAddress)' in parsed_data['parsed_fields']:
                # 解码IP地址
                ip_str = self.decode_ip_address(parsed_data['parsed_fields']['冲突IP地址(hwEtherNetAddrConflictIpAddress)'])
                message.append(f"冲突IP地址: {ip_str}")
            if '冲突MAC地址(hwEtherNetAddrConflictMacAddress)' in parsed_data['parsed_fields']:
                mac_str = self.decode_mac_address(parsed_data['parsed_fields']['冲突MAC地址(hwEtherNetAddrConflictMacAddress)'])
                message.append(f"冲突MAC地址: {mac_str}")
            if 'VLAN ID(hwEtherNetAddrConflictVlanId)' in parsed_data['parsed_fields']:
                message.append(f"VLAN ID: {parsed_data['parsed_fields']['VLAN ID(hwEtherNetAddrConflictVlanId)']}")
            if '本地接口(hwEtherNetAddrConflictLocalInterface)' in parsed_data['parsed_fields']:
                message.append(f"本地接口: {parsed_data['parsed_fields']['本地接口(hwEtherNetAddrConflictLocalInterface)']}")
            if '本地MAC地址(hwEtherNetAddrConflictLocalMacAddress)' in parsed_data['parsed_fields']:
                local_mac_str = self.decode_mac_address(parsed_data['parsed_fields']['本地MAC地址(hwEtherNetAddrConflictLocalMacAddress)'])
                message.append(f"本地MAC地址: {local_mac_str}")
            if '告警描述(hwEtherNetAddrConflictDescr)' in parsed_data['parsed_fields']:
                message.append(f"告警描述: {parsed_data['parsed_fields']['告警描述(hwEtherNetAddrConflictDescr)']}")
            if '冲突探测次数(hwEtherNetAddrConflictDetectCount)' in parsed_data['parsed_fields']:
                message.append(f"冲突探测次数: {parsed_data['parsed_fields']['冲突探测次数(hwEtherNetAddrConflictDetectCount)']}")
            if '本地VLAN ID(hwEtherNetAddrConflictLocalVlanId)' in parsed_data['parsed_fields']:
                message.append(f"本地VLAN ID: {parsed_data['parsed_fields']['本地VLAN ID(hwEtherNetAddrConflictLocalVlanId)']}")
            if '本地检测次数(hwEtherNetAddrConflictLocalDetectCount)' in parsed_data['parsed_fields']:
                message.append(f"本地检测次数: {parsed_data['parsed_fields']['本地检测次数(hwEtherNetAddrConflictLocalDetectCount)']}")
        elif parsed_data['alert_type'] == '端口链路状态变化告警':
            if '端口名称(ruijiePortName)' in parsed_data['parsed_fields']:
                message.append(f"端口名称: {parsed_data['parsed_fields']['端口名称(ruijiePortName)']}")
            if '端口MAC地址(ruijiePortMacAddress)' in parsed_data['parsed_fields']:
                message.append(f"端口MAC地址: {parsed_data['parsed_fields']['端口MAC地址(ruijiePortMacAddress)']}")
        elif parsed_data['alert_type'] == 'ARP DoS攻击告警':
            if 'ARP攻击详细信息(ruijieArpAttackInfo)' in parsed_data['parsed_fields']:
                arp_info = parsed_data['parsed_fields']['ARP攻击详细信息(ruijieArpAttackInfo)']
                message.append(f"ARP攻击详细信息: {self.parse_arp_attack_info(arp_info)}")
        elif parsed_data['alert_type'] == '设备登录事件告警' or parsed_data['alert_type'] == '锐捷用户登录事件告警':
            if '登录IP地址(ruijieLoginIp)' in parsed_data['parsed_fields']:
                message.append(f"登录IP地址: {parsed_data['parsed_fields']['登录IP地址(ruijieLoginIp)']}")
            if '登录用户ID(ruijieLoginUserId)' in parsed_data['parsed_fields']:
                message.append(f"登录用户ID: {parsed_data['parsed_fields']['登录用户ID(ruijieLoginUserId)']}")
            # 新增锐捷登录详细信息
            if '登录用户名(ruijieLoginUsername)' in parsed_data['parsed_fields']:
                message.append(f"登录用户名: {parsed_data['parsed_fields']['登录用户名(ruijieLoginUsername)']}")
            if '登录源IP(ruijieLoginSourceIp)' in parsed_data['parsed_fields']:
                message.append(f"登录源IP: {parsed_data['parsed_fields']['登录源IP(ruijieLoginSourceIp)']}")
            if '登录接口(ruijieLoginInterface)' in parsed_data['parsed_fields']:
                message.append(f"登录接口: {parsed_data['parsed_fields']['登录接口(ruijieLoginInterface)']}")
            if '登录会话ID(ruijieLoginSessionId)' in parsed_data['parsed_fields']:
                message.append(f"登录会话ID: {parsed_data['parsed_fields']['登录会话ID(ruijieLoginSessionId)']}")
        elif parsed_data['alert_type'] == '链路状态Down告警':
            if '接口索引' in parsed_data['parsed_fields']:
                message.append(f"接口索引: {parsed_data['parsed_fields']['接口索引']}")
            if '接口名称(ifDescr)' in parsed_data['parsed_fields']:
                message.append(f"接口名称: {parsed_data['parsed_fields']['接口名称(ifDescr)']}")
            if '接口状态' in parsed_data['parsed_fields']:
                message.append(f"接口状态: {parsed_data['parsed_fields']['接口状态']}")
        elif parsed_data['alert_type'] == '链路状态Up告警':
            if '接口索引' in parsed_data['parsed_fields']:
                message.append(f"接口索引: {parsed_data['parsed_fields']['接口索引']}")
            if '接口名称(ifDescr)' in parsed_data['parsed_fields']:
                message.append(f"接口名称: {parsed_data['parsed_fields']['接口名称(ifDescr)']}")
            if '接口状态' in parsed_data['parsed_fields']:
                message.append(f"接口状态: {parsed_data['parsed_fields']['接口状态']}")
        elif parsed_data['alert_type'] == '链路状态变化告警':
            if '接口索引' in parsed_data['parsed_fields']:
                message.append(f"接口索引: {parsed_data['parsed_fields']['接口索引']}")
            if '接口名称(ifDescr)' in parsed_data['parsed_fields']:
                message.append(f"接口名称: {parsed_data['parsed_fields']['接口名称(ifDescr)']}")
            if '接口状态' in parsed_data['parsed_fields']:
                message.append(f"接口状态: {parsed_data['parsed_fields']['接口状态']}")
        elif parsed_data['alert_type'] == '用户登录告警':
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.2.34' in parsed_data['raw_data']:
                message.append(f"用户名: {parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.2.34']}")
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.3.34' in parsed_data['raw_data']:
                message.append(f"登录IP: {parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.3.34']}")
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.4.34' in parsed_data['raw_data']:
                message.append(f"登录接口: {parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.4.34']}")
        elif parsed_data['alert_type'] == '用户登出告警':
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.2.34' in parsed_data['raw_data']:
                message.append(f"用户名: {parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.2.34']}")
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.3.34' in parsed_data['raw_data']:
                message.append(f"登出IP: {parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.3.34']}")
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.4.34' in parsed_data['raw_data']:
                message.append(f"登出接口: {parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.4.34']}")
        else:
            # 通用字段显示
            if '系统运行时间(sysUptime)' in parsed_data['parsed_fields']:
                message.append(f"系统运行时间: {parsed_data['parsed_fields']['系统运行时间(sysUptime)']}")
            if '告警类型标识(SNMPv2-MIB::snmpTrapOID.0)' in parsed_data['parsed_fields']:
                message.append(f"告警类型标识: {parsed_data['parsed_fields']['告警类型标识(SNMPv2-MIB::snmpTrapOID.0)']}")

        message.append(f"告警类型标识: {parsed_data['raw_data'].get('1.3.6.1.6.3.1.1.4.1.0', 'N/A')}")

        message.append("")
        message.append("-" * 50)
        message.append("原始OID信息:")
        message.append("-" * 50)
        for oid, value in parsed_data['raw_data'].items():
            field_name = self.oid_mapping.get(oid, oid)
            message.append(f"{oid} => {field_name}: {value}")

        message.append("=" * 48)

        return "\n".join(message)

    def decode_ip_address(self, ip_hex):
        """解码IP地址十六进制表示"""
        try:
            # 如果是十六进制字符串格式，转换为IP地址
            if isinstance(ip_hex, str) and len(ip_hex) >= 8:
                # 移除可能的前缀和特殊字符
                clean_hex = re.sub(r'[^0-9a-fA-F]', '', ip_hex)
                if len(clean_hex) >= 8:
                    ip_parts = [str(int(clean_hex[i:i+2], 16)) for i in range(0, 8, 2)]
                    return ".".join(ip_parts)
        except:
            pass
        return ip_hex

    def decode_mac_address(self, mac_hex):
        """解码MAC地址十六进制表示"""
        try:
            # 如果是十六进制字符串格式，转换为MAC地址
            if isinstance(mac_hex, str):
                # 移除可能的前缀和特殊字符
                clean_hex = re.sub(r'[^0-9a-fA-F]', '', mac_hex)
                if len(clean_hex) >= 12:
                    mac_parts = [clean_hex[i:i+2] for i in range(0, 12, 2)]
                    return ":".join([f"{part.upper()}" for part in mac_parts])
        except:
            pass
        return mac_hex

    def parse_arp_attack_info(self, arp_info):
        """解析锐捷ARP攻击信息"""
        try:
            # ARP攻击信息格式类似于:
            # sub:ARP-DoS-ATTACK;status:2;se:3;sr:;smac:58696c047939;sport:0;svid:250;sifindex:26;dest:;dmac:;dport:0;proto:0;param:ARP scan from host<IP=N/A, MAC=5869.6c04.7939, port=Gi0/26, VLAN=250> was detected.;time:2026-1-7_13:52:26
            parts = arp_info.split(';')
            result = []
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    if key == 'sub':
                        result.append(f"子系统: {value}")
                    elif key == 'status':
                        status_desc = {'1': '开始', '2': '结束'}
                        result.append(f"状态: {status_desc.get(value, value)}")
                    elif key == 'se':
                        se_desc = {'3': '严重', '2': '警告', '1': '提示'}
                        result.append(f"严重性: {se_desc.get(value, value)}")
                    elif key == 'sr':
                        if value:
                            result.append(f"源IP: {value}")
                    elif key == 'smac':
                        if value:
                            result.append(f"源MAC: {self.format_mac_for_display(value)}")
                    elif key == 'sport':
                        if value and value != '0':
                            result.append(f"源端口: {value}")
                    elif key == 'svid':
                        if value and value != '0':
                            result.append(f"源VLAN ID: {value}")
                    elif key == 'sifindex':
                        if value and value != '0':
                            result.append(f"源接口索引: {value}")
                    elif key == 'param':
                        result.append(f"描述: {value}")
                    elif key == 'time':
                        result.append(f"时间: {value}")
            return "\n".join(result)
        except:
            return arp_info

    def format_mac_for_display(self, mac_value):
        """格式化MAC地址用于显示"""
        try:
            if len(mac_value) == 12:  # 标准12位MAC地址
                return f"{mac_value[:4]}.{mac_value[4:8]}.{mac_value[8:12]}"
        except:
            pass
        return mac_value

    def format_simple_alert(self, parsed_data):
        """格式化简化告警信息，用于数据库存储"""
        simple_info = {
            "alert_type": parsed_data['alert_type'],
            "conflict_ip": "",  # IP地址冲突告警用
            "conflict_mac": "", # IP地址冲突告警用
            "conflict_interface": "", # IP地址冲突告警用
            "vlan_id": "",      # IP地址/VLAN相关告警用
            "description": "",  # 描述信息
            "login_username": "", # 登录相关告警用
            "login_ip": "",     # 登录相关告警用
            "login_interface": "", # 登录相关告警用
            "interface_name": "", # 接口相关告警用
            "interface_status": "", # 接口状态告警用
            "management_status": "", # 管理状态告警用
            "sys_uptime": parsed_data['sys_uptime'], # 系统运行时间
            "ruijie_port_name": "", # 锐捷端口名称
            "ruijie_port_mac": "",  # 锐捷端口MAC
            "ruijie_attack_info": "", # 锐捷攻击信息
            "ruijie_login_ip": "",    # 锐捷登录IP
            "ruijie_login_user_id": "", # 锐捷登录用户ID
            "ruijie_login_username": "", # 锐捷登录用户名
            "ruijie_login_source_ip": "", # 锐捷登录源IP
            "ruijie_login_interface": "", # 锐捷登录接口
            "ruijie_login_session_id": "" # 锐捷登录会话ID
        }

        # 根据不同的告警类型提取相应信息
        if parsed_data['alert_type'] == 'IP地址冲突告警':
            if '冲突接口(hwEtherNetAddrConflictInterface)' in parsed_data['parsed_fields']:
                simple_info["conflict_interface"] = parsed_data['parsed_fields']['冲突接口(hwEtherNetAddrConflictInterface)']
            if '冲突IP地址(hwEtherNetAddrConflictIpAddress)' in parsed_data['parsed_fields']:
                simple_info["conflict_ip"] = self.decode_ip_address(parsed_data['parsed_fields']['冲突IP地址(hwEtherNetAddrConflictIpAddress)'])
            if '冲突MAC地址(hwEtherNetAddrConflictMacAddress)' in parsed_data['parsed_fields']:
                simple_info["conflict_mac"] = self.decode_mac_address(parsed_data['parsed_fields']['冲突MAC地址(hwEtherNetAddrConflictMacAddress)'])
            if 'VLAN ID(hwEtherNetAddrConflictVlanId)' in parsed_data['parsed_fields']:
                simple_info["vlan_id"] = parsed_data['parsed_fields']['VLAN ID(hwEtherNetAddrConflictVlanId)']
            if '告警描述(hwEtherNetAddrConflictDescr)' in parsed_data['parsed_fields']:
                simple_info["description"] = parsed_data['parsed_fields']['告警描述(hwEtherNetAddrConflictDescr)']

        elif parsed_data['alert_type'] == '用户登录告警' or parsed_data['alert_type'] == '用户登出告警':
            # 华为设备登录信息
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.2.34' in parsed_data['raw_data']:
                simple_info["login_username"] = parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.2.34']
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.3.34' in parsed_data['raw_data']:
                simple_info["login_ip"] = parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.3.34']
            if '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.4.34' in parsed_data['raw_data']:
                simple_info["login_interface"] = parsed_data['raw_data']['1.3.6.1.4.1.2011.5.25.207.1.2.1.1.4.34']

        elif parsed_data['alert_type'] == '链路状态Down告警' or parsed_data['alert_type'] == '链路状态Up告警' or parsed_data['alert_type'] == '链路状态变化告警':
            if '接口名称(ifDescr)' in parsed_data['parsed_fields']:
                simple_info["interface_name"] = parsed_data['parsed_fields']['接口名称(ifDescr)']
            if '接口状态' in parsed_data['parsed_fields']:
                simple_info["interface_status"] = parsed_data['parsed_fields']['接口状态']
            if '管理状态(ifAdminStatus)' in parsed_data['parsed_fields']:
                simple_info["management_status"] = parsed_data['parsed_fields']['管理状态(ifAdminStatus)']

        elif parsed_data['alert_type'] == '端口链路状态变化告警':
            if '端口名称(ruijiePortName)' in parsed_data['parsed_fields']:
                simple_info["ruijie_port_name"] = parsed_data['parsed_fields']['端口名称(ruijiePortName)']
            if '端口MAC地址(ruijiePortMacAddress)' in parsed_data['parsed_fields']:
                simple_info["ruijie_port_mac"] = parsed_data['parsed_fields']['端口MAC地址(ruijiePortMacAddress)']

        elif parsed_data['alert_type'] == 'ARP DoS攻击告警':
            if 'ARP攻击详细信息(ruijieArpAttackInfo)' in parsed_data['parsed_fields']:
                arp_info = parsed_data['parsed_fields']['ARP攻击详细信息(ruijieArpAttackInfo)']
                simple_info["ruijie_attack_info"] = self.parse_arp_attack_info(arp_info)
                
                # 从ARP信息中提取有用信息
                parts = arp_info.split(';')
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        if key == 'sr' and value:  # 源IP
                            simple_info["conflict_ip"] = value
                        elif key == 'smac' and value:  # 源MAC
                            simple_info["conflict_mac"] = self.format_mac_for_display(value)
                        elif key == 'svid' and value and value != '0':  # VLAN ID
                            simple_info["vlan_id"] = value

        elif parsed_data['alert_type'] == '设备登录事件告警' or parsed_data['alert_type'] == '锐捷用户登录事件告警':
            if '登录IP地址(ruijieLoginIp)' in parsed_data['parsed_fields']:
                simple_info["ruijie_login_ip"] = parsed_data['parsed_fields']['登录IP地址(ruijieLoginIp)']
            if '登录用户ID(ruijieLoginUserId)' in parsed_data['parsed_fields']:
                simple_info["ruijie_login_user_id"] = parsed_data['parsed_fields']['登录用户ID(ruijieLoginUserId)']
            if '登录用户名(ruijieLoginUsername)' in parsed_data['parsed_fields']:
                simple_info["ruijie_login_username"] = parsed_data['parsed_fields']['登录用户名(ruijieLoginUsername)']
            if '登录源IP(ruijieLoginSourceIp)' in parsed_data['parsed_fields']:
                simple_info["ruijie_login_source_ip"] = parsed_data['parsed_fields']['登录源IP(ruijieLoginSourceIp)']
            if '登录接口(ruijieLoginInterface)' in parsed_data['parsed_fields']:
                simple_info["ruijie_login_interface"] = parsed_data['parsed_fields']['登录接口(ruijieLoginInterface)']
            if '登录会话ID(ruijieLoginSessionId)' in parsed_data['parsed_fields']:
                simple_info["ruijie_login_session_id"] = parsed_data['parsed_fields']['登录会话ID(ruijieLoginSessionId)']

        return simple_info