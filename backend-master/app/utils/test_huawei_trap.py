#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华为设备Trap解析测试脚本
用于验证华为设备告警解析功能
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.trap_parser import SNMPTrapParser
import json


def test_huawei_ip_conflict_trap():
    """测试华为IP地址冲突Trap"""
    print("测试华为IP地址冲突Trap...")
    
    # 示例Trap数据（基于您提供的数据）
    trap_example = {
        '1.3.6.1.2.1.1.3.0': '2158357121',
        '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.4.1.2011.5.25.123.2.6',
        '1.3.6.1.4.1.2011.5.25.123.1.28.1.0': '192.168.121.54',
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
    print(json.dumps(simple_alert, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")


def test_huawei_link_down_trap():
    """测试华为链路Down Trap"""
    print("测试华为链路Down Trap...")
    
    # 示例链路Down Trap数据（基于您提供的数据）
    trap_example = {
        '1.3.6.1.2.1.1.3.0': '2158250710',
        '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.6.3.1.1.5.5'  # 链路状态变化
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


def test_huawei_user_login_trap():
    """测试华为用户登录Trap"""
    print("测试华为用户登录Trap...")
    
    # 示例用户登录Trap数据（基于您提供的数据）
    trap_example = {
        '1.3.6.1.2.1.1.3.0': '2157657907',
        '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.4.1.2011.5.25.207.2.2',
        '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.2.34': 'admin',
        '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.3.34': '192.168.149.198',
        '1.3.6.1.4.1.2011.5.25.207.1.2.1.1.4.34': 'VTY0'
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
    print("开始测试华为设备Trap解析功能...")
    print("="*50)
    
    test_huawei_ip_conflict_trap()
    test_huawei_link_down_trap()
    test_huawei_user_login_trap()
    
    print("所有测试完成！")


if __name__ == "__main__":
    main()