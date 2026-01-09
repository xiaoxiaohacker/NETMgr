#!/usr/bin/env python3
"""
NetMgr 部署前环境检查脚本
检查系统环境是否满足部署要求
"""

import os
import sys
import subprocess
import platform
import socket
import shutil
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...", end="")
    if sys.version_info >= (3, 8):
        print(f"✓ (版本: {sys.version_info[:2]})")
        return True
    else:
        print(f"✗ (当前版本: {sys.version_info[:2]}, 需要3.8+)")
        return False


def check_os():
    """检查操作系统"""
    print("检查操作系统...")
    os_name = platform.system().lower()
    if os_name != 'linux':
        print(f"警告: 检测到 {os_name} 系统，此脚本主要针对 Linux 系统")
    else:
        print(f"✓ 操作系统: {platform.platform()}")
    return os_name == 'linux'


def check_docker():
    """检查 Docker 是否已安装"""
    print("\n检查 Docker...")
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker 版本: {result.stdout.strip()}")
            return True
        else:
            print("✗ Docker 未安装或不可用")
            return False
    except FileNotFoundError:
        print("✗ Docker 未安装")
        return False


def check_docker_compose():
    """检查 Docker Compose 是否已安装"""
    print("\n检查 Docker Compose...")
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker Compose 版本: {result.stdout.strip()}")
            return True
        else:
            print("✗ Docker Compose 未安装或不可用")
            return False
    except FileNotFoundError:
        print("✗ Docker Compose 未安装")
        return False


def check_ports(port_list):
    """检查端口是否被占用"""
    print(f"\n检查端口占用情况 {port_list}...")
    available_ports = []
    occupied_ports = []
    
    for port in port_list:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result != 0:
                available_ports.append(port)
            else:
                occupied_ports.append(port)
    
    if occupied_ports:
        print(f"✗ 以下端口已被占用: {occupied_ports}")
    if available_ports:
        print(f"✓ 以下端口可用: {available_ports}")
    
    return len(occupied_ports) == 0


def check_disk_space(path=".", required_gb=5):
    """检查磁盘空间"""
    print(f"\n检查磁盘空间 ({path})...")
    try:
        # 使用 statvfs 兼容不同平台
        if hasattr(os, 'statvfs'):
            # Linux/Mac
            stat = os.statvfs(path)
            free_space_gb = stat.f_frsize * stat.f_bavail / (1024**3)
        else:
            # Windows
            total, used, free = shutil.disk_usage(path)
            free_space_gb = free / (1024**3)
            
        if free_space_gb >= required_gb:
            print(f"✓ 可用磁盘空间: {free_space_gb:.2f} GB (需要至少 {required_gb} GB)")
            return True
        else:
            print(f"✗ 可用磁盘空间不足: {free_space_gb:.2f} GB (需要至少 {required_gb} GB)")
            return False
    except Exception as e:
        print(f"! 无法检查磁盘空间: {e}")
        return False


def check_required_files():
    """检查必要文件"""
    print("\n检查必要文件...")
    required_files = [
        "requirements.txt",
        "app/main.py",
        "app/services/db.py", 
        "app/services/models.py",
        "docker-compose.yml"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if not missing_files:
        print("✓ 所有必要文件存在")
        return True
    else:
        print(f"✗ 缺失文件: {missing_files}")
        return False
        


def check_env_file():
    """检查环境变量文件"""
    print("\n检查环境变量文件...")
    env_file = Path('.env')
    if env_file.exists():
        print("✓ .env 文件存在")
        # 检查关键环境变量
        with open(env_file, 'r') as f:
            content = f.read()
            required_vars = ['SECRET_KEY', 'DATABASE_URL', 'MYSQL_ROOT_PASSWORD']
            missing_vars = []
            
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"! 缺少以下环境变量: {missing_vars}")
            else:
                print("✓ 所需环境变量已配置")
                
        return True
    else:
        print("! .env 文件不存在，建议复制 .env.example 并进行配置")
        return False


def main():
    """主函数"""
    print("NetMgr Linux 部署环境检查工具\n")
    print("="*50)
    
    checks = []
    
    # 检查操作系统
    checks.append(check_os())
    
    # 检查 Docker
    checks.append(check_docker())
    
    # 检查 Docker Compose
    checks.append(check_docker_compose())
    
    # 检查端口占用
    checks.append(check_ports([8000, 3306, 6379]))  # 后端、MySQL、Redis 端口
    
    # 检查磁盘空间 (至少 5GB)
    checks.append(check_disk_space(Path.cwd(), 5))
    
    # 检查内存 (至少 1GB)
    checks.append(check_memory(1024))
    
    # 检查环境变量文件
    checks.append(check_env_file())
    
    print("\n" + "="*50)
    passed = sum(checks)
    total = len(checks)
    
    print(f"检查结果: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n✓ 所有检查均已通过，您可以继续部署 NetMgr")
        print("\n下一步操作:")
        print("1. 确保 .env 文件已正确配置")
        print("2. 运行 'docker-compose up -d --build' 启动服务")
        print("3. 查看部署指南: DEPLOY_LINUX.md")
    else:
        print(f"\n✗ {total - passed} 项检查未通过，请先解决这些问题")
        print("请参考部署指南: DEPLOY_LINUX.md")
    
    return passed == total


if __name__ == '__main__':
    try:
        import shutil
    except ImportError:
        print("无法导入 shutil 模块")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)