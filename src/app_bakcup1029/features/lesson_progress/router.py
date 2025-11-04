from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app_1.database import get_db
from app_1.schemas import ResponseModel
from .service import LessonProgressService
import uuid


router = APIRouter(prefix="/lesson-progress", tags=["课程进度"])


@router.get("", response_model=ResponseModel, summary="获取课程解锁进度")
def get_lesson_progress(
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定用户的课程解锁进度。

    Args:
        user_id: 用户ID（字符串形式的UUID）

    Returns:
        包含课程解锁进度信息的响应。
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return {
            "code": 0,
            "message": "无效的用户ID格式",
            "data": None
        }

    progress = LessonProgressService.get_lesson_progress(db, user_uuid)

    if progress is None:
        return {
            "code": 0,
            "message": "未找到课程进度信息",
            "data": None
        }

    return {
        "code": 1,
        "message": "获取成功",
        "data": progress
    }
