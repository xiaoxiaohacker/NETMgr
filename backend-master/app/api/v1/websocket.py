from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
import logging
from app.services.auth import decode_access_token
from app.services.db import SessionLocal  # 导入SessionLocal
from app.services.models import Device

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

# 存储活跃的WebSocket连接
active_connections: Dict[str, List[WebSocket]] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    def add_connection(self, websocket: WebSocket, user_id: str):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket连接已添加，用户: {user_id}, 当前连接数: {len(self.active_connections[user_id])}")

    def remove_connection(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            # 如果用户没有其他连接，则删除用户键
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket连接已移除，用户: {user_id}")

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"发送WebSocket消息失败: {e}")
                    # 移除失效的连接
                    try:
                        self.active_connections[user_id].remove(connection)
                        await connection.close()
                    except:
                        pass

    async def broadcast_to_all(self, message: dict):
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, message)

manager = ConnectionManager()

@router.websocket("/ws/device-status")
async def websocket_device_status(websocket: WebSocket):
    await websocket.accept()
    
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("WebSocket连接缺少token")
        await websocket.close(code=1008, reason="缺少认证token")
        return
    
    logger.info(f"收到WebSocket连接请求，尝试解码token: {token[:20]}...")  # 记录token前20个字符
    
    try:
        username = decode_access_token(token)
        logger.info(f"解码结果: {username}")
    except Exception as e:
        logger.error(f"解码token时发生异常: {e}")
        await websocket.close(code=1008, reason="认证失败")
        return
    
    if not username:
        logger.warning("WebSocket连接认证失败 - 无法解码用户名")
        await websocket.close(code=1008, reason="认证失败")
        return
    
    # 使用用户名作为用户标识
    user_id = username
    
    try:
        manager.add_connection(websocket, user_id)
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "status": "connected",
            "message": f"WebSocket连接已建立，用户: {user_id}"
        }, ensure_ascii=False))
        
        # 保持连接
        while True:
            # 等待消息（但主要用于保持连接）
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # 可以处理客户端发送的消息
                message = json.loads(data)
                logger.info(f"收到WebSocket消息: {message}")
            except asyncio.TimeoutError:
                # 发送ping消息以保持连接
                try:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "message": "keepalive"
                    }, ensure_ascii=False))
                except:
                    break
            except Exception as e:
                logger.info(f"接收WebSocket消息时出错: {e}")
                break
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开，用户: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket连接异常，用户: {user_id}, 错误: {e}")
    finally:
        manager.remove_connection(websocket, user_id)

# 全局函数，用于从其他模块发送设备状态更新
async def send_device_status_update(device_id: int, status: str, message: str = None):
    """发送设备状态更新到所有连接的客户端"""
    update_message = {
        "type": "device_status_update",
        "device_id": device_id,
        "status": status,
        "message": message or f"设备 {device_id} 状态更新为 {status}"
    }
    await manager.broadcast_to_all(update_message)

async def send_batch_device_status_update(updates: List[Dict]):
    """发送批量设备状态更新"""
    batch_message = {
        "type": "batch_device_status_update",
        "updates": updates
    }
    await manager.broadcast_to_all(batch_message)