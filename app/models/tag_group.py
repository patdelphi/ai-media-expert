"""标签组相关数据模型

定义标签组和标签的数据模型。
"""

from typing import List
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.database import BaseModel


class TagGroup(BaseModel):
    """标签组模型"""
    __tablename__ = "tag_groups"
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关联关系
    tags = relationship("TagGroupTag", back_populates="tag_group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TagGroup(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "tags": [tag.to_dict() for tag in self.tags],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TagGroupTag(BaseModel):
    """标签组标签模型"""
    __tablename__ = "tag_group_tags"
    
    name = Column(String(50), nullable=False, index=True)
    color = Column(String(7), nullable=True)  # 十六进制颜色代码
    tag_group_id = Column(Integer, ForeignKey("tag_groups.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关联关系
    tag_group = relationship("TagGroup", back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', group_id={self.tag_group_id})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "tag_group_id": self.tag_group_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }