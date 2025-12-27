import json
import os
from typing import Dict, Any

# 默认SNMP Trap配置
DEFAULT_SNMP_CONFIG = {
    "trap_listen_address": "0.0.0.0",
    "trap_listen_port": 162,
    "community_strings": ["public"],
    "allowed_hosts": []
}

# 配置文件路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "snmp_config.json")

def get_snmp_config() -> Dict[str, Any]:
    """
    获取SNMP配置
    
    Returns:
        SNMP配置字典
    """
    # 检查配置文件是否存在
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保所有必需的键都存在
                for key, value in DEFAULT_SNMP_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"读取SNMP配置文件失败: {e}")
    
    # 返回默认配置
    return DEFAULT_SNMP_CONFIG

def save_snmp_config(config: Dict[str, Any]) -> bool:
    """
    保存SNMP配置到文件
    
    Args:
        config: SNMP配置字典
        
    Returns:
        是否保存成功
    """
    try:
        # 确保配置目录存在
        config_dir = os.path.dirname(CONFIG_FILE_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # 保存配置到文件
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存SNMP配置文件失败: {e}")
        return False

def update_snmp_config(new_config: Dict[str, Any]) -> bool:
    """
    更新SNMP配置
    
    Args:
        new_config: 新的SNMP配置
        
    Returns:
        是否更新成功
    """
    try:
        # 获取当前配置
        current_config = get_snmp_config()
        
        # 更新配置
        current_config.update(new_config)
        
        # 保存配置
        return save_snmp_config(current_config)
    except Exception as e:
        print(f"更新SNMP配置失败: {e}")
        return False