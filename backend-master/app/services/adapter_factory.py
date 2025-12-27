from typing import Dict, Any
from app.adapters.base import BaseAdapter
from app.adapters.h3c import H3CAdapter
from app.adapters.huawei import HuaweiAdapter
from app.adapters.ruijie import RuijieAdapter
from app.adapters.snmp import SNMPAdapter


class AdapterFactory:
    """适配器工厂类，负责根据设备类型创建对应的适配器实例"""
    
    # 注册支持的设备类型和对应的适配器类
    _adapters = {
        'huawei': HuaweiAdapter,
        'h3c': H3CAdapter,
        'ruijie': RuijieAdapter,
        'snmp': SNMPAdapter
    }
    
    # 设备类型映射表，用于处理不同的设备类型表示方式
    _device_type_mapping = {
        'huawei': 'huawei',
        'h3c': 'h3c',
        'ruijie': 'ruijie',
        'snmp': 'snmp',
        'switch': 'snmp',  # 将switch映射到snmp适配器
        'router': 'snmp',  # 将router映射到snmp适配器
        'firewall': 'snmp'  # 将firewall映射到snmp适配器
    }
    
    @classmethod
    def create_adapter(cls, device_type: str, device_info: Dict[str, Any]) -> BaseAdapter:
        """
        根据设备类型创建对应的适配器实例
        
        Args:
            device_type: 设备类型
            device_info: 设备信息，包含IP、用户名、密码等
        
        Returns:
            对应的适配器实例
        
        Raises:
            ValueError: 如果设备类型不支持
        """
        # 标准化设备类型
        normalized_device_type = device_type.lower().strip()
        
        # 检查是否需要映射
        if normalized_device_type in cls._device_type_mapping:
            mapped_type = cls._device_type_mapping[normalized_device_type]
        else:
            mapped_type = normalized_device_type
        
        # 检查映射后的类型是否支持
        if mapped_type not in cls._adapters:
            supported_types = ', '.join(cls._adapters.keys())
            raise ValueError(f"不支持的设备类型: {device_type}，支持的设备类型有: {supported_types}")
        
        return cls._adapters[mapped_type](device_info)
    
    @classmethod
    def is_device_type_supported(cls, device_type: str) -> bool:
        """
        检查设备类型是否受支持
        
        Args:
            device_type: 设备类型
        
        Returns:
            是否支持
        """
        normalized_type = device_type.lower().strip()
        # 检查原始类型或映射后的类型是否支持
        return (normalized_type in cls._adapters) or (normalized_type in cls._device_type_mapping)
    
    @classmethod
    def get_supported_device_types(cls) -> list:
        """
        获取所有支持的设备类型列表
        
        Returns:
            支持的设备类型列表
        """
        return list(cls._adapters.keys()) + list(cls._device_type_mapping.keys())