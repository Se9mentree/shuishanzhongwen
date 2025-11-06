# app/features/user/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
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


class UpdateUserProfileRequest(BaseModel):
    """更新用户信息请求"""
    user_name: Optional[str] = Field(None, description="用户昵称，空值时不更新")
    email: Optional[str] = Field(None, description="用户邮箱，空值时不更新")
    phone: Optional[str] = Field(None, description="用户电话号码，空值时不更新")
    country: Optional[str] = Field(None, description="国家/地区，空值时不更新")
    job: Optional[str] = Field(None, description="职位/工作，空值时不更新")

    @field_validator("user_name", "email", "phone", "country", "job", mode="before")
    @classmethod
    def normalize_optional_str(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return None
            return trimmed
        return value


class SubmissionItem(BaseModel):
    """单个题目提交项"""
    exerciseId: str  # 题目ID
    userAnswer: Any  # 用户答案，可以是bool、int、str等
    points: int  # 获得的分数
    is_full_correct: bool  # 是否完全正确


class SubmitAnswersRequest(BaseModel):
    """提交答案请求"""
    submissionList: List[SubmissionItem]  # 提交的答案列表
    is_practice: bool = False  # 是否为练习模式
    token: Optional[str] = None  # 可选显式 token


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


class UnlockTopicRequest(BaseModel):
    """解锁 Topic 请求"""
    topicId: str = Field(..., description="要解锁的 Topic ID")
    point: int = Field(0, ge=0, description="解锁需要扣除的积分，默认0")
    token: Optional[str] = None  # 可选显式 token


class UnlockTopicData(BaseModel):
    """解锁 Topic 响应数据"""
    phaseId: str
    topicId: str
    lessonId: str
    costPoints: int
    remainingPoints: int
    alreadyUnlocked: bool
    lessonStatus: str


class WeakTypeExercises(BaseModel):
    """弱项题型推荐项"""
    exerciseType: str
    exercises: List[Dict[str, Any]]


class WeakTypeRecommendationData(BaseModel):
    """弱项题型推荐响应体"""
    recommendations: List[WeakTypeExercises]


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
