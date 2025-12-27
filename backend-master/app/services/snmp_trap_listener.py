import logging
from typing import Dict, Any
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.proto.api import v2c
from sqlalchemy.orm import Session
from app.services.db import get_db
from app.services.models import Alert, Device
from app.services.snmp_config import get_snmp_config
from app.utils.trap_parser import SNMPTrapParser
import json

# 配置日志记录器
logger = logging.getLogger(__name__)

class SNMPTrapListener:
    """SNMP Trap监听器，用于接收网络设备发送的告警信息"""
    
    def __init__(self, bind_address: str = None, bind_port: int = None):
        """
        初始化SNMP Trap监听器
        
        Args:
            bind_address: 监听地址，默认从配置文件读取
            bind_port: 监听端口，默认从配置文件读取
        """
        # 获取SNMP配置
        snmp_config = get_snmp_config()
        
        self.bind_address = bind_address if bind_address is not None else snmp_config.get("trap_listen_address", "0.0.0.0")
        self.bind_port = bind_port if bind_port is not None else snmp_config.get("trap_listen_port", 162)
        self.community_strings = snmp_config.get("community_strings", ["public"])
        self.allowed_hosts = snmp_config.get("allowed_hosts", [])
        self.snmp_engine = None
        
    def start(self):
        """启动SNMP Trap监听器"""
        try:
            logger.info(f"正在启动SNMP Trap监听器，监听地址: {self.bind_address}:{self.bind_port}")
            
            # 创建SNMP引擎
            self.snmp_engine = engine.SnmpEngine()

            # 配置传输层
            config.addTransport(
                self.snmp_engine,
                udp.domainName + (1,),
                udp.UdpTransport().openServerMode((self.bind_address, self.bind_port))
            )

            # 注册SNMP社区字符串
            for i, community in enumerate(self.community_strings):
                config.addV1System(self.snmp_engine, f'my-area-{i}', community)

            # 配置安全模型
            config.addTargetParams(
                self.snmp_engine, 'my-creds', 'my-area-0', 'noAuthNoPriv', 1
            )

            # 注册通知接收回调
            ntfrcv.NotificationReceiver(self.snmp_engine, self._trap_callback)
            
            logger.info("SNMP Trap监听器启动成功")
            
            # 开始监听
            self.snmp_engine.transportDispatcher.jobStarted(1)
            
            # 等待接收Trap
            try:
                self.snmp_engine.transportDispatcher.runDispatcher()
            except KeyboardInterrupt:
                self.snmp_engine.transportDispatcher.closeDispatcher()
                logger.info("SNMP Trap监听器已停止")
                
        except Exception as e:
            logger.error(f"启动SNMP Trap监听器失败: {str(e)}")
            raise

    def _trap_callback(self, snmpEngine, stateReference, contextEngineId, contextName,
                      varBinds, cbCtx):
        """
        SNMP Trap回调函数
        
        Args:
            snmpEngine: SNMP引擎
            stateReference: 状态引用
            contextEngineId: 上下文引擎ID
            contextName: 上下文名称
            varBinds: 变量绑定列表
            cbCtx: 回调上下文
        """
        try:
            # 获取源地址信息
            transportDomain, transportAddress = snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)
            source_ip = transportAddress[0] if transportAddress else "Unknown"
            
            # 检查是否在允许的主机列表中（如果配置了的话）
            if self.allowed_hosts and source_ip not in self.allowed_hosts:
                logger.warning(f"拒绝来自未授权主机 {source_ip} 的Trap消息")
                return
            
            logger.info(f"收到来自 {source_ip} 的SNMP Trap消息")
            
            # 解析Trap数据
            trap_data = {}
            for oid, value in varBinds:
                oid_str = self._format_value(oid)
                value_str = self._format_value(value)
                trap_data[oid_str] = value_str
                
            # 保存告警到数据库
            self._save_alert(trap_data, source_ip)
            
        except Exception as e:
            logger.error(f"处理SNMP Trap消息失败: {str(e)}")

    def _format_value(self, value) -> str:
        """
        格式化SNMP值
        
        Args:
            value: SNMP值对象
            
        Returns:
            格式化后的字符串值
        """
        if isinstance(value, v2c.ObjectIdentifier):
            return str(value)
        elif isinstance(value, v2c.Integer):
            return str(int(value))
        elif isinstance(value, v2c.OctetString):
            # 尝试解码为UTF-8字符串
            try:
                return value.asOctets().decode('utf-8')
            except UnicodeDecodeError:
                # 如果无法解码为UTF-8，则返回十六进制表示
                return value.prettyPrint()
        elif isinstance(value, v2c.IpAddress):
            return str(value)
        elif isinstance(value, v2c.Counter32):
            return str(int(value))
        elif isinstance(value, v2c.Gauge32):
            return str(int(value))
        elif isinstance(value, v2c.TimeTicks):
            return str(int(value))
        elif isinstance(value, v2c.Opaque):
            return str(value)
        elif isinstance(value, v2c.Counter64):
            return str(int(value))
        else:
            return str(value)

    def _save_alert(self, trap_data: Dict[str, Any], source_ip: str):
        """
        保存告警到数据库
        
        Args:
            trap_data: 解析后的Trap数据
            source_ip: 发送Trap的设备IP地址
        """
        db_session = None
        try:
            # 创建数据库会话
            db_gen = get_db()
            db_session: Session = next(db_gen)
            
            # 根据IP查找设备
            device = db_session.query(Device).filter(Device.management_ip == source_ip).first()
            device_id = device.id if device else None
            
            # 初始化简化详情
            simple_details_json = None
            
            # 解析SNMP Trap数据
            trap_parser = SNMPTrapParser()
            parsed_data = trap_parser.parse_trap(trap_data)
            formatted_message = trap_parser.format_alert_message(parsed_data)
            simple_alert = trap_parser.format_simple_alert(parsed_data)
            
            # 添加简化信息
            simple_details_json = json.dumps(simple_alert, ensure_ascii=False)
            
            # 创建告警对象
            alert = Alert(
                device_id=device_id,
                alert_type="snmp_trap",
                severity=self._determine_severity(trap_data),
                message=formatted_message,
                simple_details=simple_details_json,
                status="New"
            )
            
            # 添加到数据库
            db_session.add(alert)
            db_session.commit()
            db_session.refresh(alert)
            
            logger.info(f"SNMP Trap告警已保存到数据库，ID: {alert.id}")
            
            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db_session,
                    level="INFO",
                    module="ALERT",
                    message=f"收到SNMP Trap告警，设备IP: {source_ip}，告警类型: {alert.alert_type}，严重性: {alert.severity}",
                    device_id=device_id
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")
            
        except Exception as e:
            logger.error(f"保存SNMP Trap告警到数据库失败: {str(e)}")
            if db_session:
                db_session.rollback()
                
            # 记录系统日志
            try:
                from app.services.system_log import create_system_log
                create_system_log(
                    db=db_session,
                    level="ERROR",
                    module="ALERT",
                    message=f"保存SNMP Trap告警失败: {str(e)}",
                    device_id=device_id
                )
            except Exception as log_error:
                logger.error(f"记录系统日志失败: {str(log_error)}")
        finally:
            # 关闭数据库会话
            if db_session:
                db_session.close()

    def _determine_severity(self, trap_data: Dict[str, Any]) -> str:
        """
        根据Trap数据确定告警严重性
        
        Args:
            trap_data: 解析后的Trap数据
            
        Returns:
            告警严重性 (Critical, Major, Minor, Warning)
        """
        # 检查是否有明显的严重性指示
        trap_message = self._format_trap_message(trap_data).lower()
        
        # 根据常见的Trap内容确定严重性
        if any(keyword in trap_message for keyword in ["critical", "failure", "down", "error"]):
            return "Critical"
        elif any(keyword in trap_message for keyword in ["warning", "warn"]):
            return "Warning"
        elif any(keyword in trap_message for keyword in ["major"]):
            return "Major"
        elif any(keyword in trap_message for keyword in ["minor"]):
            return "Minor"
        else:
            # 默认返回Major
            return "Major"

    def _format_trap_message(self, trap_data: Dict[str, Any]) -> str:
        """
        格式化Trap消息
        
        Args:
            trap_data: 解析后的Trap数据
            
        Returns:
            格式化后的消息字符串
        """
        message_parts = []
        for oid, value in trap_data.items():
            message_parts.append(f"{oid}={value}")
        return "; ".join(message_parts)

# 创建全局SNMP Trap监听器实例
_trap_listener = None

def get_trap_listener(bind_address: str = None, bind_port: int = None) -> SNMPTrapListener:
    """
    获取SNMP Trap监听器单例实例
    
    Returns:
        SNMPTrapListener实例
    """
    global _trap_listener
    if _trap_listener is None:
        _trap_listener = SNMPTrapListener(bind_address, bind_port)
    return _trap_listener

def start_trap_listener(bind_address: str = None, bind_port: int = None):
    """启动SNMP Trap监听器"""
    listener = get_trap_listener(bind_address, bind_port)
    listener.start()