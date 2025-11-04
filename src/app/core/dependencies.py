# app/core/dependencies.py
"""
依赖函数：从请求中提取用户信息
"""
from fastapi import Header, HTTPException, status, Query
from typing import Optional
import uuid
from .security import verify_token


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(
        default=None,
        description="可选显式 token（主要用于 Swagger 调试）"
    )
) -> uuid.UUID:
    """
    从 Authorization 请求头中提取用户ID

    使用方式：
    - 请求头中传入: Authorization: Bearer <token>
    """
    token_value: Optional[str] = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token_value = parts[1]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的 Authorization 格式，应为 'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if not token_value and token:
        token_value = token

    if not token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证信息，请提供 Authorization 头",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token_value)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少 user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return uuid.UUID(user_id_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 user_id 格式",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
