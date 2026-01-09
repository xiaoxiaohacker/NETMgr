#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锐捷设备Trap解析测试脚本
用于验证锐捷设备告警解析功能
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.trap_parser import SNMPTrapParser
import json


def test_ruijie_port_link_change_trap():
    """测试锐捷端口链路状态变化Trap"""
    print("测试锐捷端口链路状态变化Trap...")
    
    # 示例Trap数据（基于您提供的数据）
    trap_example = {
        '1.3.6.1.2.1.1.3.0': '16692044',
        '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.4.1.4881.1.1.10.2.105.2.3',
        '1.3.6.1.4.1.4881.1.1.10.2.105.2.1.0': 'GigabitEthernet 0/25',
        '1.3.6.1.4.1.4881.1.1.10.2.105.2.2.0': 'EC140400241006'
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
    print(json.dumps(simple_alert, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")


def test_ruijie_arp_dos_attack_trap():
    """测试锐捷ARP DoS攻击Trap"""
    print("测试锐捷ARP DoS攻击Trap...")
    
    # 示例ARP DoS攻击Trap数据（基于您提供的数据）
    trap_example = {
        '1.3.6.1.2.1.1.3.0': '16694330',
        '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.4.1.4881.1.1.10.2.43.2.0.1',
        '1.3.6.1.4.1.4881.1.1.10.2.43.1.0.0': 'sub:ARP-DoS-ATTACK;status:2;se:3;sr:;smac:58696c047939;sport:0;svid:250;sifindex:26;dest:;dmac:;dport:0;proto:0;param:ARP scan from host<IP=N/A, MAC=5869.6c04.7939, port=Gi0/26, VLAN=250> was detected.;time:2026-1-7_13:52:26'
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
    print(json.dumps(simple_alert, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")


def test_ruijie_device_login_trap():
    """测试锐捷设备登录Trap"""
    print("测试锐捷设备登录Trap...")
    
    # 示例登录Trap数据（基于您提供的数据）
    trap_example = {
        '1.3.6.1.2.1.1.3.0': '16712483',
        '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.4.1.4881.1.1.10.2.87.1.1.0.1',
        '1.3.6.1.4.1.4881.1.1.10.2.87.1.1.3.0': '192.168.121.51',
        '1.3.6.1.4.1.4881.1.1.10.2.87.1.1.4.0': '1767794127'
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
    print(json.dumps(simple_alert, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")


def main():
    """主测试函数"""
    print("开始测试锐捷设备Trap解析功能...")
    print("="*50)
    
    test_ruijie_port_link_change_trap()
    test_ruijie_arp_dos_attack_trap()
    test_ruijie_device_login_trap()
    
    print("所有测试完成！")


if __name__ == "__main__":
    main()