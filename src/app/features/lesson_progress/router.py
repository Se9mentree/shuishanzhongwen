from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ResponseModel
from app.core.dependencies import get_current_user_id
from .service import LessonProgressService
import uuid


router = APIRouter(prefix="/lesson-progress", tags=["课程进度"])


@router.get("", response_model=ResponseModel, summary="获取课程解锁进度")
def get_lesson_progress(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取指定用户的课程解锁进度。

    通过请求头中的 Authorization: Bearer <token> 自动获取用户ID

    Args:
        user_id: 从 token 中自动提取的用户ID

    Returns:
        包含课程解锁进度信息的响应。
    """
    progress = LessonProgressService.get_lesson_progress(db, user_id)

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
