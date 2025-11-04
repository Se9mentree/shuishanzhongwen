
import uuid
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from . import crud

# 导入共享的模型和 Schema
from app_1.exercise_query import models, schemas
# 导入共享的格式化工具
from app_1.exercise_query.formatter import build_public_url 

def get_lesson_word_list(
    db: Session,
    lesson_id: uuid.UUID,
    base_url: Optional[str] = None
) -> Optional[Dict]:
    """
    获取一个课程下所有词语的详细信息，并格式化 audio_url。
    """
    
    # 1. 从 CRUD 获取数据
    words_from_db = crud.get_words_by_lesson(db, lesson_id)
    
    if not words_from_db:
        return None

    formatted_words = []
    for word in words_from_db:

        formatted_words.append({
            "id": str(word.id),
            "characters": word.characters,
            "pinyin": word.pinyin,
            "translation": word.translation,
            "hsk_level": word.hsk_level,
            "audio_url": build_public_url(
                word.audio_url, 
                base_url
            )
        })
    
    return {
        "lesson_id": str(lesson_id),
        "count": len(formatted_words),
        "words": formatted_words
    }