"""通用数据模式

定义API响应的通用数据结构。
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# 泛型类型变量
DataType = TypeVar('DataType')


class ResponseModel(BaseModel, Generic[DataType]):
    """统一API响应模型
    
    所有API接口都使用这个统一的响应格式。
    """
    code: int = Field(description="响应状态码")
    message: str = Field(description="响应消息")
    data: Optional[DataType] = Field(default=None, description="响应数据")
    
    model_config = ConfigDict(
        json_encoders={},
    )


class PaginationParams(BaseModel):
    """分页参数模型"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[DataType]):
    """分页响应模型"""
    items: list[DataType] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    
    @classmethod
    def create(
        cls,
        items: list[DataType],
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse[DataType]":
        """创建分页响应"""
        pages = (total + size - 1) // size  # 向上取整
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class ErrorDetail(BaseModel):
    """错误详情模型"""
    field: Optional[str] = Field(default=None, description="错误字段")
    message: str = Field(description="错误消息")
    code: Optional[str] = Field(default=None, description="错误代码")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int = Field(description="HTTP状态码")
    message: str = Field(description="错误消息")
    details: Optional[list[ErrorDetail]] = Field(default=None, description="错误详情列表")
    timestamp: str = Field(description="错误时间戳")
    path: Optional[str] = Field(default=None, description="请求路径")


class HealthCheck(BaseModel):
    """健康检查响应模型"""
    status: str = Field(description="服务状态")
    timestamp: str = Field(description="检查时间")
    version: Optional[str] = Field(default=None, description="应用版本")
    environment: Optional[str] = Field(default=None, description="运行环境")
    

class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str = Field(description="任务ID")
    status: str = Field(description="任务状态")
    progress: int = Field(ge=0, le=100, description="进度百分比")
    message: Optional[str] = Field(default=None, description="状态消息")
    created_at: str = Field(description="创建时间")
    started_at: Optional[str] = Field(default=None, description="开始时间")
    completed_at: Optional[str] = Field(default=None, description="完成时间")
    error_message: Optional[str] = Field(default=None, description="错误消息")


class FileInfo(BaseModel):
    """文件信息模型"""
    filename: str = Field(description="文件名")
    size: int = Field(description="文件大小（字节）")
    content_type: str = Field(description="文件类型")
    url: Optional[str] = Field(default=None, description="文件访问URL")
    created_at: str = Field(description="创建时间")
