from datetime import datetime
from typing import Dict, Any, List
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.services.models import Alert
from app.services.db import get_db
from app.utils.trap_parser import SNMPTrapParser
import json

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务类"""
    
    @staticmethod
    def create_alert(alert_data: Dict[str, Any], db: Session = None) -> Alert:
        """
        创建告警记录
        
        Args:
            alert_data: 告警数据
            db: 数据库会话
            
        Returns:
            创建的告警对象
        """
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
            
        try:
            # 初始化简化详情
            simple_details_json = None
            
            # 解析SNMP Trap数据（如果是Trap类型）
            if alert_data.get('type') == 'snmp_trap' or alert_data.get('alert_type') == 'snmp_trap' or alert_data.get('alert_type') == 'ruijie_user_login':
                trap_details = alert_data.get('details', {})
                if trap_details:
                    trap_parser = SNMPTrapParser()
                    parsed_data = trap_parser.parse_trap(trap_details)
                    formatted_message = trap_parser.format_alert_message(parsed_data)
                    simple_alert = trap_parser.format_simple_alert(parsed_data)
                    
                    # 创建告警数据
                    alert_payload = {
                        "type": "new_alert",
                        "alert": {
                            "id": simple_alert.get('alert_type', 'Unknown'),
                            "device_id": alert_data.get('device_id', 'Unknown'),
                            "timestamp": datetime.now().isoformat(),
                            "message": formatted_message,
                            "severity": parsed_data['severity'],
                            "details": simple_alert
                        }
                    }
                    
                    # 发送到WebSocket
                    await manager.broadcast(json.dumps(alert_payload))
                    
                    # 记录到数据库
                    try:
                        db_gen = get_db()
                        db: Session = next(db_gen)
                        
                        # 根据设备IP查找设备ID
                        device = None
                        if 'ruijie_login_ip' in simple_alert and simple_alert['ruijie_login_ip']:
                            device = db.query(Device).filter(Device.management_ip == simple_alert['ruijie_login_ip']).first()
                        elif 'login_ip' in simple_alert and simple_alert['login_ip']:
                            device = db.query(Device).filter(Device.management_ip == simple_alert['login_ip']).first()
                        
                        # 创建告警记录
                        new_alert = Alert(
                            device_id=device.id if device else None,
                            alert_type=simple_alert.get('alert_type', 'snmp_trap'),
                            severity=parsed_data['severity'],
                            message=formatted_message,
                            simple_details=json.dumps(simple_alert, ensure_ascii=False),
                            status="New"
                        )
                        
                        db.add(new_alert)
                        db.commit()
                        db.refresh(new_alert)
                        
                        logger.info(f"告警已保存到数据库，ID: {new_alert.id}")
                    except Exception as e:
                        logger.error(f"保存告警到数据库失败: {str(e)}")
                    finally:
                        if 'db' in locals():
                            db.close()
            
            # 创建告警对象
            # 注意：这里需要确保传入的字段名与模型定义一致
            alert_dict = {
                'device_id': alert_data.get('device_id', 1),  # 默认设备ID为1
                'alert_type': alert_data.get('type') or alert_data.get('alert_type', 'unknown'),
                'severity': alert_data.get('severity', 'Major'),
                'message': alert_data.get('message', ''),
                'status': alert_data.get('status', 'New'),
                'simple_details': simple_details_json
            }
            
            alert = Alert(**alert_dict)
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.info(f"告警记录创建成功: ID={alert.id}, 类型={alert.alert_type}")
            return alert
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库错误，创建告警记录失败: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"创建告警记录失败: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()

    @staticmethod
    def get_alerts(skip: int = 0, limit: int = 100, db: Session = None) -> List[Alert]:
        """
        获取告警列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            db: 数据库会话
            
        Returns:
            告警列表
        """
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
            
        try:
            alerts = db.query(Alert).offset(skip).limit(limit).all()
            return alerts
        except SQLAlchemyError as e:
            logger.error(f"数据库错误，获取告警列表失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"获取告警列表失败: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()

    @staticmethod
    def get_alert(alert_id: int, db: Session = None) -> Alert:
        """
        获取单个告警详情
        
        Args:
            alert_id: 告警ID
            db: 数据库会话
            
        Returns:
            告警对象
        """
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
            
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            return alert
        except SQLAlchemyError as e:
            logger.error(f"数据库错误，获取告警详情失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"获取告警详情失败: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()

    @staticmethod
    def delete_alert(alert_id: int, db: Session = None) -> bool:
        """
        删除告警记录
        
        Args:
            alert_id: 告警ID
            db: 数据库会话
            
        Returns:
            删除是否成功
        """
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
            
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                db.delete(alert)
                db.commit()
                logger.info(f"告警记录删除成功: ID={alert_id}")
                return True
            else:
                logger.warning(f"告警记录不存在: ID={alert_id}")
                return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库错误，删除告警记录失败: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"删除告警记录失败: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()

    @staticmethod
    def get_alerts_by_device(device_id: int, skip: int = 0, limit: int = 100, 
                           db: Session = None) -> List[Alert]:
        """
        根据设备ID获取告警列表
        
        Args:
            device_id: 设备ID
            skip: 跳过的记录数
            limit: 返回的记录数
            db: 数据库会话
            
        Returns:
            告警列表
        """
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
            
        try:
            alerts = db.query(Alert).filter(Alert.device_id == device_id)\
                                   .offset(skip).limit(limit).all()
            return alerts
        except SQLAlchemyError as e:
            logger.error(f"数据库错误，获取设备告警列表失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"获取设备告警列表失败: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()

    @staticmethod
    def get_unresolved_alerts_count(db: Session = None) -> int:
        """
        获取未解决的告警数量
        
        Args:
            db: 数据库会话
            
        Returns:
            未解决的告警数量
        """
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
            
        try:
            count = db.query(Alert).filter(Alert.status != 'resolved').count()
            return count
        except SQLAlchemyError as e:
            logger.error(f"数据库错误，获取未解决告警数量失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"获取未解决告警数量失败: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()