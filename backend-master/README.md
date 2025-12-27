# NetMgr 交换机管理系统

## 项目介绍
NetMgr是一个基于FastAPI框架开发的交换机管理后端系统，主要用于管理华为、华三、锐捷等厂商的网络交换机设备。系统提供了统一的API接口，实现了对不同厂商交换机的统一管理和监控。

## 主要功能
- 用户认证系统（注册、登录、JWT认证）
- 设备管理（添加、查询、更新、删除设备）
- 设备信息获取（型号、版本、序列号等）
- 接口状态监控
- 配置管理（查看、保存配置）
- 命令执行（在设备上执行任意命令）
- 异步任务处理（配置备份、批量操作等，可选功能）
- 系统日志管理
- 系统设置管理
- 网络拓扑管理

## 技术栈
- **Web框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy
- **认证**: JWT (python-jose) + PassLib
- **网络设备连接**: Netmiko
- **任务队列**: Celery + Redis（可选）
- **容器化**: Docker

## 项目结构
```
app/
├── adapters/          # 交换机适配器（不同厂商的实现）
│   ├── base.py        # 适配器基类
│   ├── huawei.py      # 华为交换机适配器
│   ├── h3c.py         # 华三交换机适配器
│   ├── ruijie.py      # 锐捷交换机适配器
│   └── snmp.py        # SNMP适配器
├── api/               # API路由
│   └── v1/            # v1版本API
│       ├── auth.py    # 认证相关接口
│       ├── devices.py # 设备管理相关接口
│       ├── alerts.py      # 告警相关API接口
│       ├── dashboard.py   # 仪表盘相关API接口
│       ├── device_stats.py# 设备统计相关API接口
│       ├── logs.py        # 日志管理相关API接口
│       ├── settings.py    # 系统设置相关API接口
│       ├── topology.py    # 网络拓扑相关API接口
│       ├── tasks.py       # 异步任务相关API接口
│       ├── users.py       # 用户管理相关API接口
│       └── websocket.py   # WebSocket相关API接口
├── models/            # 数据库模型
├── schemas/           # Pydantic数据模型
├── services/          # 业务逻辑层
│   ├── adapter_manager.py  # 适配器管理器
│   ├── auth.py        # 认证服务
│   ├── config.py      # 配置信息
│   ├── db.py          # 数据库连接
│   ├── encryption.py  # 数据加密服务
│   ├── models.py      # 服务层数据模型
│   ├── device_status_checker.py  # 设备状态检查器
│   └── snmp_trap_listener.py   # SNMP Trap监听器
├── main.py            # 应用程序入口
├── scheduler.py       # 任务调度器
└── worker.py          # Celery Worker启动文件
```

## 安装和部署

### 环境要求
- Python 3.8+
- MySQL 5.7+ 或 MariaDB 10.2+
- Redis (可选，用于异步任务)
- Node.js 16+ (前端开发)

### 本地开发

#### 1. 克隆项目代码
```bash
git clone <repository-url>
cd backend-master
```

#### 2. 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# Windows激活虚拟环境
venv\Scripts\activate

# Linux/Mac激活虚拟环境
source venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
创建 `.env` 文件，配置数据库连接信息：
```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/netmgr
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 5. 初始化数据库
```bash
# 直接运行Python脚本创建表
python -c "
from app.services.db import engine
from app.services.models import Base
Base.metadata.create_all(bind=engine)
print('数据库表创建成功')
"
```

#### 6. 启动应用
```bash
# 开发模式启动（支持热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用启动脚本
python start_app.py
```

#### 7. 启动异步任务处理器（可选）
```bash
# 启动Celery Worker
python start_worker.py
```

### Docker部署

使用docker-compose一键部署：
```bash
docker-compose up -d
```

### 生产环境部署

#### 1. 使用Gunicorn部署
```bash
# 安装gunicorn
pip install gunicorn

# 启动应用
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 前端开发指南

### 环境要求
- Node.js 16+
- npm 或 yarn

### 项目设置
```bash
cd frontend
npm install
```

### 开发环境
```bash
# 启动开发服务器
npm run dev

# 默认访问地址: http://localhost:5173
```

### 生产构建
```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 前端代理配置
在开发环境中，Vite配置已将`/api`请求代理到后端服务（默认为 http://127.0.0.1:8000），确保开发环境下的API调用正常工作。

## API文档

启动应用后，访问以下地址获取API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目配置

### 数据库配置
在 `app/services/config.py` 中配置数据库连接信息，支持MySQL和SQLite。

### 认证配置
- JWT令牌过期时间可在环境变量中配置
- 密钥长度至少32位，建议使用随机生成的密钥

### 设备适配器
系统支持多种厂商设备，包括：
- 华为 (Huawei)
- 华三 (H3C) 
- 锐捷 (Ruijie)
- SNMP设备

如需支持新厂商设备，可继承BaseAdapter类并实现相应方法。

## 常见问题

### 1. 数据库连接失败
- 检查数据库服务是否启动
- 确认数据库连接字符串格式正确
- 检查用户名密码是否正确

### 2. 设备连接失败
- 确认设备IP地址、端口、用户名、密码正确
- 检查网络连通性
- 确认设备支持SSH连接

### 3. 前后端分离开发
- 后端启动在 http://localhost:8000
- 前端启动在 http://localhost:5173
- 前端开发服务器已配置代理，将API请求转发到后端

### 4. 权限问题
- 确保应用对数据库有读写权限
- 确保应用对配置备份目录有读写权限

## 贡献指南

### 代码规范
- Python代码遵循PEP8规范
- 使用有意义的变量和函数命名
- 添加必要的注释和文档字符串
- 确保代码风格一致性

### 提交规范
- 使用有意义的提交信息
- 遵循"动词+描述"的格式
- 如有重要变更，更新相关文档

## 许可证

[在此处添加项目许可证信息]