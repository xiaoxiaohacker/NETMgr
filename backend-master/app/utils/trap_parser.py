#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNMP Trap解析工具
用于将原始OID数据转换为可读的告警信息
"""

import binascii
import logging
import struct
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SNMPTrapParser:
    """SNMP Trap解析器"""
    
    # 华为设备OID映射
    HUAWEI_OID_MAP = {
        '1.3.6.1.4.1.2011.5.25.123.2.6': 'IP地址冲突告警',
        '1.3.6.1.4.1.2011.5.25.123.1.28.1.0': '冲突MAC地址',
        '1.3.6.1.4.1.2011.5.25.123.1.28.2.0': '冲突接口',
        '1.3.6.1.4.1.2011.5.25.123.1.28.3.0': '冲突IP地址',
        '1.3.6.1.4.1.2011.5.25.123.1.28.4.0': 'VLAN ID',
        '1.3.6.1.4.1.2011.5.25.123.1.28.5.0': '冲突探测次数',
        '1.3.6.1.4.1.2011.5.25.123.1.28.6.0': '本地接口',
        '1.3.6.1.4.1.2011.5.25.123.1.28.7.0': '本地MAC地址',
        '1.3.6.1.4.1.2011.5.25.123.1.28.8.0': '本地VLAN ID',
        '1.3.6.1.4.1.2011.5.25.123.1.28.9.0': '本地检测次数',
        '1.3.6.1.4.1.2011.5.25.123.1.28.10.0': '告警描述'
    }
    
    # 标准OID映射
    STANDARD_OID_MAP = {
        '1.3.6.1.2.1.1.3.0': '系统运行时间',
        '1.3.6.1.6.3.1.1.4.1.0': '告警类型标识'
    }
    
    @classmethod
    def parse_trap(cls, trap_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析SNMP Trap数据
        
        Args:
            trap_data: 原始Trap数据，键为OID，值为对应的值
            
        Returns:
            解析后的告警信息
        """
        parsed_data = {}
        
        # 合并所有OID映射
        oid_map = {**cls.STANDARD_OID_MAP, **cls.HUAWEI_OID_MAP}
        
        for oid, value in trap_data.items():
            # 获取可读的OID名称
            readable_name = oid_map.get(oid, oid)
            
            # 特殊处理某些字段
            if oid == '1.3.6.1.4.1.2011.5.25.123.1.28.3.0':
                # IP地址需要特殊处理
                readable_value = cls._parse_ip_address(value)
            elif oid in ['1.3.6.1.4.1.2011.5.25.123.1.28.1.0', 
                         '1.3.6.1.4.1.2011.5.25.123.1.28.7.0']:
                # MAC地址需要特殊处理
                readable_value = cls._parse_mac_address(value)
            else:
                readable_value = value
                
            parsed_data[readable_name] = {
                'oid': oid,
                'raw_value': value,
                'readable_value': readable_value
            }
            
        return parsed_data
    
    @staticmethod
    def _parse_ip_address(hex_value: str) -> str:
        """
        解析IP地址（十六进制格式转点分十进制）
        
        Args:
            hex_value: 十六进制表示的IP地址
            
        Returns:
            点分十进制IP地址
        """
        try:
            # 移除可能的前缀并清理数据
            clean_hex = hex_value.replace('\\x', '').replace(' ', '')
            
            # 如果是类似"5439-df20-7a19"的格式，需要转换
            if '-' in clean_hex:
                # 这种格式可能是十六进制字符串的另一种表示
                parts = clean_hex.split('-')
                hex_string = ''.join(parts)
            else:
                hex_string = clean_hex
                
            # 确保长度是偶数
            if len(hex_string) % 2 != 0:
                hex_string = '0' + hex_string
                
            # 转换为字节
            if len(hex_string) >= 8:
                # 取前8个字符（4个字节）
                ip_bytes = bytes.fromhex(hex_string[:8])
                ip_parts = [str(b) for b in ip_bytes]
                return '.'.join(ip_parts)
            else:
                # 尝试其他方式解析
                # 如果看起来像正常的IP地址格式，直接返回
                ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
                if ip_pattern.match(hex_value):
                    return hex_value
                return f"无法解析的IP地址: {hex_value}"
        except Exception as e:
            logger.error(f"解析IP地址失败: {hex_value}, 错误: {e}")
            # 如果看起来像正常的IP地址格式，直接返回
            ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
            if ip_pattern.match(hex_value):
                return hex_value
            return f"解析失败: {hex_value}"
    
    @staticmethod
    def _parse_mac_address(hex_value: str) -> str:
        """
        解析MAC地址
        
        Args:
            hex_value: 十六进制表示的MAC地址
            
        Returns:
            标准MAC地址格式
        """
        try:
            # 尝试多种可能的格式
            if isinstance(hex_value, str):
                # 清理数据
                clean_value = hex_value.strip()
                
                # 处理类似"001a-a91f-a3f3"的格式
                if re.match(r'^[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}$', clean_value):
                    # 替换-为无字符，然后每两个字符添加一个冒号
                    clean_value = clean_value.replace('-', '')
                    mac_parts = [clean_value[i:i+2] for i in range(0, len(clean_value), 2)]
                    return ':'.join(mac_parts).upper()
                
                # 处理类似"001a:a91f:a3f3"的格式
                if re.match(r'^[0-9a-fA-F]{4}:[0-9a-fA-F]{4}:[0-9a-fA-F]{4}$', clean_value):
                    # 替换:为无字符，然后每两个字符添加一个冒号
                    clean_value = clean_value.replace(':', '')
                    mac_parts = [clean_value[i:i+2] for i in range(0, len(clean_value), 2)]
                    return ':'.join(mac_parts).upper()
                
                # 处理类似"00:1a:a9:1f:a3:f3"的格式
                if re.match(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', clean_value):
                    return clean_value.upper()
                
                # 如果包含非ASCII字符，可能是二进制数据的字符串表示
                try:
                    # 尝试解码为bytes再转为十六进制
                    if clean_value.startswith('\\x'):
                        # 处理\x格式的字符串
                        byte_values = []
                        parts = clean_value.split('\\x')[1:]  # 移除第一个空元素
                        for part in parts:
                            if part:
                                byte_values.append(int(part[:2], 16))
                        mac_bytes = bytes(byte_values)
                    else:
                        # 尝试直接转换
                        mac_bytes = clean_value.encode('latin1')
                        
                    # 格式化为标准MAC地址
                    mac_parts = [f"{b:02x}" for b in mac_bytes]
                    if len(mac_parts) >= 6:
                        return ':'.join(mac_parts[:6]).upper()
                    else:
                        return clean_value
                except Exception:
                    return clean_value
            else:
                return str(hex_value)
        except Exception as e:
            logger.error(f"解析MAC地址失败: {hex_value}, 错误: {e}")
            return f"解析失败: {hex_value}"

    @classmethod
    def format_alert_message(cls, parsed_data: Dict[str, Any]) -> str:
        """
        格式化告警消息为易读文本
        
        Args:
            parsed_data: 解析后的数据
            
        Returns:
            格式化的告警文本
        """
        # 查找告警类型
        alert_type = "未知告警"
        # 遍历所有键值对，查找告警类型标识
        for key, value in parsed_data.items():
            if key == '告警类型标识':
                alert_type = cls.HUAWEI_OID_MAP.get(str(value['raw_value']), '未知告警类型')
                break
        
        # 构建告警摘要
        summary_lines = [
            "=" * 50,
            f"SNMP Trap告警",
            "=" * 50,
            f"告警类型: {alert_type}",
            ""
        ]
        
        # 添加详细信息
        summary_lines.append("详细信息:")
        summary_lines.append("-" * 30)
        
        # 按重要性排序显示关键信息
        priority_fields = [
            '系统运行时间', '冲突接口', '冲突IP地址', '冲突MAC地址', 
            'VLAN ID', '本地接口', '本地MAC地址', '告警描述'
        ]
        
        # 先显示优先字段
        for field in priority_fields:
            if field in parsed_data:
                value_info = parsed_data[field]
                summary_lines.append(f"{field}: {value_info['readable_value']}")
        
        # 显示其他字段
        for field, value_info in parsed_data.items():
            if field not in priority_fields:
                summary_lines.append(f"{field}: {value_info['readable_value']}")
        
        summary_lines.extend([
            "",
            "-" * 50,
            "原始OID信息:",
            "-" * 50
        ])
        
        # 显示原始OID映射
        for field, value_info in parsed_data.items():
            summary_lines.append(f"{value_info['oid']} => {field}: {value_info['raw_value']}")
            
        summary_lines.append("=" * 50)
        
        return "\n".join(summary_lines)
    
    @classmethod
    def format_simple_alert(cls, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """
        格式化为简化的告警信息，便于前端展示
        
        Args:
            parsed_data: 解析后的数据
            
        Returns:
            简化格式的告警信息
        """
        # 查找告警类型
        alert_type = "未知告警"
        # 遍历所有键值对，查找告警类型标识
        for key, value in parsed_data.items():
            if key == '告警类型标识':
                alert_type = cls.HUAWEI_OID_MAP.get(str(value['raw_value']), '未知告警类型')
                break
        
        # 提取关键信息
        conflict_ip = ""
        conflict_mac = ""
        conflict_interface = ""
        vlan_id = ""
        description = ""
        
        for field, value_info in parsed_data.items():
            if '冲突IP地址' in field:
                conflict_ip = value_info['readable_value']
            elif '冲突MAC地址' in field:
                conflict_mac = value_info['readable_value']
            elif '冲突接口' in field:
                conflict_interface = value_info['readable_value']
            elif 'VLAN ID' in field:
                vlan_id = value_info['readable_value']
            elif '告警描述' in field:
                description = value_info['readable_value']
        
        return {
            "alert_type": alert_type,
            "conflict_ip": conflict_ip,
            "conflict_mac": conflict_mac,
            "conflict_interface": conflict_interface,
            "vlan_id": vlan_id,
            "description": description
        }


# 将测试函数移动到文件末尾
if __name__ == "__main__":
    def main():
        """测试函数"""
        # 示例Trap数据（你提供的数据）
        trap_example = {
            '1.3.6.1.2.1.1.3.0': '1875511436',
            '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.4.1.2011.5.25.123.2.6',
            '1.3.6.1.4.1.2011.5.25.123.1.28.1.0': 'À¨y6',
            '1.3.6.1.4.1.2011.5.25.123.1.28.2.0': 'GigabitEthernet0/0/25',
            '1.3.6.1.4.1.2011.5.25.123.1.28.3.0': '5439-df20-7a19',
            '1.3.6.1.4.1.2011.5.25.123.1.28.4.0': '1201',
            '1.3.6.1.4.1.2011.5.25.123.1.28.5.0': '0',
            '1.3.6.1.4.1.2011.5.25.123.1.28.6.0': 'GigabitEthernet0/0/25',
            '1.3.6.1.4.1.2011.5.25.123.1.28.7.0': '001a-a91f-a3f3',
            '1.3.6.1.4.1.2011.5.25.123.1.28.8.0': '1201',
            '1.3.6.1.4.1.2011.5.25.123.1.28.9.0': '0',
            '1.3.6.1.4.1.2011.5.25.123.1.28.10.0': 'Remote IP conflict'
        }
        
        # 解析Trap数据
        parser = SNMPTrapParser()
        parsed_data = parser.parse_trap(trap_example)
        
        # 格式化输出
        formatted_message = parser.format_alert_message(parsed_data)
        print(formatted_message)
        
        # 简化格式输出
        simple_alert = parser.format_simple_alert(parsed_data)
        print("\n简化格式:")
        print(simple_alert)
    
    main()