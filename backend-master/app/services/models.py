from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.services.db import Base
from enum import Enum as PyEnum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # 增加长度以适应bcrypt哈希
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    devices = relationship("Device", back_populates="owner")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))  # 增加长度
    management_ip = Column(String(45), unique=True, index=True, nullable=False)  # IPv6最大长度为45
    vendor = Column(String(50), nullable=False)
    model = Column(String(100))
    os_version = Column(String(100))
    serial_number = Column(String(100))
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)  # 增加长度以适应加密密码
    enable_password = Column(String(255), nullable=True)  # 增加长度以适应加密密码
    port = Column(Integer, default=22)
    device_type = Column(String(50))
    location = Column(String(200))  # 增加长度
    status = Column(String(20), default="unknown")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 外键关系
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # 关系
    owner = relationship("User", back_populates="devices")
    configs = relationship("Config", back_populates="device", cascade="all, delete-orphan")
    interfaces = relationship("InterfaceStatus", back_populates="device", cascade="all, delete-orphan")
    logs = relationship("SystemLog", back_populates="device")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")

class InterfaceStatus(Base):
    __tablename__ = "interface_status"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    interface_name = Column(String(50), nullable=False)
    admin_status = Column(String(20))
    operational_status = Column(String(20))
    mac_address = Column(String(17))  # MAC地址格式 AA:BB:CC:DD:EE:FF
    connected_to_mac = Column(String(17))  # 连接的对端MAC地址
    ip_address = Column(String(45))  # 支持IPv6
    speed = Column(String(20))
    description = Column(String(255))  # 接口描述信息
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    device = relationship("Device", back_populates="interfaces")

# 为Device类添加关系引用（修复循环导入问题）
Device.interfaces = relationship("InterfaceStatus", back_populates="device", cascade="all, delete-orphan")

class Config(Base):
    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    filename = Column(String(255), nullable=False)  # 增加长度
    config = Column(Text, nullable=False)  # 使用Text类型存储长配置
    taken_by = Column(String(50), nullable=False)
    description = Column(String(500))  # 增加长度
    file_size = Column(Integer, default=0)  # 文件大小（字节）
    hash = Column(String(32))  # MD5哈希值
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    device = relationship("Device", back_populates="configs")

class CommandLog(Base):
    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    command = Column(Text, nullable=False)  # 使用Text类型存储长命令
    output = Column(Text)  # 使用Text类型存储命令输出
    executed_by = Column(String(50), nullable=False)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    device = relationship("Device")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # 告警类型: InterfaceDown, HighCPU, HighMemory等
    severity = Column(String(20), nullable=False)    # 严重性: Critical, Major, Minor, Warning
    message = Column(Text, nullable=False)           # 告警详细信息
    simple_details = Column(Text, nullable=True)     # 简化的告警详情（JSON格式）
    status = Column(String(20), default="New")       # 状态: New, Acknowledged, Resolved
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())  # 告警发生时间
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)          # 确认时间
    resolved_at = Column(DateTime(timezone=True), nullable=True)              # 解决时间
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True) # 确认人
    
    # 关系
    device = relationship("Device", back_populates="alerts")
    acknowledger = relationship("User")

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String(20), nullable=False)  # 日志级别: INFO, WARNING, ERROR, DEBUG
    module = Column(String(50), nullable=False)  # 模块名称
    message = Column(Text, nullable=False)  # 日志消息
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)  # 关联设备（可选）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 关联用户（可选）
    
    # 关系
    device = relationship("Device")
    user = relationship("User")

class TaskStatus(PyEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(PyEnum):
    CONFIG_BACKUP = "config_backup"
    DEVICE_INSPECTION = "device_inspection"
    FIRMWARE_UPGRADE = "firmware_upgrade"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    task_type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    result = Column(Text)  # 任务执行结果
    logs = Column(Text)    # 任务执行日志
    
    # 关系
    creator_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User")
    
    # 目标设备（多对多关系）
    target_devices = relationship("Device", secondary="task_devices")


class DeviceStatusHistory(Base):
    __tablename__ = "device_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    online_count = Column(Integer, nullable=False, default=0)
    offline_count = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    unknown_count = Column(Integer, nullable=False, default=0)
    
    # 索引时间戳以优化查询
    __table_args__ = (
        {'mysql_charset': 'utf8mb4'},
    )

class DevicePerformance(Base):
    __tablename__ = "device_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    cpu_usage = Column(Integer, nullable=True)  # CPU使用率百分比
    memory_usage = Column(Integer, nullable=True)  # 内存使用率百分比
    inbound_bandwidth = Column(Integer, nullable=True)  # 入站带宽使用量（KB/s）
    outbound_bandwidth = Column(Integer, nullable=True)  # 出站带宽使用量（KB/s）
    
    # 关系
    device = relationship("Device")
    
    # 索引时间戳以优化查询
    __table_args__ = (
        {'mysql_charset': 'utf8mb4'},
    )

# 任务与设备的关联表
task_devices = Table(
    "task_devices",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("device_id", Integer, ForeignKey("devices.id"), primary_key=True)
)

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)  # 设置项键名
    setting_value = Column(Text, nullable=False)  # 设置项值（JSON格式）
    description = Column(Text)  # 设置项描述
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # 更新时间
    
    __table_args__ = (
        {'mysql_charset': 'utf8mb4'},
    )
