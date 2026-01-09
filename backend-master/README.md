# NetMgr 网络设备管理系统

NetMgr 是一个基于前后端分离架构的网络设备管理系统，旨在统一管理多厂商（华为、华三、锐捷等）网络设备，提升运维效率。

## 功能特性

- **设备管理**: 添加、编辑、删除、查询设备；支持华为、华三、锐捷等主流厂商；实时在线/离线状态监控。
- **配置管理**: 自动化配置备份与恢复；配置历史版本追踪；配置差异比较。
- **网络监控**: 实时接口状态监测；设备连通性检测（Ping/SSH）；SNMP数据采集；网络拓扑自动生成与展示。
- **系统管理**: JWT用户认证授权；操作日志记录；任务调度（Celery）；系统参数设置。
- **告警管理**: 实时告警监控，支持按级别、设备、时间等维度筛选。
- **任务管理**: 周期性或一次性任务的创建、调度、执行和监控。

## 技术栈

- **后端**: Python 3.8+, FastAPI, SQLAlchemy, MySQL, Celery, Redis
- **前端**: Vue 3, TypeScript, Element Plus, Vite
- **数据库**: MySQL 5.7+, Redis（可选）
- **容器化**: Docker, docker-compose

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- MySQL 5.7+ 或 MariaDB 10.2+
- Redis（用于异步任务，可选）

### 后端开发环境

```bash
cd backend-master

# 创建虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（创建 .env 文件）
echo "DATABASE_URL=mysql+pymysql://username:password@localhost:3306/netmgr" > .env
echo "REDIS_URL=redis://localhost:6379/0" >> .env
echo "SECRET_KEY=your-32-character-secret-key-here" >> .env

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端开发环境

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问地址: http://localhost:5173

### 构建与部署命令

#### Docker 部署（推荐）
```bash
cd backend-master
docker-compose up -d
```

#### 生产部署 - 后端
```bash
# 安装 Gunicorn
pip install gunicorn uvicorn

# 启动服务
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 生产部署 - 前端
```bash
# 构建生产包
npm run build
# 输出目录: dist/
# 将 dist/ 内容部署到 Nginx/Apache 等 Web 服务器
```

## API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend-master/          # 后端项目根目录
├── app/                 # 后端应用代码
│   ├── adapters/        # 设备适配器（华为、华三、锐捷等）
│   ├── api/             # API路由定义
│   ├── models/          # 数据模型定义
│   ├── services/        # 业务逻辑服务
│   ├── utils/           # 工具函数
│   └── main.py          # 应用入口
├── config_backups/      # 配置备份文件存储
├── docker-compose.yml   # Docker编排文件
├── requirements.txt     # Python依赖
└── README.md            # 项目说明
frontend/               # 前端项目根目录
├── src/                # 前端源码
│   ├── api/            # API接口定义
│   ├── components/     # 组件
│   ├── router/         # 路由配置
│   ├── views/          # 页面组件
│   └── utils/          # 工具函数
├── package.json        # npm依赖
└── vite.config.ts      # 构建配置
```

## 设计模式

- **工厂模式**: [AdapterManager](file://e:\Desktop\NETMgr\backend-master\app\services\adapter_manager.py#L8-L95) 根据设备类型动态创建适配器实例
- **单例模式**: 配置服务、数据库连接等全局共享资源
- **分层架构**: 路由(API) → 服务(Service) → 数据模型(Model)
- **观察者模式**: SNMP Trap 监听与告警触发机制

## 安全要求

- 使用 HTTPS 传输敏感数据
- JWT Token 设置合理过期时间（建议≤24h）
- 密码使用 PassLib 加密存储
- 敏感配置项加密保存（如设备登录凭据）

## 已知问题

- SNMP Trap 解析逻辑需进一步完善（见 utils/trap_parser.py）
- 拓扑发现依赖 LLDP/CDP，部分老旧设备可能不兼容
- 大量设备批量操作可能导致内存占用升高

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进本项目。