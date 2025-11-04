
import uuid
from typing import List
from sqlalchemy.orm import Session

# 从 exercise_query 导入共享 models
from app.exercise_query import models

def get_words_by_lesson(db: Session, lesson_id: uuid.UUID) -> List[models.Word]:
    """
    根据 lesson_id 高效地查询所有关联的 Word 对象。
    通过 LessonWord 表进行 JOIN。
    """
    #
    return db.query(models.Word)\
        .join(models.LessonWord, models.Word.id == models.LessonWord.word_id)\
        .filter(models.LessonWord.lesson_id == lesson_id)\
        .all()