from typing import Dict, Any
import logging
from app.adapters.base import BaseAdapter
from app.adapters.h3c import H3CAdapter
from app.adapters.huawei import HuaweiAdapter
from app.adapters.ruijie import RuijieAdapter
from app.adapters.snmp import SNMPAdapter

logger = logging.getLogger(__name__)


class AdapterManager:
    """适配器管理器，负责根据设备厂商类型创建对应的适配器实例"""
    
    # 注册支持的厂商和对应的适配器类
    _adapters = {
        'huawei': HuaweiAdapter,
        'h3c': H3CAdapter,
        'ruijie': RuijieAdapter,
        'snmp': SNMPAdapter
    }
    
    @classmethod
    def get_adapter(cls, device_info: Dict[str, Any]) -> BaseAdapter:
        """
        根据设备信息获取对应的适配器实例
        
        Args:
            device_info: 设备信息，包含厂商、IP、用户名、密码等
        
        Returns:
            对应的适配器实例
        
        Raises:
            ValueError: 如果厂商不支持
        """
        vendor = device_info.get('vendor', '').lower()
        
        if vendor not in cls._adapters:
            supported_vendors = ', '.join(cls._adapters.keys())
            raise ValueError(f"不支持的厂商: {vendor}，支持的厂商有: {supported_vendors}")
        
        return cls._adapters[vendor](device_info)
    
    @classmethod
    def is_vendor_supported(cls, vendor: str) -> bool:
        """
        检查厂商是否受支持
        
        Args:
            vendor: 厂商名称
        
        Returns:
            是否支持
        """
        return vendor.lower() in cls._adapters
    
    @classmethod
    def get_supported_vendors(cls) -> list:
        """
        获取所有支持的厂商列表
        
        Returns:
            支持的厂商列表
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def register_adapter(cls, vendor: str, adapter_class: type) -> None:
        """
        注册新的适配器
        
        Args:
            vendor: 厂商名称
            adapter_class: 适配器类
        """
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError("适配器类必须继承自BaseAdapter")
        
        cls._adapters[vendor.lower()] = adapter_class
    
    @staticmethod
    def get_device_performance(device_info):
        """获取设备性能数据"""
        adapter = AdapterManager.get_adapter(device_info)
        try:
            return adapter.get_device_performance()
        except Exception as e:
            logger.error(f"获取设备性能数据失败: {str(e)}")
            # 返回默认值
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'inbound_bandwidth': 0,
                'outbound_bandwidth': 0
            }
        finally:
            if adapter:
                adapter.disconnect()
