#!/usr/bin/env python3
"""
启动 Celery Worker 的脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # 设置工作目录
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    # 启动 Celery worker
    cmd = [
        "celery",
        "-A",
        "app.main.celery_app",
        "worker",
        "--loglevel=info",
        "--pool=solo"  # Windows兼容模式
    ]
    
    print("启动 Celery Worker...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Celery Worker 启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCelery Worker 已停止")
        sys.exit(0)

if __name__ == "__main__":
    main()