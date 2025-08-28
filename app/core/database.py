"""数据库配置和连接管理

提供数据库连接、会话管理和基础模型类。
"""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, Integer, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建基础模型类
Base = declarative_base()


class BaseModel(Base):
    """基础模型类
    
    提供所有模型的通用字段和方法。
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# 数据库引擎配置
if settings.database_url.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )
    async_engine = None
else:
    # PostgreSQL配置
    engine = create_engine(
        settings.database_url_sync,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    
    # 异步引擎（如果需要）
    async_engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 异步会话工厂
if async_engine:
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
else:
    AsyncSessionLocal = None


def get_db():
    """获取数据库会话
    
    用于依赖注入的数据库会话生成器。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话
    
    用于异步操作的数据库会话生成器。
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Async database session not configured")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def create_tables():
    """创建数据库表"""
    # 导入所有模型以确保它们被注册到Base.metadata中
    from app.models import user, video  # noqa: F401
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除数据库表"""
    Base.metadata.drop_all(bind=engine)


async def create_tables_async():
    """异步创建数据库表"""
    if not async_engine:
        raise RuntimeError("Async engine not configured")
    
    # 导入所有模型以确保它们被注册到Base.metadata中
    from app.models import user, video  # noqa: F401
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables_async():
    """异步删除数据库表"""
    if not async_engine:
        raise RuntimeError("Async engine not configured")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)