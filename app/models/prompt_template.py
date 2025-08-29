"""提示词模板数据模型

定义提示词模板相关的数据模型。
"""

from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import BaseModel


class PromptTemplate(BaseModel):
    """提示词模板模型"""
    __tablename__ = "prompt_templates"
    
    title = Column(String(200), nullable=False)  # 模板标题
    content = Column(Text, nullable=False)  # 模板内容
    is_active = Column(Boolean, default=True)  # 是否启用
    usage_count = Column(Integer, default=0)  # 使用次数
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, title={self.title})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }