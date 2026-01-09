from sqlalchemy import text
from app.services.db import engine
import redis
import logging
from app.services.config import REDIS_URL

logger = logging.getLogger(__name__)

class HealthCheckService:
    """系统健康检查服务"""
    
    @staticmethod
    def check_database():
        """检查数据库连接"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"数据库连接检查失败: {str(e)}")
            return False
    
    @staticmethod
    def check_redis():
        """检查Redis连接（如果配置了Redis）"""
        if not REDIS_URL:
            return True  # 如果没有配置Redis，则视为正常
        
        try:
            redis_client = redis.from_url(REDIS_URL)
            redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis连接检查失败: {str(e)}")
            return False
    
    @classmethod
    def get_system_health(cls):
        """获取系统整体健康状况"""
        db_status = cls.check_database()
        redis_status = cls.check_redis()
        
        overall_status = db_status and redis_status
        
        return {
            "overall_status": "healthy" if overall_status else "unhealthy",
            "checks": {
                "database": {
                    "status": "healthy" if db_status else "unhealthy",
                    "message": "Database connection successful" if db_status else "Database connection failed"
                },
                "redis": {
                    "status": "healthy" if redis_status else "unhealthy", 
                    "message": "Redis connection successful" if redis_status else "Redis connection failed"
                }
            }
        }