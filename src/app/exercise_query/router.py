from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from . import schemas
from . import service
from app.database import get_db


router = APIRouter(
    prefix="/queryquestion",
    tags=["Question Query"]
)

# 2. 定义 POST /queryquestion/get-exercises 端点
@router.post(
    "/get-exercises",
    response_model=schemas.ExerciseResponse,
    summary="获取练习题目列表"
)
async def get_exercises(
    request: schemas.ExerciseRequest,
    req: Request,                       # ← 新增：注入 Request 以获取 base_url
    db: Session = Depends(get_db)
):
    """
    接收前端的练习请求，并返回一个根据要求动态生成的题目列表。

    - **request**: 请求体数据，FastAPI 会使用 `schemas.ExerciseRequest` 解析校验。
    - **db**: 依赖注入，确保每个请求使用独立的数据库会话。
    - **req**: 当前请求对象，用于获取 base_url（如 "http://127.0.0.1:8000/"），
      传递给 service 层在生成媒体 URL 时拼出绝对地址。
    """
    # 例如 "http://127.0.0.1:8000/"
    base = str(req.base_url)

    # 传入 base_url，让 service 在构造题目时用 build_public_url(...) 拼成绝对 URL
    exercise_session = service.create_exercise_session(
        db=db,
        request=request,
        base_url=base,                  # ← 新增：把 base_url 传下去
    )

    if not exercise_session or not exercise_session.get("exercises"):
        raise HTTPException(
            status_code=404,
            detail="未能根据您的要求找到足够的题目，请尝试放宽条件或检查课程ID是否正确。"
        )

    return exercise_session


@router.get(
    "/get-practice",
    response_model=schemas.PracticeResponse,
    summary="按能力获取随机练习题目"
)
async def get_practice(
    req: Request,
    skills: List[schemas.PracticeSkill] = Query(
        ...,
        alias="skill",
        description="练习维度：听/说/读/写/译。重复传参以实现多选，例如 ?skill=听&skill=读",
    ),
    limit: int = Query(10, ge=1, le=50, description="返回的题目数量"),
    db: Session = Depends(get_db),
):
    """
    根据指定的一个或多个练习维度（听/说/读/写/译）随机返回指定数量的题目列表。
    """
    base_url = str(req.base_url)

    practice = service.get_practice_exercises(
        db=db,
        skills=skills,
        limit=limit,
        base_url=base_url,
    )

    if not practice or not practice.exercises:
        raise HTTPException(
            status_code=404,
            detail="未找到符合条件的练习题目"
        )

    return practice
