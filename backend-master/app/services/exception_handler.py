from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Union
import logging

logger = logging.getLogger(__name__)

class ExceptionHandler:
    @staticmethod
    async def handle_exception(request: Request, call_next):
        try:
            response = await call_next(request)
        except HTTPException as ex:
            logger.error(f"HTTP exception occurred: {ex.detail}, status_code: {ex.status_code}")
            response = JSONResponse(
                status_code=ex.status_code,
                content={
                    "success": False,
                    "code": ex.status_code,
                    "message": ex.detail,
                    "data": None
                }
            )
        except Exception as ex:
            logger.error(f"Unhandled exception occurred: {str(ex)}", exc_info=True)
            response = JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "code": 500,
                    "message": "服务器内部错误",
                    "data": None
                }
            )
        return response