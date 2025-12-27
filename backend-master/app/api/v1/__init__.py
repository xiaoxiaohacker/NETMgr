# 导出各个模块的router
from .auth import router as auth_router
from .devices import router as devices_router
from .dashboard import router as dashboard_router
from .device_stats import router as device_stats_router
from .alerts import router as alerts_router
from .tasks import router as tasks_router
from .logs import router as logs_router
from .settings import router as settings_router
from .topology import router as topology_router
from .snmp import router as snmp_router
from .config_backup_tasks import router as config_backup_router
from .users import router as users_router  # 添加用户管理路由

__all__ = [
    "auth_router",
    "devices_router", 
    "dashboard_router",
    "tasks_router",
    "device_stats_router",
    "alerts_router",
    "logs_router",  # 添加日志路由
    "settings_router",  # 添加系统设置路由
    "topology_router",  # 添加网络拓扑路由
    "snmp_router",
    "config_backup_router",
    "users_router"  # 导出用户管理路由
]