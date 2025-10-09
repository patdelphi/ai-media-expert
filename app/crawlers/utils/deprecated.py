"""
废弃功能装饰器模块
用于标记已废弃的方法和类
"""

import warnings
from functools import wraps
from typing import Callable, Any


def deprecated(message: str = "This function is deprecated") -> Callable:
    """
    标记函数或方法为已废弃的装饰器
    
    Args:
        message: 废弃警告信息
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} is deprecated: {message}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator