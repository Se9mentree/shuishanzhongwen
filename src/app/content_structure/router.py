from fastapi import APIRouter, HTTPException
from typing import List

from app.utils.util import _db 


from app.content_structure import schema
from app.content_structure import service
import uuid 
import json

router = APIRouter()

@router.get(
    "/api/v2/content-structure",  
    response_model=List[schema.PhaseResponse],
    tags=["内容结构 (Content Structure)"] 
)
async def get_full_content_structure():

    conn = None
    cur = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        result = await service.get_full_content_structure(cur)
        
        
        return result

    except (Exception, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"获取内容结构时发生错误: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get(
    "/api/v2/lesson/{lesson_id}/dialogue",
    response_model=schema.DialogueResponse,
    tags=["内容结构 (Content Structure)"],
    summary="获取单个课程的对话内容"
)
async def get_lesson_dialogue(lesson_id: uuid.UUID):
    """
    根据课程 ID (Lesson ID) 获取该课程的 JSON 格式对话内容。
    如果课程不存在或对话字段为空，将返回 404。
    """
    conn = None
    cur = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用新的 service 函数
        result_data = await service.get_dialogue_by_lesson_id(cur, str(lesson_id))
        
        if not result_data:
            raise HTTPException(status_code=404, detail="Lesson not found or dialogue is empty")
        
        # FastAPI 会自动使用 DialogueResponse 模型来验证这个字典
        return result_data

    except json.JSONDecodeError as e:
        # 捕获 service 层可能抛出的 JSON 解析错误 (如果数据库数据损坏)
        raise HTTPException(status_code=500, detail=f"对话数据格式错误，无法解析: {str(e)}")
    except (Exception, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"获取对话时发生错误: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get(
    "/api/v2/scenarios",
    response_model=List[schema.ScenarioResponse],
    tags=["场景系统 (Scenario System)"],
    summary="获取所有场景及其关联课程的详细信息"
)
async def get_all_scenarios():
    """
    获取所有场景 (Scenario) 的名称、描述和排序，以及该场景下所有关联课程的 ID 和相关性排序。
    """
    conn = None
    cur = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用 service 层函数获取数据
        result = await service.get_all_scenarios_with_lessons(cur)
        
        return result

    except (Exception, ValueError) as e:
        # 捕获数据库或处理错误，返回 500 错误
        raise HTTPException(status_code=500, detail=f"获取场景信息时发生错误: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()