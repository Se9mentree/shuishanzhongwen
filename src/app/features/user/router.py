# app/features/user/router.py
from fastapi import APIRouter, Depends, Query, Header, HTTPException, Request
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ResponseModel
from app.core.dependencies import get_current_user_id
from app.core.security import verify_token
from .schemas import (
    RegisterRequest,
    SubmitAnswersRequest,
    UnlockTopicRequest,
    WeakTypeRecommendationData,
)
from .service import UserService
import uuid


router = APIRouter(prefix="/user", tags=["用户"])


@router.post("/register", response_model=ResponseModel, summary="用户注册")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册接口

    - **user_name**: 用户名（必填）
    - **password**: 密码（必填）
    - **country**: 国家（选填）
    - **job**: 职业（选填）
    - **phone**: 电话（必填）
    - **email**: 邮箱（选填）
    - **init_cn_level**: 初始中文水平（选填，默认1）

    返回注册结果
    """
    # 检查用户名是否已存在
    existing = UserService.get_user_by_username(db, request.user_name)
    if existing:
        return {"code": 0, "message": "账号已存在", "data": None}

    # 创建用户
    user = UserService.create_user(
        db,
        user_name=request.user_name,
        raw_password=request.password,
        user_extra={
            "country": request.country,
            "job": request.job,
            "phone": request.phone,
            "email": request.email,
            "init_cn_level": request.init_cn_level if request.init_cn_level is not None else 1,
            "points": 0
        }
    )

    return {
        "code": 1,
        "message": "注册成功",
        "data": {
            "user_id": str(user.user_id),
            "user_name": user.user_name
        }
    }


@router.post("/submit-answers", response_model=ResponseModel, summary="提交答案")
def submit_answers(
    request: SubmitAnswersRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    提交答案接口

    需要在 Authorization 头中提供 Bearer token

    - **submissionList**: 提交的答案列表
        - **exerciseId**: 题目ID
        - **userAnswer**: 用户答案（可以是任何类型）
        - **points**: 获得的分数
        - **is_full_correct**: 是否完全正确（必填，用于判断是否记录到错题表）

    返回提交结果，包括：
    - 成功保存的题目数量
    - 本次获得的总积分
    - 用户当前的总积分
    - 所有保存的attempt记录
    """
    # 从 Authorization 头获取 token
    token_value = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token_value = parts[1]
        else:
            raise HTTPException(status_code=401, detail="无效的 Authorization 格式，应为 'Bearer <token>'")

    if not token_value:
        if request.token:
            token_value = request.token
        else:
            raise HTTPException(status_code=401, detail="未提供 token")

    # 验证 token 并获取用户ID
    payload = verify_token(token_value)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的 token")

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Token 中缺少 user_id")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的 user_id 格式")

    # 获取用户信息
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 提交答案并更新积分
    submissions = [item.model_dump() for item in request.submissionList]
    # 使用用户ID获取会话ID，或者直接使用user_id
    result = UserService.submit_answers(
        db=db,
        user=user,
        session_id=str(user_id),
        submissions=submissions,
        is_practice=request.is_practice
    )

    return {
        "code": 1,
        "message": "答案提交成功",
        "data": result
    }


@router.post("/unlock-topic", response_model=ResponseModel, summary="解锁指定主题的首个课程")
def unlock_topic(
    request: UnlockTopicRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    解锁指定 topic 的首个课程。

    - **topicId**: 主题 ID
    - **point**: 扣除的积分（默认 0）
    """
    token_value = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token_value = parts[1]
        else:
            raise HTTPException(status_code=401, detail="无效的 Authorization 格式，应为 'Bearer <token>'")

    if not token_value:
        if request.token:
            token_value = request.token
        else:
            raise HTTPException(status_code=401, detail="未提供 token")

    payload = verify_token(token_value)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的 token")

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Token 中缺少 user_id")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的 user_id 格式")

    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    try:
        topic_id = uuid.UUID(request.topicId)
    except ValueError:
        raise HTTPException(status_code=400, detail="topicId 格式不正确")

    try:
        result = UserService.unlock_topic_first_lesson(
            db=db,
            user=user,
            topic_id=topic_id,
            cost_points=request.point
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "code": 1,
        "message": "主题解锁成功",
        "data": result
    }


@router.get(
    "/weak-type-recommendations",
    response_model=ResponseModel,
    summary="弱项题型强化推荐"
)
def weak_type_recommendations(
    req: Request,
    top_n: int = Query(2, ge=1, le=5, description="推荐的弱项题型数量"),
    per_type: int = Query(5, ge=1, le=10, description="每个题型推荐的题目数量"),
    token: Optional[str] = Query(None, description="显式 token，用于 Swagger 调试"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """基于错题数据推荐错题率最高的题型进行强化练习。"""
    token_value = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token_value = parts[1]
        else:
            raise HTTPException(status_code=401, detail="无效的 Authorization 格式，应为 'Bearer <token>'")

    if not token_value:
        token_value = token
        if not token_value:
            raise HTTPException(status_code=401, detail="未提供 token")

    payload = verify_token(token_value)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的 token")

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Token 中缺少 user_id")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的 user_id 格式")

    recommendations = UserService.get_weak_type_recommendations(
        db=db,
        user_id=user_id,
        top_n=top_n,
        per_type_limit=per_type,
        base_url=str(req.base_url)
    )

    data = WeakTypeRecommendationData(recommendations=recommendations).model_dump()

    return {
        "code": 1,
        "message": "获取成功",
        "data": data
    }


@router.get("/word-learning-analytics", response_model=ResponseModel, summary="获取词汇粒度学情分析数据")
def get_word_learning_analytics(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取用户的学情分析数据（词汇粒度）

    通过请求头中的 Authorization: Bearer <token> 自动获取用户ID

    返回学情分析数据，包括：
    - 用户ID
    - 学过的总词汇数
    - 全部词汇的平均分
    - 每个词汇的学习数据（包含听说读写译五个维度的分数）
    """
    # 获取学情分析数据
    analytics_data = UserService.get_learning_analytics(db, user_id)

    if analytics_data is None:
        return {
            "code": 0,
            "message": "获取学情分析数据失败",
            "data": None
        }

    return {
        "code": 1,
        "message": "获取成功",
        "data": analytics_data
    }


@router.get("/topic-learning-analytics", response_model=ResponseModel, summary="获取主题粒度学情分析数据")
def get_topic_learning_analytics(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取用户的学情分析数据（主题粒度）

    通过请求头中的 Authorization: Bearer <token> 自动获取用户ID

    返回学情分析数据，包括：
    - 用户ID
    - 学过的总主题数
    - 全部主题的平均分
    - 每个主题的学习数据（包含听说读写译五个维度的分数）
    - 每个主题下的课程（lesson）数据（包含听说读写译五个维度的分数）
    """
    # 获取主题粒度的学情分析数据
    analytics_data = UserService.get_topic_learning_analytics(db, user_id)

    if analytics_data is None:
        return {
            "code": 0,
            "message": "获取学情分析数据失败",
            "data": None
        }

    return {
        "code": 1,
        "message": "获取成功",
        "data": analytics_data
    }


@router.get(
    "/wrong-exercise-recommendations",
    response_model=ResponseModel,
    summary="错题推荐列表"
)
def get_wrong_exercise_recommendations(
    req: Request,
    limit: int = Query(10, ge=1, le=50),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取用户错题推荐列表

    返回随机的错题及其关联的相同词汇练习，默认返回10条错题。
    """
    recommendations = UserService.get_wrong_exercise_recommendations(
        db=db,
        user_id=user_id,
        limit=limit,
        base_url=str(req.base_url)
    )

    return {
        "code": 1,
        "message": "获取成功",
        "data": {
            "count": len(recommendations),
            "items": recommendations
        }
    }
