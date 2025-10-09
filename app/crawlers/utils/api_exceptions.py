"""API异常类定义

定义爬虫模块使用的各种API异常类型。
"""


class APIException(Exception):
    """API异常基类"""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class APIError(APIException):
    """通用API错误"""
    pass


class APIConnectionError(APIException):
    """API连接错误"""
    pass


class APIResponseError(APIException):
    """API响应错误"""
    pass


class APIUnauthorizedError(APIException):
    """API未授权错误"""
    pass


class APINotFoundError(APIException):
    """API未找到错误"""
    pass


class APIUnavailableError(APIException):
    """API不可用错误"""
    pass


class APITimeoutError(APIException):
    """API超时错误"""
    pass


class APIRateLimitError(APIException):
    """API限流错误"""
    pass


class APIValidationError(APIException):
    """API验证错误"""
    pass