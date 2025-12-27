#!/usr/bin/env python3
"""
启动脚本，同时启动FastAPI应用和Celery Worker
"""

import os
import sys
import subprocess
import signal
import time
from threading import Thread

# 存储子进程的全局变量
processes = []

def signal_handler(sig, frame):
    """处理中断信号，优雅地关闭所有子进程"""
    print("\n正在关闭所有进程...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"进程 {process.pid} 未在5秒内响应终止信号，强制终止...")
            process.kill()
    print("所有进程已关闭")
    sys.exit(0)

def start_uvicorn():
    """启动Uvicorn服务器"""
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    print("启动 Uvicorn 服务器...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(cmd)
        processes.append(process)
        return process
    except FileNotFoundError:
        print("错误: 未找到 uvicorn 命令，请确保已安装 uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"启动 Uvicorn 服务器时出错: {e}")
        sys.exit(1)

def start_celery_worker():
    """启动Celery Worker"""
    # 等待一段时间再启动Celery Worker，确保Redis已经启动
    time.sleep(5)
    
    # 检查操作系统是否为Windows
    if os.name == 'nt':
        pool_option = "--pool=solo"  # Windows兼容模式
    else:
        pool_option = "--pool=threads"
    
    cmd = [
        "celery",
        "-A",
        "app.tasks",  # 修改为正确的模块路径
        "worker",
        "--loglevel=info",
        pool_option
    ]
    
    print("启动 Celery Worker...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(cmd)
        processes.append(process)
        return process
    except FileNotFoundError:
        print("警告: 未找到 celery 命令，将只启动FastAPI服务器。如果需要异步任务功能，请安装celery和redis")
        return None
    except Exception as e:
        print(f"启动 Celery Worker 时出错: {e}")
        return None

def main():
    # 注册信号处理器
    if os.name != 'nt':  # Windows不支持这些信号
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动Uvicorn服务器
        uvicorn_process = start_uvicorn()
        
        # 启动Celery Worker
        celery_process = start_celery_worker()
        
        # 等待任一进程结束
        while True:
            if uvicorn_process and uvicorn_process.poll() is not None:
                print(f"Uvicorn服务器已退出，退出码: {uvicorn_process.returncode}")
                break
                
            if celery_process and celery_process.poll() is not None:
                print(f"Celery Worker已退出，退出码: {celery_process.returncode}")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n接收到中断信号...")
    finally:
        # Windows下使用不同的处理方式
        if os.name == 'nt':
            print("\n正在关闭所有进程...")
            for process in processes:
                if process and process.poll() is None:  # 进程仍在运行
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print(f"进程 {process.pid} 未在5秒内响应终止信号，强制终止...")
                        process.kill()
            time.sleep(2)

if __name__ == "__main__":
    main()