"""全局异常处理中间件

处理应用中的所有异常，提供统一的错误响应格式。
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
from typing import Union

logger = logging.getLogger(__name__)

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # FastAPI HTTPException 直接返回
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except SQLAlchemyError as e:
            # 数据库异常
            logger.error(f"Database error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "数据库操作失败"}
            )
        except Exception as e:
            # 其他未处理的异常
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "服务器内部错误"}
            )