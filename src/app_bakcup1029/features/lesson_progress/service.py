# app/features/lesson_progress/service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app_1.models import LessonProgress, LessonProgressStatus
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


class LessonProgressService:
    """课程进度服务"""

    @staticmethod
    def get_lesson_progress(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户的课程解锁进度

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            包含课程进度信息的字典，如果用户不存在返回None
        """
        # 查询用户所有课程进度
        lesson_progresses = db.query(LessonProgress).filter(
            LessonProgress.user_id == user_id
        ).order_by(LessonProgress.updated_at.desc()).all()

        if not lesson_progresses:
            # 如果用户没有任何课程进度记录，返回空的进度信息
            return {
                "last_accessed_topic_id": None,
                "last_accessed_lesson_id": None,
                "total_unlocked_count": 0,
                "total_completed_count": 0,
                "unlocked_lessons": []
            }

        # 统计解锁和完成的课程数量
        unlocked_count = len([p for p in lesson_progresses if p.status in [
            LessonProgressStatus.unlocked,
            LessonProgressStatus.in_progress,
            LessonProgressStatus.completed
        ]])
        completed_count = len([p for p in lesson_progresses if p.status == LessonProgressStatus.completed])

        # 获取最后访问的课程
        last_progress = lesson_progresses[0] if lesson_progresses else None
        last_accessed_topic_id = str(last_progress.topic_id) if last_progress else None
        last_accessed_lesson_id = str(last_progress.lesson_id) if last_progress else None

        # 构建解锁课程列表
        unlocked_lessons = []
        for progress in lesson_progresses:
            if progress.status != LessonProgressStatus.locked:
                lesson_info = {
                    "lesson_id": str(progress.lesson_id),
                    "topic_id": str(progress.topic_id),
                    "status": progress.status.value,
                    "unlock_date": progress.unlock_date.isoformat() if progress.unlock_date else None,
                    "completed_at": progress.completed_at.isoformat() if progress.completed_at else None
                }
                unlocked_lessons.append(lesson_info)

        return {
            "last_accessed_topic_id": last_accessed_topic_id,
            "last_accessed_lesson_id": last_accessed_lesson_id,
            "total_unlocked_count": unlocked_count,
            "total_completed_count": completed_count,
            "unlocked_lessons": unlocked_lessons
        }

    @staticmethod
    def unlock_lesson(
        db: Session,
        user_id: uuid.UUID,
        topic_id: uuid.UUID,
        lesson_id: uuid.UUID,
        unlock_date: Optional[datetime] = None
    ) -> LessonProgress:
        """
        解锁课程

        Args:
            db: 数据库会话
            user_id: 用户ID
            topic_id: 主题ID
            lesson_id: 课程ID
            unlock_date: 解锁时间

        Returns:
            LessonProgress对象
        """
        # 查询是否存在
        progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.topic_id == topic_id
            )
        ).first()

        if progress is None:
            # 创建新的进度记录
            progress = LessonProgress(
                user_id=user_id,
                topic_id=topic_id,
                lesson_id=lesson_id,
                status=LessonProgressStatus.unlocked,
                unlock_date=unlock_date or datetime.utcnow()
            )
            db.add(progress)
        else:
            # 更新状态（如果之前是locked）
            if progress.status == LessonProgressStatus.locked:
                progress.status = LessonProgressStatus.unlocked
                progress.unlock_date = unlock_date or datetime.utcnow()
                progress.updated_at = datetime.utcnow()

        db.commit()
        return progress

    @staticmethod
    def mark_lesson_in_progress(
        db: Session,
        user_id: uuid.UUID,
        topic_id: uuid.UUID,
        lesson_id: uuid.UUID
    ) -> LessonProgress:
        """
        标记课程为进行中

        Args:
            db: 数据库会话
            user_id: 用户ID
            topic_id: 主题ID
            lesson_id: 课程ID

        Returns:
            LessonProgress对象
        """
        # 查询或创建进度记录
        progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.topic_id == topic_id
            )
        ).first()

        if progress is None:
            progress = LessonProgress(
                user_id=user_id,
                topic_id=topic_id,
                lesson_id=lesson_id,
                status=LessonProgressStatus.in_progress,
                unlock_date=datetime.utcnow(),
                first_accessed_at=datetime.utcnow()
            )
            db.add(progress)
        else:
            progress.status = LessonProgressStatus.in_progress
            if progress.first_accessed_at is None:
                progress.first_accessed_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()

        db.commit()
        return progress

    @staticmethod
    def mark_lesson_completed(
        db: Session,
        user_id: uuid.UUID,
        topic_id: uuid.UUID,
        lesson_id: uuid.UUID
    ) -> LessonProgress:
        """
        标记课程为已完成

        Args:
            db: 数据库会话
            user_id: 用户ID
            topic_id: 主题ID
            lesson_id: 课程ID

        Returns:
            LessonProgress对象
        """
        # 查询或创建进度记录
        progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.topic_id == topic_id
            )
        ).first()

        if progress is None:
            progress = LessonProgress(
                user_id=user_id,
                topic_id=topic_id,
                lesson_id=lesson_id,
                status=LessonProgressStatus.completed,
                unlock_date=datetime.utcnow(),
                first_accessed_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(progress)
        else:
            progress.status = LessonProgressStatus.completed
            if progress.first_accessed_at is None:
                progress.first_accessed_at = datetime.utcnow()
            progress.completed_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()

        db.commit()
        return progress

    @staticmethod
    def get_lesson_status(
        db: Session,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID
    ) -> Optional[str]:
        """
        获取特定课程的状态

        Args:
            db: 数据库会话
            user_id: 用户ID
            lesson_id: 课程ID

        Returns:
            课程状态字符串，如果不存在返回None
        """
        progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id
            )
        ).first()

        return progress.status.value if progress else None
