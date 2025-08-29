"""系统配置相关数据模型

定义系统配置项的数据模型。
"""

from sqlalchemy import Boolean, Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func

from app.core.database import BaseModel


class SystemConfig(BaseModel):
    """系统配置模型"""
    __tablename__ = "system_configs"
    
    key = Column(String(100), unique=True, index=True, nullable=False, comment="配置键")
    value = Column(Text, nullable=False, comment="配置值")
    description = Column(Text, nullable=True, comment="配置描述")
    category = Column(String(50), nullable=False, default="general", comment="配置分类")
    
    # 配置属性
    is_public = Column(Boolean, default=False, nullable=False, comment="是否为公开配置")
    is_encrypted = Column(Boolean, default=False, nullable=False, comment="是否加密存储")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    
    # 数据类型
    data_type = Column(String(20), default="string", nullable=False, comment="数据类型")
    
    # 验证规则
    validation_rule = Column(Text, nullable=True, comment="验证规则（JSON格式）")
    default_value = Column(Text, nullable=True, comment="默认值")
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', category='{self.category}')>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典，可选择是否包含敏感信息"""
        data = {
            "id": self.id,
            "key": self.key,
            "description": self.description,
            "category": self.category,
            "is_public": self.is_public,
            "is_active": self.is_active,
            "data_type": self.data_type,
            "default_value": self.default_value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
        # 只有在需要敏感信息或配置为公开时才包含值
        if include_sensitive or self.is_public:
            data["value"] = self.value
        
        if include_sensitive:
            data["is_encrypted"] = self.is_encrypted
            data["validation_rule"] = self.validation_rule
        
        return data
    
    @classmethod
    def get_by_key(cls, db, key: str):
        """根据键获取配置"""
        return db.query(cls).filter(cls.key == key, cls.is_active == True).first()
    
    @classmethod
    def get_by_category(cls, db, category: str, include_inactive=False):
        """根据分类获取配置列表"""
        query = db.query(cls).filter(cls.category == category)
        if not include_inactive:
            query = query.filter(cls.is_active == True)
        return query.order_by(cls.key).all()
    
    @classmethod
    def get_public_configs(cls, db):
        """获取所有公开配置"""
        return db.query(cls).filter(
            cls.is_public == True,
            cls.is_active == True
        ).order_by(cls.category, cls.key).all()