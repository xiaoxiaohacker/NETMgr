import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.services.config import DATABASE_URL, DEBUG

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建数据库引擎
try:
    # SQLite数据库需要特殊的配置
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            echo=DEBUG  # 在调试模式下输出SQL语句
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=DEBUG  # 在调试模式下输出SQL语句
        )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# 创建数据库会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖项函数
    提供数据库会话，并确保在使用后正确关闭
    """
    db = SessionLocal()
    try:
        yield db
        # 如果没有异常，尝试提交事务
        if db.is_active:
            try:
                db.commit()
            except SQLAlchemyError as e:
                logger.error(f"Database commit failed: {str(e)}")
                db.rollback()
                raise
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        # 确保回滚事务
        if db.is_active:
            db.rollback()
        raise
    finally:
        # 确保关闭会话
        if db.is_active:
            db.close()
            logger.debug("Database session closed")