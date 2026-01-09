# NetMgr Linux部署指南

本文档详细介绍如何在Linux环境下部署NetMgr网络设备管理系统。

## 系统要求

- Ubuntu 20.04 LTS / CentOS 8 / Debian 10 或更高版本
- Python 3.8+
- Node.js 16+
- MySQL 5.7+ 或 MariaDB 10.2+
- Redis (可选，用于异步任务)
- 至少2GB内存
- 至少5GB可用磁盘空间

## 安装步骤

### 1. 安装系统依赖

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv gcc python3-dev libmariadb-dev default-libmysqlclient-dev build-essential nodejs npm docker.io docker-compose
```

#### CentOS/RHEL:
```bash
sudo yum update
sudo yum install -y python3 python3-pip gcc python3-devel mariadb-devel mysql-community-devel epel-release
sudo yum install -y nodejs npm docker docker-compose
```

### 2. 克隆项目代码

```bash
git clone https://github.com/your-username/NETMgr.git
cd NETMgr/backend-master
```

### 3. 创建Python虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # 激活虚拟环境
```

### 4. 安装Python依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 配置数据库

#### 安装MySQL
```bash
# Ubuntu/Debian
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
```

#### 启动MySQL并配置
```bash
sudo systemctl start mysql
sudo mysql_secure_installation
```

#### 创建数据库和用户
```sql
CREATE DATABASE netmgr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'netmgr'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON netmgr.* TO 'netmgr'@'localhost';
FLUSH PRIVILEGES;
```

### 6. 配置环境变量

复制示例环境文件并进行配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接等参数：

```bash
nano .env
```

### 7. 初始化数据库

使用init.sql文件初始化数据库：

```bash
mysql -u root -p < init.sql
```

### 8. 安装和构建前端

```bash
cd ../frontend
npm install
npm run build
```

### 9. 启动服务

#### 方法一：直接运行
```bash
cd ../backend-master
source venv/bin/activate
python start_app.py
```

#### 方法二：使用Gunicorn（推荐用于生产环境）
```bash
cd ../backend-master
source venv/bin/activate
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 方法三：使用Docker Compose
```bash
cd ../backend-master
docker-compose up -d
```

## 配置反向代理（使用Nginx）

安装Nginx：

```bash
sudo apt install nginx  # Ubuntu/Debian
# 或
sudo yum install nginx  # CentOS/RHEL
```

创建Nginx配置：

```bash
sudo nano /etc/nginx/sites-available/netmgr
```

配置内容如下：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/netmgr /etc/nginx/sites-enabled
sudo nginx -t  # 检查配置
sudo systemctl restart nginx
```

## 启用HTTPS（使用Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
# 或
sudo yum install certbot python3-certbot-nginx  # CentOS/RHEL

sudo certbot --nginx -d your-domain.com
```

## 系统服务配置

创建systemd服务文件：

```bash
sudo nano /etc/systemd/system/netmgr.service
```

内容如下：

```ini
[Unit]
Description=NetMgr Application
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/NETMgr/backend-master
EnvironmentFile=/path/to/NETMgr/backend-master/.env
ExecStart=/path/to/NETMgr/backend-master/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动并启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start netmgr
sudo systemctl enable netmgr
```

## 健康检查

系统提供健康检查端点：

```bash
curl http://your-domain.com/health
```

## 日志管理

应用日志位于：

- 后端日志：控制台输出
- Nginx日志：`/var/log/nginx/access.log` 和 `/var/log/nginx/error.log`

## 备份策略

定期备份数据库和配置文件：

```bash
# 数据库备份
mysqldump -u netmgr -p netmgr > backup_$(date +%Y%m%d_%H%M%S).sql

# 配置备份目录备份
tar -czf config_backups_$(date +%Y%m%d_%H%M%S).tar.gz config_backups/
```

## 监控和维护

- 定期检查系统资源使用情况
- 监控应用日志中的错误
- 确保数据库有足够的磁盘空间
- 定期更新系统和应用依赖

## 故障排除

### 问题：数据库连接失败
- 检查数据库服务是否运行
- 验证数据库连接参数
- 检查防火墙设置

### 问题：应用无法启动
- 检查Python依赖是否安装完整
- 验证环境变量配置
- 查看详细错误日志

### 问题：前端页面无法访问API
- 检查CORS配置
- 验证代理设置
- 确认后端服务运行状态