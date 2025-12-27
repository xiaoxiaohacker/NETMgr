# NetMgr 网络设备管理系统

## 项目概述

NetMgr 是一个基于前后端分离架构的网络设备管理系统，用于统一管理华为、华三、锐捷等多厂商的网络设备。系统提供设备管理、状态监控、配置备份、网络拓扑可视化等功能。

### 技术栈

**后端**:
- Web框架: FastAPI
- 数据库: MySQL + SQLAlchemy
- 认证: JWT (python-jose) + PassLib
- 网络设备连接: Netmiko
- 任务队列: Celery + Redis（可选）
- 容器化: Docker

**前端**:
- 前端框架: Vue 3
- 构建工具: Vite
- UI组件库: Element Plus
- 状态管理: Pinia
- HTTP客户端: Axios
- 路由管理: Vue Router

## 项目结构

```
NETMgr/
├── backend-master/     # 后端项目目录
│   ├── app/           # 后端应用代码
│   ├── config/        # 配置文件
│   ├── requirements.txt # Python依赖
│   ├── Dockerfile     # Docker配置
│   └── docker-compose.yml # Docker编排配置
├── frontend/          # 前端项目目录
│   ├── src/          # 前端源代码
│   ├── public/       # 静态资源
│   ├── package.json  # Node.js依赖
│   └── vite.config.ts # Vite构建配置
└── README.md         # 本文件
```

## 功能特性

### 设备管理
- 支持多种厂商设备（华为、华三、锐捷等）
- 设备添加、编辑、删除、查询
- 设备状态监控（在线/离线）

### 配置管理
- 设备配置备份与恢复
- 配置变更历史追踪
- 配置比较功能

### 网络监控
- 实时接口状态监控
- 设备连通性检查
- 网络拓扑可视化

### 系统管理
- 用户认证与授权
- 系统日志管理
- 任务调度管理
- 系统设置配置

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 5.7+ 或 MariaDB 10.2+
- Redis (可选，用于异步任务)

### 本地开发

#### 1. 启动后端服务
```bash
cd backend-master

# 创建并激活虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（创建 .env 文件）
# DATABASE_URL=mysql+pymysql://username:password@localhost:3306/netmgr
# REDIS_URL=redis://localhost:6379/0
# SECRET_KEY=your-secret-key-here

# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. 启动前端服务
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5173`，已配置代理将API请求转发到后端服务。

### Docker部署

使用Docker Compose一键部署整个系统：
```bash
cd backend-master
docker-compose up -d
```

### 生产环境部署

#### 后端部署
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 前端部署
```bash
# 构建生产版本
npm run build

# 将dist目录内容部署到Web服务器
```

## API文档

启动后端服务后，访问以下地址获取API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 配置说明

### 数据库配置
在 `backend-master/app/services/config.py` 中配置数据库连接信息，支持MySQL和SQLite。

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
- Vue组件使用Composition API
- 使用有意义的变量和函数命名
- 添加必要的注释和文档字符串

### 提交规范
- 使用有意义的提交信息
- 遵循"动词+描述"的格式
- 如有重要变更，更新相关文档

## 许可证

[在此处添加项目许可证信息]

## 联系方式

如有问题或建议，请通过以下方式联系我们：
- 提交GitHub Issue
- 邮箱: [在此处添加联系邮箱]