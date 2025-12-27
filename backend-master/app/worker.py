"""
Celery Worker 启动文件
"""
import os
import sys
from pathlib import Path

# 将项目根目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tasks import celery_app

if __name__ == "__main__":
    celery_app.start()