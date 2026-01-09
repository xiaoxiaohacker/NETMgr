import threading
import time
import logging
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.services.db import engine, get_db
from app.services.models import Task, TaskStatus, TaskType, Device
from app.services.config_backup_service import create_config_backup
from app.services.schemas import ConfigCreate
from app.services.adapter_manager import AdapterManager
from app.tasks import backup_device_config_task, batch_process_devices, CELERY_AVAILABLE

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TaskScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.interval = 10  # 检查间隔（秒）

    def start(self):
        """启动任务调度器"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("任务调度器已启动")

    def stop(self):
        """停止任务调度器"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("任务调度器已停止")

    def _run(self):
        """运行调度器主循环"""
        while self.running:
            try:
                self._check_and_execute_tasks()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"任务调度器执行出错: {e}")

    def _check_and_execute_tasks(self):
        """检查并执行待处理的任务"""
        db = SessionLocal()
        try:
            # 获取所有待处理且到达执行时间的任务
            now = datetime.utcnow()
            pending_tasks = db.query(Task).filter(
                Task.status == TaskStatus.PENDING,
                (Task.scheduled_time <= now) | (Task.scheduled_time.is_(None))
            ).all()

            logger.info(f"检查到 {len(pending_tasks)} 个待处理任务")

            for task in pending_tasks:
                # 创建新的数据库会话来处理每个任务，避免会话污染
                self._process_single_task(task.id)

        except Exception as e:
            logger.error(f"检查任务时出错: {e}", exc_info=True)
        finally:
            db.close()

    def _process_single_task(self, task_id):
        """处理单个任务，使用独立的数据库会话"""
        db = None
        try:
            db = SessionLocal()
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"任务 {task_id} 不存在或已被处理")
                return

            # 检查任务是否仍处于PENDING状态（防止重复处理）
            if task.status != TaskStatus.PENDING:
                logger.info(f"任务 {task_id} 状态已改变，当前状态: {task.status}")
                return

            # 更新任务状态为排队中
            now = datetime.utcnow()
            old_status = task.status
            task.status = TaskStatus.QUEUED
            if not task.logs:
                task.logs = ""
            task.logs += f"{now.strftime('%Y-%m-%d %H:%M:%S')} - 任务状态由 '{old_status}' 变更为 'QUEUED' (已加入执行队列)\n"
            db.commit()

            logger.info(f"任务 {task_id} 状态已更新为 QUEUED")

            # 为每个任务创建一个新的线程来执行
            task_thread = threading.Thread(target=self._execute_task_wrapper, args=(task_id,), daemon=True)
            task_thread.start()

            logger.info(f"已启动任务 {task_id} 的执行线程")

        except Exception as e:
            logger.error(f"处理任务 {task_id} 时出错: {e}")
        finally:
            if db:
                db.close()

    def execute_task_now(self, task_id):
        """
        手动立即执行指定的任务

        Args:
            task_id: 要执行的任务ID

        Returns:
            bool: 是否成功提交执行请求
        """
        logger.info(f"收到手动执行任务请求: {task_id}")

        # 使用独立的数据库会话处理任务
        try:
            # 先验证任务是否存在且状态正确
            db = SessionLocal()
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.error(f"无法执行任务: 任务 {task_id} 不存在")
                db.close()
                return False

            if task.status not in [TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.FAILED]:
                logger.warning(f"无法执行任务: 任务 {task_id} 当前状态为 {task.status}，不允许手动执行")
                db.close()
                return False

            # 关闭初始会话，让执行包装器创建新的会话
            db.close()

            # 如果任务是失败状态，先重置为PENDING
            if task.status == TaskStatus.FAILED:
                # 在这里重新打开会话来更新状态
                reset_db = SessionLocal()
                try:
                    task_to_reset = reset_db.query(Task).filter(Task.id == task_id).first()
                    if task_to_reset:
                        task_to_reset.status = TaskStatus.PENDING
                        task_to_reset.started_at = None
                        task_to_reset.completed_at = None
                        task_to_reset.progress = 0
                        task_to_reset.result = None
                        if not task_to_reset.logs:
                            task_to_reset.logs = ""
                        task_to_reset.logs += f"\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - 收到手动执行请求，任务从 FAILED 状态重置为 PENDING\n"
                        reset_db.commit()
                        logger.info(f"任务 {task_id} 已从 FAILED 状态重置为 PENDING")
                finally:
                    reset_db.close()

            # 启动新线程执行任务，避免阻塞调用方
            task_thread = threading.Thread(target=self._execute_task_wrapper, args=(task_id,), daemon=True)
            task_thread.start()
            logger.info(f"已启动任务 {task_id} 的执行线程")
            return True
        except Exception as e:
            logger.error(f"提交任务执行请求时出错: {e}", exc_info=True)
            return False

    def _execute_task_wrapper(self, task_id):
        """任务执行包装器，为每个任务创建独立的数据库会话"""
        db = None
        try:
            db = SessionLocal()
            # 查询任务并锁定行以防止并发修改
            task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
            if not task:
                logger.error(f"任务 {task_id} 不存在")
                return

            # 再次确认任务状态
            if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                logger.info(f"任务 {task_id} 状态已改变，当前状态: {task.status}")
                db.commit()  # 提交查询时的锁
                return

            # 确保在执行前状态没有被改变
            db.refresh(task)
            if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                logger.info(f"任务 {task_id} 状态在刷新后已改变，当前状态: {task.status}")
                return

            self._execute_task(db, task)
            db.commit()  # 确保所有更改都被提交

        except Exception as e:
            logger.error(f"执行任务 {task_id} 时出错: {e}", exc_info=True)
            # 如果发生严重错误，尝试更新任务状态
            if db:
                try:
                    # 回滚任何未完成的事务
                    db.rollback()
                    task = db.query(Task).filter(Task.id == task_id).first()
                    if task and task.status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.utcnow()
                        if not task.logs:
                            task.logs = ""
                        task.logs += f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - 任务执行异常: {str(e)}\n"
                        db.commit()
                except Exception as inner_e:
                    logger.error(f"更新任务 {task_id} 失败状态时出错: {inner_e}")
                    db.rollback()
        finally:
            if db:
                db.close()

    def _execute_task(self, db, task):
        """执行单个任务"""
        try:
            # 更新任务状态为运行中
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            task.progress = 0
            task.logs = ""  # 初始化日志
            db.commit()

            # 根据任务类型执行相应的操作
            if task.task_type == TaskType.CONFIG_BACKUP:
                self._execute_config_backup_task(db, task)
            elif task.task_type == TaskType.DEVICE_INSPECTION:
                self._execute_device_inspection_task(db, task)
            elif task.task_type == TaskType.FIRMWARE_UPGRADE:
                self._execute_firmware_upgrade_task(db, task)
            else:
                # 未知任务类型
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.result = "未知的任务类型"
                task.logs += f"错误: 未知的任务类型 {task.task_type}\n"
                db.commit()

                # 记录系统日志
                try:
                    from app.services.system_log import create_system_log
                    create_system_log(
                        db=db,
                        level="ERROR",
                        module="TASK",
                        message=f"未知的任务类型: {task.task_type}",
                        device_id=None
                    )
                except Exception as log_error:
                    logger.error(f"记录系统日志失败: {str(log_error)}")

        except Exception as e:
            logger.error(f"执行任务 {task.id} 时出错: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.result = str(e)
            task.logs += f"致命错误: {str(e)}\n"
            db.commit()

            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="ERROR",
                    module="TASK",
                    message=f"执行任务 '{task.name}' (ID: {task.id}) 时发生致命错误: {str(e)}",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")

    def _execute_config_backup_task(self, db, task):
        """执行配置备份任务"""
        logger.info(f"开始执行配置备份任务 {task.id}")
        task.logs = "开始执行配置备份任务\n"
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        db.commit()  # 提交日志更新

        try:
            # 获取目标设备信息
            devices = task.target_devices
            total_devices = len(devices)

            if total_devices == 0:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.result = "没有找到目标设备"
                task.logs += "错误: 没有找到目标设备\n"
                db.commit()
                return

            successful_backups = 0
            failed_backups = 0

            # 逐个备份设备配置
            for i, device in enumerate(devices):
                try:
                    # 更新进度
                    progress = int((i / total_devices) * 100)
                    task.progress = progress
                    task.logs += f"正在备份设备 {device.name} ({device.management_ip})...\n"
                    db.commit()

                    # 准备设备信息
                    device_info = {
                        "management_ip": device.management_ip,
                        "username": device.username,
                        "password": device.password,
                        "port": device.port,
                        "device_type": device.device_type,
                        "enable_password": device.enable_password
                    }

                    logger.info(f"准备备份设备 {device.name} ({device.management_ip}), 设备类型: {device.device_type}")

                    # 为SNMP设备增加特殊配置
                    if device.device_type and device.device_type.lower() in ['snmp', 'switch']:
                        device_info.update({
                            "snmp_community": "public",  # 社区字符串（用于SNMP v1/v2c）
                            "snmp_port": 161,
                            "snmp_timeout": 20,  # 增加超时时间到20秒
                            "snmp_retries": 3,   # 增加重试次数到3次
                            "snmp_version": 2,   # 使用SNMP v2c进行测试
                            "snmp_security_name": None,  # v2c不需要安全名称
                            # v2c不需要认证和加密配置
                            "snmp_auth_protocol": None,
                            "snmp_auth_key": None,
                            "snmp_priv_protocol": None,
                            "snmp_priv_key": None
                        })
                        logger.info(f"为SNMP设备添加特殊配置: {device_info}")
                        logger.info("注意：如果SNMP v2c不起作用，可以尝试切换到SNMP v3")

                    # 如果Celery可用，尝试使用Celery执行任务
                    if CELERY_AVAILABLE:
                        try:
                            # 尝试通过Celery执行任务
                            result = backup_device_config_task.delay(device_info, device.id)
                            # 等待任务完成
                            task_result = result.get(timeout=300)  # 5分钟超时

                            if task_result['success']:
                                # 保存配置到数据库
                                config_data = ConfigCreate(
                                    device_id=device.id,
                                    config=task_result['config'],
                                    taken_by="system",
                                    description=f"自动配置备份任务 {task.id}"
                                )
                                create_config_backup(db, config_data)

                                successful_backups += 1
                                task.logs += f"  成功: 设备 {device.management_ip} 的配置已成功备份\n"

                                # 记录系统日志
                                try:
                                    from app.services.system_log import create_system_log
                                    create_system_log(
                                        db=db,
                                        level="INFO",
                                        module="BACKUP",
                                        message=f"设备 {device.management_ip} 的配置备份成功",
                                        device_id=device.id
                                    )
                                except Exception as log_error:
                                    logger.error(f"记录系统日志失败: {str(log_error)}")
                            else:
                                failed_backups += 1
                                task.logs += f"  失败: 任务执行失败 - {task_result.get('error', '未知错误')}\n"

                                # 记录系统日志
                                try:
                                    from app.services.system_log import create_system_log
                                    create_system_log(
                                        db=db,
                                        level="ERROR",
                                        module="BACKUP",
                                        message=f"设备 {device.management_ip} 的配置备份失败: {task_result.get('error', '未知错误')}",
                                        device_id=device.id
                                    )
                                except Exception as log_error:
                                    logger.error(f"记录系统日志失败: {str(log_error)}")
                        except Exception as celery_error:
                            logger.warning(f"Celery执行失败，使用直接执行模式: {str(celery_error)}")
                            # 使用直接执行模式
                            backup_result = self._direct_backup_device_config(device_info, device.id)
                            if backup_result['success']:
                                # 保存配置到数据库
                                config_data = ConfigCreate(
                                    device_id=device.id,
                                    config=backup_result['config'],
                                    taken_by="system",
                                    description=f"自动配置备份任务 {task.id}"
                                )
                                create_config_backup(db, config_data)

                                successful_backups += 1
                                task.logs += f"  成功: 设备 {device.management_ip} 的配置已成功备份(直接执行)\n"

                                # 记录系统日志
                                try:
                                    from app.services.system_log import create_system_log
                                    create_system_log(
                                        db=db,
                                        level="INFO",
                                        module="BACKUP",
                                        message=f"设备 {device.management_ip} 的配置备份成功(直接执行)",
                                        device_id=device.id
                                    )
                                except Exception as log_error:
                                    logger.error(f"记录系统日志失败: {str(log_error)}")
                            else:
                                failed_backups += 1
                                task.logs += f"  失败: 直接执行模式失败 - {backup_result.get('error', '未知错误')}\n"

                                # 记录系统日志
                                try:
                                    from app.services.system_log import create_system_log
                                    create_system_log(
                                        db=db,
                                        level="ERROR",
                                        module="BACKUP",
                                        message=f"设备 {device.management_ip} 的配置备份失败(直接执行): {backup_result.get('error', '未知错误')}",
                                        device_id=device.id
                                    )
                                except Exception as log_error:
                                    logger.error(f"记录系统日志失败: {str(log_error)}")
                    else:
                        # Celery不可用，使用直接执行模式
                        backup_result = self._direct_backup_device_config(device_info, device.id)
                        if backup_result['success']:
                            # 保存配置到数据库
                            config_data = ConfigCreate(
                                device_id=device.id,
                                config=backup_result['config'],
                                taken_by="system",
                                description=f"自动配置备份任务 {task.id}"
                            )
                            create_config_backup(db, config_data)

                            successful_backups += 1
                            task.logs += f"  成功: 设备 {device.management_ip} 的配置已成功备份(直接执行)\n"

                            # 记录系统日志
                            try:
                                from app.services.system_log import create_system_log
                                create_system_log(
                                    db=db,
                                    level="INFO",
                                    module="BACKUP",
                                    message=f"设备 {device.management_ip} 的配置备份成功(直接执行)",
                                    device_id=device.id
                                )
                            except Exception as log_error:
                                logger.error(f"记录系统日志失败: {str(log_error)}")
                        else:
                            failed_backups += 1
                            task.logs += f"  失败: 直接执行模式失败 - {backup_result.get('error', '未知错误')}\n"

                            # 记录系统日志
                            try:
                                from app.services.system_log import create_system_log
                                create_system_log(
                                    db=db,
                                    level="ERROR",
                                    module="BACKUP",
                                    message=f"设备 {device.management_ip} 的配置备份失败(直接执行): {backup_result.get('error', '未知错误')}",
                                    device_id=device.id
                                )
                            except Exception as log_error:
                                logger.error(f"记录系统日志失败: {str(log_error)}")

                    # 提交日志更新
                    db.commit()

                except Exception as e:
                    failed_backups += 1
                    task.logs += f"  失败: 备份设备 {device.name} 时出错: {str(e)}\n"
                    logger.error(f"备份设备 {device.name} 时出错: {str(e)}", exc_info=True)

                    # 记录系统日志
                    try:
                        from app.services.system_log import create_system_log
                        create_system_log(
                            db=db,
                            level="ERROR",
                            module="BACKUP",
                            message=f"备份设备 {device.management_ip} 时出错: {str(e)}",
                            device_id=device.id
                        )
                    except Exception as log_error:
                        logger.error(f"记录系统日志失败: {str(log_error)}")

                    db.commit()

            # 更新最终结果
            task.progress = 100
            task.completed_at = datetime.utcnow()

            if failed_backups == 0:
                task.status = TaskStatus.COMPLETED
                task.result = f"配置备份任务完成，成功备份 {successful_backups} 个设备"
            elif successful_backups == 0:
                task.status = TaskStatus.FAILED
                task.result = f"配置备份任务失败，{failed_backups} 个设备备份失败"
            else:
                task.status = TaskStatus.COMPLETED
                task.result = f"配置备份任务部分完成，成功备份 {successful_backups} 个设备，{failed_backups} 个设备备份失败"

            task.logs += f"任务完成，成功: {successful_backups}，失败: {failed_backups}\n"
            db.commit()

            logger.info(f"配置备份任务 {task.id} 执行完成: {task.result}")

            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="INFO",
                    module="TASK",
                    message=f"配置备份任务 '{task.name}' (ID: {task.id}) 执行完成: {task.result}",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")

        except Exception as e:
            logger.error(f"执行配置备份任务 {task.id} 时出错: {str(e)}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.result = f"执行任务时发生错误: {str(e)}"
            task.logs += f"错误: {str(e)}\n"
            db.commit()

            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="ERROR",
                    module="TASK",
                    message=f"配置备份任务 '{task.name}' (ID: {task.id}) 执行失败: {str(e)}",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")

    def _direct_backup_device_config(self, device_info, device_id):
        """直接执行设备配置备份，不使用Celery"""
        try:
            # 使用AdapterManager替代AdapterFactory
            adapter = AdapterManager.get_adapter(device_info)

            # 连接到设备并获取配置
            if adapter.connect():
                config = adapter.get_config()
                adapter.disconnect()

                # 检查配置是否成功获取
                if config is None or config.strip() == "":
                    return {
                        'success': False,
                        'error': '无法从设备获取配置'
                    }
                else:
                    return {
                        'success': True,
                        'config': config
                    }
            else:
                return {
                    'success': False,
                    'error': '无法连接到设备'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _execute_device_inspection_task(self, db, task):
        """执行设备巡检任务"""
        logger.info(f"开始执行设备巡检任务 {task.id}")
        task.logs = "开始执行设备巡检任务\n"
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        db.commit()

        try:
            devices = task.target_devices
            total_devices = len(devices)

            if total_devices == 0:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.result = "没有找到目标设备"
                task.logs += "错误: 没有找到目标设备\n"
                db.commit()
                return

            successful_inspections = 0
            failed_inspections = 0

            for i, device in enumerate(devices):
                try:
                    progress = int((i / total_devices) * 100)
                    task.progress = progress
                    task.logs += f"正在巡检设备 {device.name} ({device.management_ip})...\n"
                    db.commit()

                    # 模拟设备巡检过程
                    time.sleep(2)

                    # 模拟巡检结果
                    inspection_result = {
                        "device_id": device.id,
                        "status": "normal",
                        "cpu_usage": f"{70 + i}%",
                        "memory_usage": f"{60 + i}%",
                        "uptime": f"{30 + i} days",
                        "message": f"设备 {device.management_ip} 巡检完成"
                    }

                    successful_inspections += 1
                    task.logs += f"  成功: {inspection_result['message']} (CPU: {inspection_result['cpu_usage']}, 内存: {inspection_result['memory_usage']})\n"
                    db.commit()

                    # 记录系统日志
                    try:
                        from app.services.system_log import create_system_log
                        create_system_log(
                            db=db,
                            level="INFO",
                            module="INSPECTION",
                            message=f"设备 {device.management_ip} 巡检成功 (CPU: {inspection_result['cpu_usage']}, 内存: {inspection_result['memory_usage']})",
                            device_id=device.id
                        )
                    except Exception as log_error:
                        logger.error(f"记录系统日志失败: {str(log_error)}")

                except Exception as e:
                    failed_inspections += 1
                    task.logs += f"  失败: 巡检设备 {device.name} 时出错: {str(e)}\n"
                    db.commit()

                    # 记录系统日志
                    try:
                        from app.services.system_log import create_system_log
                        create_system_log(
                            db=db,
                            level="ERROR",
                            module="INSPECTION",
                            message=f"巡检设备 {device.management_ip} 时出错: {str(e)}",
                            device_id=device.id
                        )
                    except Exception as log_error:
                        logger.error(f"记录系统日志失败: {str(log_error)}")

            task.progress = 100
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = f"设备巡检任务完成。成功: {successful_inspections}, 失败: {failed_inspections}"
            task.logs += f"任务完成。成功: {successful_inspections}, 失败: {failed_inspections}\n"
            db.commit()
            logger.info(f"设备巡检任务 {task.id} 执行完成")

            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="INFO",
                    module="TASK",
                    message=f"设备巡检任务 '{task.name}' (ID: {task.id}) 执行完成: {task.result}",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.result = str(e)
            task.logs += f"任务执行失败: {str(e)}\n"
            db.commit()

    def _execute_firmware_upgrade_task(self, db, task):
        """执行固件升级任务"""
        logger.info(f"开始执行固件升级任务 {task.id}")
        task.logs = "开始执行固件升级任务\n"
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        db.commit()

        try:
            devices = task.target_devices
            total_devices = len(devices)

            if total_devices == 0:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.result = "没有找到目标设备"
                task.logs += "错误: 没有找到目标设备\n"
                db.commit()
                return

            successful_upgrades = 0
            failed_upgrades = 0

            for i, device in enumerate(devices):
                try:
                    progress = int((i / total_devices) * 100)
                    task.progress = progress
                    task.logs += f"正在升级设备 {device.name} ({device.management_ip})...\n"
                    db.commit()

                    # 模拟固件升级过程
                    time.sleep(3)

                    # 模拟升级结果
                    upgrade_result = {
                        "device_id": device.id,
                        "status": "success",
                        "old_version": device.os_version,
                        "new_version": "v2.1." + str(i),
                        "message": f"设备 {device.management_ip} 固件升级完成"
                    }

                    successful_upgrades += 1
                    task.logs += f"  成功: {upgrade_result['message']} (版本从 {upgrade_result['old_version']} 升级到 {upgrade_result['new_version']})\n"
                    db.commit()

                    # 记录系统日志
                    try:
                        from app.services.system_log import create_system_log
                        create_system_log(
                            db=db,
                            level="INFO",
                            module="FIRMWARE",
                            message=f"设备 {device.management_ip} 固件升级成功 (版本从 {upgrade_result['old_version']} 升级到 {upgrade_result['new_version']})",
                            device_id=device.id
                        )
                    except Exception as log_error:
                        logger.error(f"记录系统日志失败: {str(log_error)}")

                except Exception as e:
                    failed_upgrades += 1
                    task.logs += f"  失败: 升级设备 {device.name} 时出错: {str(e)}\n"
                    db.commit()

                    # 记录系统日志
                    try:
                        from app.services.system_log import create_system_log
                        create_system_log(
                            db=db,
                            level="ERROR",
                            module="FIRMWARE",
                            message=f"升级设备 {device.management_ip} 时出错: {str(e)}",
                            device_id=device.id
                        )
                    except Exception as log_error:
                        logger.error(f"记录系统日志失败: {str(log_error)}")

            task.progress = 100
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = f"固件升级任务完成。成功: {successful_upgrades}, 失败: {failed_upgrades}"
            task.logs += f"任务完成。成功: {successful_upgrades}, 失败: {failed_upgrades}\n"
            db.commit()
            logger.info(f"固件升级任务 {task.id} 执行完成")

            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="INFO",
                    module="TASK",
                    message=f"固件升级任务 '{task.name}' (ID: {task.id}) 执行完成: {task.result}",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.result = str(e)
            task.logs += f"任务执行失败: {str(e)}\n"
            db.commit()

            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db,
                    level="ERROR",
                    module="TASK",
                    message=f"固件升级任务 '{task.name}' (ID: {task.id}) 执行失败: {str(e)}",
                    device_id=None
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")


# 定义支持的任务类型
SUPPORTED_TASK_TYPES = {
    'config_backup': '配置备份',
    'device_inspection': '设备巡检',
    'firmware_upgrade': '固件升级',
    'security_scan': '安全扫描',
    'performance_monitoring': '性能监控',
    'configuration_compliance': '配置合规性检查'
}

# 定义支持的厂商
SUPPORTED_VENDORS = [
    'Cisco',
    'Huawei',
    'H3C',
    'ruijie'
]

# 创建全局调度器实例
scheduler = TaskScheduler()