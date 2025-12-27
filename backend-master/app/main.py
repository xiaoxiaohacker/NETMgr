from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from app.services.db import Base, engine
from app.services.models import SystemLog
from app.api.v1 import auth_router, devices_router, tasks_router, dashboard_router, device_stats_router, alerts_router, logs_router, settings_router, topology_router, snmp_router, config_backup_router, users_router  # 添加users_router
from app.new_dashboard import router as new_dashboard_router
from app.api.v1.websocket import router as websocket_router  # 导入WebSocket路由
from app.services.cors_config import ALLOWED_ORIGINS, ALLOWED_METHODS, ALLOWED_HEADERS
from app.services.config import REDIS_URL
from app.scheduler import TaskScheduler
from app.services.device_status_checker import device_status_checker  # 导入设备状态检查器
import os
import json
from typing import Any
from fastapi.responses import JSONResponse
import logging

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 自定义JSONResponse，确保UTF-8编码
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# 创建FastAPI应用实例
app = FastAPI(
    title="NetMgr API",
    description="网络设备管理系统API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    default_response_class=UTF8JSONResponse
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)

# 挂载静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend", "dist")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 注册API路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["设备管理"])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["任务管理"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["仪表板"])
app.include_router(device_stats_router, prefix="/api/v1/device-stats", tags=["设备统计"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["告警管理"])
app.include_router(logs_router, prefix="/api/v1/logs", tags=["日志管理"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["系统设置"])
app.include_router(topology_router, prefix="/api/v1/topology", tags=["网络拓扑"])
app.include_router(snmp_router, prefix="/api/v1/snmp", tags=["SNMP管理"])
app.include_router(config_backup_router, prefix="/api/v1/config-backup", tags=["配置备份"])
app.include_router(users_router, prefix="/api/v1/users", tags=["用户管理"])  # 添加用户管理路由

# 注册WebSocket路由
app.include_router(websocket_router, tags=["WebSocket"])

# 注册新仪表板路由
app.include_router(new_dashboard_router, prefix="/api/dashboard", tags=["新仪表板"])

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Network Manager API - Swagger UI",
        oauth2_redirect_url=None,
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Network Manager API - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="Network Manager API", version=app.version, routes=app.routes))

@app.get("/")
async def root():
    return {"message": "欢迎使用网络设备管理系统API"}

# 应用启动事件处理器
@app.on_event("startup")
async def startup_event():
    """应用启动事件处理"""
    logger.info("NetMgr 应用正在启动...")
    
    # ✅ 自动创建数据库表
    Base.metadata.create_all(bind=engine)

    # 检查并填充模拟数据（如果数据库为空）
    # try:
    #     from app.services.mock_data import populate_mock_data
    #     populate_mock_data()
    # except Exception as e:
    #     logger.error(f"填充模拟数据时出错: {str(e)}")

    # 初始化 Celery（仅在Redis可用时）
    try:
        from celery import Celery
        celery_app = Celery(__name__)
        celery_app.conf.broker_url = REDIS_URL
        celery_app.conf.result_backend = REDIS_URL
        logger.info("Celery已初始化")
    except Exception as e:
        logger.error(f"Celery初始化失败: {str(e)}")

    # 启动SNMP Trap监听器（在后台线程中运行）
    try:
        import threading
        from app.services.snmp_trap_listener import start_trap_listener, get_snmp_config
        
        # 获取SNMP配置
        snmp_config = get_snmp_config()
        bind_address = snmp_config.get("trap_listen_address", "0.0.0.0")
        bind_port = snmp_config.get("trap_listen_port", 162)
        
        # 在非守护线程中启动SNMP Trap监听器
        trap_thread = threading.Thread(
            target=start_trap_listener, 
            args=(bind_address, bind_port),
            daemon=False
        )
        trap_thread.start()
        logger.info(f"SNMP Trap监听器已在后台线程中启动，监听地址: {bind_address}:{bind_port}")
    except Exception as e:
        logger.error(f"启动SNMP Trap监听器失败: {str(e)}")

    # 启动设备状态检查器
    try:
        device_status_checker.start()
        logger.info(f"设备状态检查器已启动，检查间隔: {device_status_checker.check_interval}秒")
    except Exception as e:
        logger.error(f"启动设备状态检查器失败: {str(e)}")

    # 初始化并启动任务调度器
    from app.scheduler import scheduler
    scheduler.start()

    logger.info("NetMgr 应用启动完成")
    
    # 记录系统日志
    try:
        from app.services.db import get_db
        db = next(get_db())
        from app.services.system_log import create_system_log
        create_system_log(
            db=db,
            level="INFO",
            module="SYSTEM",
            message="NetMgr 应用已成功启动",
            device_id=None
        )
        db.close()
    except Exception as log_error:
        logger.error(f"记录系统日志失败: {str(log_error)}")


# 应用关闭事件处理器
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件处理"""
    logger.info("NetMgr 应用正在关闭...")
    
    # 停止设备状态检查器
    try:
        device_status_checker.stop()
        logger.info("设备状态检查器已停止")
    except Exception as e:
        logger.error(f"停止设备状态检查器失败: {str(e)}")

    # 停止任务调度器
    try:
        from app.scheduler import scheduler
        if scheduler.running:
            scheduler.shutdown()
            logger.info("任务调度器已关闭")
    except Exception as e:
        logger.error(f"关闭任务调度器失败: {str(e)}")

    logger.info("NetMgr 应用关闭完成")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常处理器捕获到未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": f"服务器内部错误: {str(exc)}", "success": False}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    logger.warning(f"未找到资源: {request.url}")
    return JSONResponse(
        status_code=404,
        content={"message": "请求的资源不存在", "success": False}
    )

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: Exception):
    logger.warning(f"未授权访问: {request.url}")
    return JSONResponse(
        status_code=401,
        content={"message": "未授权访问，请重新登录", "success": False}
    )

@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: Exception):
    logger.warning(f"访问被禁止: {request.url}")
    return JSONResponse(
        status_code=403,
        content={"message": "访问被拒绝", "success": False}
    )
