# app/features/auth/service.py
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core import security
from app import models
from typing import Optional


class AuthService:
    """认证服务"""

    @staticmethod
    def authenticate_user(db: Session, phone: str, password: str) -> Optional[models.User]:
        """
        验证用户凭证

        Args:
            db: 数据库会话
            phone: 手机号码
            password: 密码

        Returns:
            验证成功返回用户对象，失败返回 None
        """
        user = db.query(models.User).filter(models.User.phone == phone).first()
        if not user:
            return None
        if not security.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_user_session(db: Session, user_id: str, token: str) -> models.UserSession:
        """
        创建用户会话

        Args:
            db: 数据库会话
            user_id: 用户ID
            token: 访问令牌

        Returns:
            创建的会话对象
        """
        session = models.UserSession(user_id=user_id, token=token)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def logout_user(db: Session, token: str) -> bool:
        """
        登出用户

        Args:
            db: 数据库会话
            token: 访问令牌

        Returns:
            成功返回 True，失败返回 False
        """
        session = db.query(models.UserSession).filter(
            models.UserSession.token == token,
            models.UserSession.logout_time.is_(None)
        ).first()

        if not session:
            return False

        session.logout_time = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def get_user_by_token(db: Session, token: str) -> Optional[models.UserSession]:
        """
        通过 token 获取用户会话

        Args:
            db: 数据库会话
            token: 访问令牌

        Returns:
            会话对象或 None
        """
        return db.query(models.UserSession).filter(
            models.UserSession.token == token,
            models.UserSession.logout_time.is_(None)
        ).first()

    @staticmethod
    def generate_access_token(user_id: str, username: str) -> str:
        """
        生成访问令牌

        Args:
            user_id: 用户ID
            username: 用户名

        Returns:
            JWT token
        """
        return security.create_access_token({
            "user_id": str(user_id),
            "username": username
        })

    @staticmethod
    def get_user_profile(db: Session, user_id: uuid.UUID) -> Optional[dict]:
        """
        聚合用户个人档案数据

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            包含用户学习概览的数据字典；如果用户不存在返回 None
        """
        user = db.query(models.User).filter(models.User.user_id == user_id).first()
        if user is None:
            return None

        # 统计学习单词数量
        words_learned = db.query(
            func.count(func.distinct(models.UserWordPerformance.word_id))
        ).filter(
            models.UserWordPerformance.user_id == user_id
        ).scalar() or 0

        # 统计掌握主题数量（至少完成该主题下的一节课）
        mastered_topics = db.query(
            func.count(func.distinct(models.LessonProgress.topic_id))
        ).filter(
            models.LessonProgress.user_id == user_id,
            models.LessonProgress.status == models.LessonProgressStatus.completed
        ).scalar() or 0

        # 统计学习天数与连续学习日期
        study_dates = [
            row[0] for row in db.query(
                func.date(models.Attempt.started_at)
            ).filter(
                models.Attempt.person_id == user_id,
                models.Attempt.status == models.AttemptStatus.submitted,
                models.Attempt.started_at.isnot(None)
            ).distinct().all()
            if row[0] is not None
        ]

        unique_study_dates = set(study_dates)
        days_studied = len(unique_study_dates)

        consecutive_study_dates = []
        if unique_study_dates:
            latest_date = max(unique_study_dates)
            streak_dates = []
            cursor = latest_date
            while cursor in unique_study_dates:
                streak_dates.append(cursor)
                cursor -= timedelta(days=1)
            streak_dates.sort()
            consecutive_study_dates = [d.isoformat() for d in streak_dates]

        # 课程学习进度
        from app.features.lesson_progress.service import LessonProgressService
        learning_progress = LessonProgressService.get_lesson_progress(db, user_id)

        return {
            "user_id": str(user.user_id),
            "user_name": user.user_name,
            "avatar": user.avatar,
            "points": user.points,
            "registered_at": user.reg_time.isoformat() if user.reg_time else None,
            "days_studied": days_studied,
            "words_learned": int(words_learned),
            "mastered_topics": int(mastered_topics),
            "consecutive_study_dates": consecutive_study_dates,
            "learning_progress": learning_progress
        }
