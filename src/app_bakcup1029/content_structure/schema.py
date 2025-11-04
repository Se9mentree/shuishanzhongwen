from __future__ import annotations
import uuid
from pydantic import BaseModel, ConfigDict
from typing import List,Union



class LessonResponse(BaseModel):
    """
    嵌套在 Topic 中的课程响应模型
    """
    id: uuid.UUID
    lesson_name: str
    display_order: int
    dialogue: Union[str, None] = None
    model_config = ConfigDict(from_attributes=True) 


class TopicResponse(BaseModel):
    """
    嵌套在 Phase 中的主题响应模型
    """
    id: uuid.UUID
    topic_name: str
    topic_order: int
    lessons: List[LessonResponse] # 嵌套 Lesson 列表
    
    model_config = ConfigDict(from_attributes=True)


class PhaseResponse(BaseModel):
    """
    获取内容结构的顶层响应模型
    """
    id: uuid.UUID
    name: str
    display_order: int
    topics: List[TopicResponse] # 嵌套 Topic 列表
    
    model_config = ConfigDict(from_attributes=True)

class DialogueRole(BaseModel):
    roleId: int
    roleName: str

class DialogueEntry(BaseModel):
    dialogueId: int
    roleId: int
    text: str
    textEn: str
    pinyin: str


class DialogueResponse(BaseModel):
    """
    获取单个课程对话的响应模型
    """
    roles: List[DialogueRole]
    dialogues: List[DialogueEntry]


class ScenarioLessonDetail(BaseModel):
    """
    嵌套在 Scenario 中的课程详情模型，包含关联信息
    """
    lesson_id: uuid.UUID
    lesson_name: str
    relevance_order: int
    
    model_config = ConfigDict(from_attributes=True) 

class ScenarioResponse(BaseModel):
    """
    场景的顶级响应模型
    """
    id: uuid.UUID
    name: str
    description: str
    display_order: int
    lessons: List[ScenarioLessonDetail] # 嵌套课程列表
    
    model_config = ConfigDict(from_attributes=True)