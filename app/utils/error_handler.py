"""错误处理和异常恢复工具

提供统一的错误处理机制、异常恢复策略和详细的日志记录功能。
"""

import asyncio
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from functools import wraps
import inspect

from app.core.app_logging import download_logger


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"          # 轻微错误，不影响主要功能
    MEDIUM = "medium"    # 中等错误，影响部分功能
    HIGH = "high"        # 严重错误，影响核心功能
    CRITICAL = "critical" # 致命错误，系统无法正常运行


class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"              # 网络相关错误
    PARSING = "parsing"              # 解析相关错误
    DOWNLOAD = "download"            # 下载相关错误
    DATABASE = "database"            # 数据库相关错误
    VALIDATION = "validation"        # 数据验证错误
    AUTHENTICATION = "authentication" # 认证相关错误
    PERMISSION = "permission"        # 权限相关错误
    SYSTEM = "system"                # 系统相关错误
    UNKNOWN = "unknown"              # 未知错误


class DownloadError(Exception):
    """下载相关异常基类"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'details': self.details,
            'recoverable': self.recoverable,
            'timestamp': self.timestamp.isoformat(),
            'type': self.__class__.__name__
        }


class NetworkError(DownloadError):
    """网络相关错误"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, ErrorCategory.NETWORK, **kwargs)
        self.details['status_code'] = status_code


class ParsingError(DownloadError):
    """解析相关错误"""
    
    def __init__(self, message: str, url: Optional[str] = None, platform: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.PARSING, **kwargs)
        self.details.update({
            'url': url,
            'platform': platform
        })


class DownloadTaskError(DownloadError):
    """下载任务相关错误"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.DOWNLOAD, **kwargs)
        self.details['task_id'] = task_id


class ValidationError(DownloadError):
    """数据验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.LOW, **kwargs)
        self.details.update({
            'field': field,
            'value': str(value) if value is not None else None
        })


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class ErrorHandler:
    """错误处理器
    
    提供统一的错误处理、重试机制和恢复策略。
    """
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self.error_callbacks: List[Callable] = []
    
    def register_recovery_strategy(
        self,
        category: ErrorCategory,
        strategy: Callable
    ):
        """注册错误恢复策略
        
        Args:
            category: 错误类别
            strategy: 恢复策略函数
        """
        if category not in self.recovery_strategies:
            self.recovery_strategies[category] = []
        self.recovery_strategies[category].append(strategy)
    
    def register_error_callback(self, callback: Callable):
        """注册错误回调函数
        
        Args:
            callback: 错误回调函数
        """
        self.error_callbacks.append(callback)
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            
        Returns:
            恢复结果（如果成功恢复）
        """
        context = context or {}
        
        # 转换为标准错误格式
        if isinstance(error, DownloadError):
            download_error = error
        else:
            download_error = self._convert_to_download_error(error)
        
        # 记录错误
        await self._log_error(download_error, context)
        
        # 更新错误计数
        error_key = f"{download_error.category.value}:{download_error.message}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # 执行错误回调
        for callback in self.error_callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(download_error, context)
                else:
                    callback(download_error, context)
            except Exception as callback_error:
                download_logger.error(
                    "错误回调执行失败",
                    callback=callback.__name__,
                    error=str(callback_error)
                )
        
        # 尝试恢复
        if download_error.recoverable:
            return await self._attempt_recovery(download_error, context)
        
        return None
    
    def _convert_to_download_error(self, error: Exception) -> DownloadError:
        """将普通异常转换为下载错误
        
        Args:
            error: 原始异常
            
        Returns:
            下载错误对象
        """
        error_message = str(error)
        error_type = type(error).__name__
        
        # 根据异常类型判断类别
        if 'network' in error_message.lower() or 'connection' in error_message.lower():
            category = ErrorCategory.NETWORK
        elif 'parse' in error_message.lower() or 'json' in error_message.lower():
            category = ErrorCategory.PARSING
        elif 'database' in error_message.lower() or 'sql' in error_message.lower():
            category = ErrorCategory.DATABASE
        elif 'permission' in error_message.lower() or 'forbidden' in error_message.lower():
            category = ErrorCategory.PERMISSION
        else:
            category = ErrorCategory.UNKNOWN
        
        # 根据异常类型判断严重程度
        if error_type in ['ConnectionError', 'TimeoutError']:
            severity = ErrorSeverity.MEDIUM
        elif error_type in ['PermissionError', 'AuthenticationError']:
            severity = ErrorSeverity.HIGH
        elif error_type in ['SystemError', 'MemoryError']:
            severity = ErrorSeverity.CRITICAL
        else:
            severity = ErrorSeverity.LOW
        
        return DownloadError(
            message=error_message,
            category=category,
            severity=severity,
            details={
                'original_type': error_type,
                'traceback': traceback.format_exc()
            }
        )
    
    async def _log_error(
        self,
        error: DownloadError,
        context: Dict[str, Any]
    ):
        """记录错误日志
        
        Args:
            error: 下载错误对象
            context: 错误上下文
        """
        log_data = {
            'error_category': error.category.value,
            'error_severity': error.severity.value,
            'error_message': error.message,
            'error_details': error.details,
            'recoverable': error.recoverable,
            'context': context,
            'timestamp': error.timestamp.isoformat()
        }
        
        # 根据严重程度选择日志级别
        if error.severity == ErrorSeverity.CRITICAL:
            download_logger.critical("严重错误", **log_data)
        elif error.severity == ErrorSeverity.HIGH:
            download_logger.error("高级错误", **log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            download_logger.warning("中级错误", **log_data)
        else:
            download_logger.info("轻微错误", **log_data)
    
    async def _attempt_recovery(
        self,
        error: DownloadError,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """尝试错误恢复
        
        Args:
            error: 下载错误对象
            context: 错误上下文
            
        Returns:
            恢复结果
        """
        strategies = self.recovery_strategies.get(error.category, [])
        
        for strategy in strategies:
            try:
                download_logger.info(
                    "尝试错误恢复",
                    strategy=strategy.__name__,
                    error_category=error.category.value
                )
                
                if inspect.iscoroutinefunction(strategy):
                    result = await strategy(error, context)
                else:
                    result = strategy(error, context)
                
                if result is not None:
                    download_logger.info(
                        "错误恢复成功",
                        strategy=strategy.__name__
                    )
                    return result
                    
            except Exception as recovery_error:
                download_logger.warning(
                    "错误恢复策略失败",
                    strategy=strategy.__name__,
                    error=str(recovery_error)
                )
        
        download_logger.warning(
            "所有恢复策略均失败",
            error_category=error.category.value
        )
        return None
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息
        
        Returns:
            错误统计数据
        """
        total_errors = sum(self.error_counts.values())
        
        # 按类别统计
        category_stats = {}
        for error_key, count in self.error_counts.items():
            category = error_key.split(':')[0]
            category_stats[category] = category_stats.get(category, 0) + count
        
        return {
            'total_errors': total_errors,
            'error_counts': dict(self.error_counts),
            'category_distribution': category_stats,
            'most_common_errors': sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


def with_error_handling(
    retry_config: Optional[RetryConfig] = None,
    error_handler: Optional[ErrorHandler] = None
):
    """错误处理装饰器
    
    Args:
        retry_config: 重试配置
        error_handler: 错误处理器
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            config = retry_config or RetryConfig()
            handler = error_handler or default_error_handler
            
            last_error = None
            
            for attempt in range(config.max_attempts):
                try:
                    if inspect.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except Exception as e:
                    last_error = e
                    
                    # 记录重试信息
                    download_logger.warning(
                        f"函数执行失败，尝试重试 ({attempt + 1}/{config.max_attempts})",
                        function=func.__name__,
                        error=str(e),
                        attempt=attempt + 1
                    )
                    
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < config.max_attempts - 1:
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        
                        if config.jitter:
                            import random
                            delay *= (0.5 + random.random() * 0.5)
                        
                        await asyncio.sleep(delay)
            
            # 所有重试都失败，使用错误处理器处理
            context = {
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs),
                'attempts': config.max_attempts
            }
            
            recovery_result = await handler.handle_error(last_error, context)
            if recovery_result is not None:
                return recovery_result
            
            # 如果恢复也失败，重新抛出异常
            raise last_error
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 对于同步函数，创建异步包装
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 默认错误处理器实例
default_error_handler = ErrorHandler()


# 注册默认恢复策略
async def network_recovery_strategy(error: DownloadError, context: Dict[str, Any]):
    """网络错误恢复策略"""
    download_logger.info("执行网络错误恢复策略")
    # 等待一段时间后重试
    await asyncio.sleep(5)
    return None  # 返回None表示需要重试原操作


async def parsing_recovery_strategy(error: DownloadError, context: Dict[str, Any]):
    """解析错误恢复策略"""
    download_logger.info("执行解析错误恢复策略")
    # 可以尝试使用备用解析器
    return None


# 注册默认恢复策略
default_error_handler.register_recovery_strategy(ErrorCategory.NETWORK, network_recovery_strategy)
default_error_handler.register_recovery_strategy(ErrorCategory.PARSING, parsing_recovery_strategy)


# 错误回调函数
async def log_error_callback(error: DownloadError, context: Dict[str, Any]):
    """错误日志回调"""
    download_logger.error(
        "错误回调记录",
        error_dict=error.to_dict(),
        context=context
    )


# 注册默认错误回调
default_error_handler.register_error_callback(log_error_callback)