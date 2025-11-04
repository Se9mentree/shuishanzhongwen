
import uuid
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from . import service
from app.database import get_db 


from app.exercise_query import schemas 


router = APIRouter(
    prefix="/lesson",  
    tags=["Lesson Content"]
)

@router.get(
    "/words/{lesson_id}",
    response_model=schemas.LessonWordListResponse, 
    summary="获取课程词语列表"
)
async def get_lesson_words(
    lesson_id: uuid.UUID,          
    req: Request,                   
    db: Session = Depends(get_db)
):
    """
    接收 lesson_id，返回该课程下的所有词语列表，
    包含拼音、翻译和绝对路径的 audio_url。
    """

    base = str(req.base_url)

    word_list_data = service.get_lesson_word_list(
        db=db,
        lesson_id=lesson_id,
        base_url=base,
    )

    if not word_list_data:
        raise HTTPException(
            status_code=404,
            detail=f"未能找到 Lesson ID 为 {lesson_id} 的词语列表。"
        )

    return word_list_data