from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr

# 定义用户角色枚举
class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"

# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

# 用户相关模型
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=100)
    is_active: Optional[bool] = True
    role: Optional[UserRole] = UserRole.OPERATOR  # 添加角色字段，默认为操作员
    created_at: Optional[datetime] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=10)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# 设备相关模型
class DeviceBase(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    management_ip: str = Field(..., max_length=50)
    vendor: str = Field(..., max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    username: str = Field(..., max_length=50)
    port: Optional[int] = 22
    device_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = "unknown"

class DeviceCreate(DeviceBase):
    password: str
    enable_password: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    management_ip: Optional[str] = Field(None, max_length=50)
    vendor: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = None
    enable_password: Optional[str] = None
    port: Optional[int] = None
    device_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None

class DeviceOut(DeviceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 配置相关模型
class ConfigBase(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    taken_by: Optional[str] = Field(None, max_length=50)

class ConfigCreate(ConfigBase):
    device_id: int
    config: Optional[str] = None  # 配置内容，可选，系统可以自动从设备获取

class ConfigOut(ConfigBase):
    id: int
    device_id: int
    filename: str
    file_size: int
    hash: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# 接口状态模型
class InterfaceStatusBase(BaseModel):
    interface_name: str = Field(..., max_length=100)
    admin_status: Optional[str] = None
    operational_status: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    speed: Optional[str] = None
    description: Optional[str] = None

class InterfaceStatusCreate(InterfaceStatusBase):
    device_id: int

class InterfaceStatusOut(InterfaceStatusBase):
    id: int
    device_id: int
    last_seen: datetime

    class Config:
        from_attributes = True

# 命令执行模型
class CommandRequest(BaseModel):
    command: str
    session_token: Optional[str] = None  # 添加会话令牌字段

class CommandResponse(BaseModel):
    command: str
    output: str
    success: bool
    executed_at: datetime
    session_token: Optional[str] = None  # 添加会话令牌字段

# 批量操作模型
class BulkDeviceCreate(BaseModel):
    devices: List[DeviceCreate]

# 系统设置模型
class SystemSettingsBase(BaseModel):
    setting_key: str
    setting_value: str
    description: Optional[str] = None

class SystemSettingsCreate(SystemSettingsBase):
    pass

class SystemSettingsUpdate(BaseModel):
    setting_value: str
    description: Optional[str] = None

class SystemSettingsOut(SystemSettingsBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

# 专门的设置项模型
class BasicSettings(BaseModel):
    systemName: str
    description: str
    language: str
    timezone: str

class ScanSettings(BaseModel):
    enabled: bool
    interval: int
    ipRange: str
    ports: str
    vendors: List[str]

class NotificationSettings(BaseModel):
    emailEnabled: bool
    smtpServer: Optional[str] = None
    smtpPort: Optional[int] = None
    smtpUsername: Optional[str] = None
    smtpPassword: Optional[str] = None
    senderEmail: Optional[str] = None
    recipients: Optional[str] = None
    smsEnabled: bool
    smsGateway: Optional[str] = None
    smsApiKey: Optional[str] = None
    smsSignature: Optional[str] = None
