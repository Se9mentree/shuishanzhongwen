# app/features/user/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict


class RegisterRequest(BaseModel):
    """用户注册请求"""
    user_name: str
    password: str
    country: Optional[str] = None
    job: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    init_cn_level: Optional[int] = None


class SubmissionItem(BaseModel):
    """单个题目提交项"""
    exerciseId: str  # 题目ID
    userAnswer: Any  # 用户答案，可以是bool、int、str等
    points: int  # 获得的分数
    is_full_correct: bool  # 是否完全正确


class SubmitAnswersRequest(BaseModel):
    """提交答案请求"""
    sessionId: str  # 会话ID
    token: str  # 用户token
    submissionList: List[SubmissionItem]  # 提交的答案列表


class AttemptInfo(BaseModel):
    """单个attempt信息"""
    attempt_id: str
    exercise_id: str
    points: int


class SubmitAnswersData(BaseModel):
    """提交答案响应数据"""
    total_submissions: int
    saved_count: int
    total_points_earned: int
    current_total_points: int
    attempts: List[Dict[str, Any]]
    errors: Optional[List[str]] = None


class WordPerformanceData(BaseModel):
    """单个词汇的学情数据"""
    word_id: str  # 词汇ID
    characters: str  # 汉字
    pinyin: Optional[str] = None  # 拼音
    translation: Optional[str] = None  # 翻译
    hsk_level: Optional[int] = None  # HSK等级
    avg_score: float  # 词汇平均分 = 各维度正确率的平均值
    listen: Optional[float] = None  # 听力维度正确率(%) = (正确数/总数)*100，无数据则默认100
    speak: Optional[float] = None  # 口语维度正确率(%) = (正确数/总数)*100，无数据则默认100
    reading: Optional[float] = None  # 阅读维度正确率(%) = (正确数/总数)*100，无数据则默认100
    writing: Optional[float] = None  # 写作维度正确率(%) = (正确数/总数)*100，无数据则默认100
    translation_score: Optional[float] = None  # 翻译维度正确率(%) = (正确数/总数)*100，无数据则默认100


class LearningAnalyticsData(BaseModel):
    """学情分析数据"""
    user_id: str  # 用户ID
    total_words: int  # 学过的总词汇数
    avg_score: float  # 全部词汇平均分
    word_performances: List[WordPerformanceData]  # 词汇粒度的学情数据


class LessonPerformanceData(BaseModel):
    """单个课程的学情数据"""
    lesson_id: str  # 课程ID
    lesson_name: str  # 课程名称
    avg_score: float  # 课程平均分 = 该课程所有词汇的平均分的平均值
    listen: Optional[float] = None  # 听力维度正确率
    speak: Optional[float] = None  # 口语维度正确率
    reading: Optional[float] = None  # 阅读维度正确率
    writing: Optional[float] = None  # 写作维度正确率
    translation_score: Optional[float] = None  # 翻译维度正确率


class TopicPerformanceData(BaseModel):
    """单个主题的学情数据"""
    topic_id: str  # 主题ID
    topic_name: str  # 主题名称
    avg_score: float  # 主题平均分 = 该主题所有课程的平均分的平均值
    listen: Optional[float] = None  # 听力维度正确率 = 该主题所有课程该维度的平均值
    speak: Optional[float] = None  # 口语维度正确率 = 该主题所有课程该维度的平均值
    reading: Optional[float] = None  # 阅读维度正确率 = 该主题所有课程该维度的平均值
    writing: Optional[float] = None  # 写作维度正确率 = 该主题所有课程该维度的平均值
    translation_score: Optional[float] = None  # 翻译维度正确率 = 该主题所有课程该维度的平均值
    lessons: List[LessonPerformanceData]  # 课程粒度的学情数据


class TopicLearningAnalyticsData(BaseModel):
    """主题粒度的学情分析数据"""
    user_id: str  # 用户ID
    total_topics: int  # 学过的总主题数
    avg_score: float  # 全部主题平均分
    topic_performances: List[TopicPerformanceData]  # 主题粒度的学情数据
