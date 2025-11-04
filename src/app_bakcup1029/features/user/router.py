# app/features/user/router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app_1.database import get_db
from app_1.schemas import ResponseModel
from .schemas import RegisterRequest, SubmitAnswersRequest
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
def submit_answers(request: SubmitAnswersRequest, db: Session = Depends(get_db)):
    """
    提交答案接口

    - **sessionId**: 会话ID（通过登录接口获取）
    - **token**: 访问令牌（通过登录接口获取）
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
    # 通过sessionId查询用户
    user = UserService.get_user_by_session_id(db, request.sessionId)
    if not user:
        return {
            "code": 0,
            "message": "无效的session或用户未登录",
            "data": None
        }

    # 提交答案并更新积分
    submissions = [item.model_dump() for item in request.submissionList]
    result = UserService.submit_answers(db, user, request.sessionId, submissions)

    return {
        "code": 1,
        "message": "答案提交成功",
        "data": result
    }


@router.get("/word-learning-analytics", response_model=ResponseModel, summary="获取词汇粒度学情分析数据")
def get_word_learning_analytics(
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取用户的学情分析数据（词汇粒度）

    - **user_id**: 用户ID（必填）

    返回学情分析数据，包括：
    - 用户ID
    - 学过的总词汇数
    - 全部词汇的平均分
    - 每个词汇的学习数据（包含听说读写译五个维度的分数）
    """
    try:
        # 转换user_id为UUID格式
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return {
            "code": 0,
            "message": "无效的用户ID格式",
            "data": None
        }

    # 获取学情分析数据
    analytics_data = UserService.get_learning_analytics(db, user_uuid)

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
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取用户的学情分析数据（主题粒度）

    - **user_id**: 用户ID（必填）

    返回学情分析数据，包括：
    - 用户ID
    - 学过的总主题数
    - 全部主题的平均分
    - 每个主题的学习数据（包含听说读写译五个维度的分数）
    - 每个主题下的课程（lesson）数据（包含听说读写译五个维度的分数）
    """
    try:
        # 转换user_id为UUID格式
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return {
            "code": 0,
            "message": "无效的用户ID格式",
            "data": None
        }

    # 获取主题粒度的学情分析数据
    analytics_data = UserService.get_topic_learning_analytics(db, user_uuid)

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
