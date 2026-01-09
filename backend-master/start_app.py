#!/usr/bin/env python3
"""
启动脚本，同时启动FastAPI应用和后台服务
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置环境变量，解决中文乱码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

def main():
    """启动应用"""
    try:
        # 检查是否安装了 uvicorn
        import uvicorn
    except ImportError:
        print("正在安装 uvicorn...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn[standard]"])
        import uvicorn

    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent.absolute()
    # 设置 PYTHONPATH
    os.chdir(current_dir)

    # 导入并启动后台服务
    from app.scheduler import TaskScheduler
    from app.services.device_status_checker import device_status_checker

    # 初始化任务调度器
    scheduler = TaskScheduler()
    scheduler.start()
    logger.info("任务调度器已启动")

    # 启动设备状态检查器
    device_status_checker.start()
    logger.info("设备状态检查器已启动")

    # 启动 uvicorn 服务器
    logger.info("正在启动服务器...")
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 8000)),
            reload=os.environ.get("ENVIRONMENT") == "development",  # 生产环境不需要热重载
            log_level="info",
            workers=int(os.environ.get("WORKERS", 1))  # Linux生产环境建议使用多个worker
        )
    except KeyboardInterrupt:
        logger.info("正在关闭服务器...")
    finally:
        # 确保后台服务正确关闭
        scheduler.stop()
        device_status_checker.stop()
        logger.info("后台服务已停止")


if __name__ == "__main__":
    main()