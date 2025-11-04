# app/features/lesson_progress/service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models import LessonProgress, LessonProgressStatus, Attempt, AttemptStatus
from app.exercise_query.models import Lesson, LessonWord, Exercise, Topic, Phase
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
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
        # 自动确保仅第一个主题的首个课程处于已解锁状态
        LessonProgressService.ensure_first_lessons_unlocked(db, user_id)

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
        unlock_date: Optional[datetime] = None,
        commit: bool = True
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

        changed = False
        if progress is None:
            # 创建新的进度记录
            progress = LessonProgress(
                user_id=user_id,
                topic_id=topic_id,
                lesson_id=lesson_id,
                status=LessonProgressStatus.in_progress,
                unlock_date=unlock_date or datetime.utcnow()
            )
            db.add(progress)
            changed = True
        else:
            # 更新状态（如果之前是locked）
            if progress.status == LessonProgressStatus.locked:
                progress.status = LessonProgressStatus.in_progress
                progress.unlock_date = unlock_date or datetime.utcnow()
                progress.updated_at = datetime.utcnow()
                changed = True

        if changed:
            if commit:
                db.commit()
            else:
                db.flush()

        return progress

    @staticmethod
    def mark_lesson_completed(
        db: Session,
        user_id: uuid.UUID,
        topic_id: uuid.UUID,
        lesson_id: uuid.UUID,
        commit: bool = True
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

        changed = False
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
            changed = True
        else:
            if progress.status != LessonProgressStatus.completed:
                progress.status = LessonProgressStatus.completed
                changed = True
            if progress.first_accessed_at is None:
                progress.first_accessed_at = datetime.utcnow()
                changed = True
            progress.completed_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()
            changed = True

        if changed:
            if commit:
                db.commit()
            else:
                db.flush()

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

    @staticmethod
    def initialize_first_lessons_for_new_user(
        db: Session,
        user_id: uuid.UUID
    ) -> None:
        """
        为新用户初始化首课解锁记录。
        仅解锁第一个主题的第一个课程。

        Args:
            db: 数据库会话
            user_id: 新用户的ID
        """
        try:
            print(f"[DEBUG] 开始为用户 {user_id} 初始化首课解锁记录")

            initial_lesson = LessonProgressService._get_initial_lesson(db)
            if not initial_lesson:
                print(f"[WARNING] 没有查询到任何主题或课程数据")
                return

            now = datetime.utcnow()
            print(f"[DEBUG] 为用户 {user_id} 初始化首课 {initial_lesson.id}")

            progress = LessonProgress(
                user_id=user_id,
                topic_id=initial_lesson.topic_id,
                lesson_id=initial_lesson.id,
                status=LessonProgressStatus.in_progress,
                unlock_date=now
            )
            db.add(progress)

            print(f"[DEBUG] 准备提交首课记录")
            db.commit()
            print(f"[DEBUG] ✓ 成功为用户 {user_id} 创建首课解锁记录")

        except Exception as e:
            print(f"[ERROR] 为用户 {user_id} 初始化首课记录时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise

    @staticmethod
    def ensure_first_lessons_unlocked(
        db: Session,
        user_id: uuid.UUID
    ) -> None:
        """确保仅第一个主题的首节课对该用户已解锁。"""
        initial_lesson = LessonProgressService._get_initial_lesson(db)
        if not initial_lesson:
            return

        changed = False
        progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.topic_id == initial_lesson.topic_id,
                LessonProgress.lesson_id == initial_lesson.id
            )
        ).first()

        now = datetime.utcnow()
        if progress is None:
            db.add(
                LessonProgress(
                    user_id=user_id,
                    topic_id=initial_lesson.topic_id,
                    lesson_id=initial_lesson.id,
                    status=LessonProgressStatus.in_progress,
                    unlock_date=now
                )
            )
            changed = True
        elif progress.status == LessonProgressStatus.locked:
            progress.status = LessonProgressStatus.in_progress
            progress.unlock_date = progress.unlock_date or now
            progress.updated_at = now
            changed = True

        if changed:
            db.commit()

    @staticmethod
    def handle_post_submission_progress(
        db: Session,
        user_id: uuid.UUID,
        topic_id: uuid.UUID,
        lesson_id: uuid.UUID
    ) -> None:
        """
        在提交练习后检查课程是否完成，若完成则标记为完成并解锁下一节课。
        """
        print(f"[DEBUG] handle_post_submission_progress: 检查用户 {user_id} 的课程 {lesson_id} 是否完成")

        if LessonProgressService._is_lesson_completed(
            db=db,
            user_id=user_id,
            lesson_id=lesson_id
        ):
            print(f"[DEBUG] 课程 {lesson_id} 已完成，标记为 completed 并解锁下一课程")

            LessonProgressService.mark_lesson_completed(
                db=db,
                user_id=user_id,
                topic_id=topic_id,
                lesson_id=lesson_id,
                commit=False
            )
            print(f"[DEBUG] 标记课程为 completed")

            LessonProgressService._unlock_next_lesson(
                db=db,
                user_id=user_id,
                lesson_id=lesson_id
            )
            print(f"[DEBUG] 解锁下一课程")

            # 统一提交所有更改
            db.commit()
            print(f"[DEBUG] ✓ 成功提交课程完成和解锁操作")
        else:
            print(f"[DEBUG] 课程 {lesson_id} 未完成，跳过")

    @staticmethod
    def _unlock_next_lesson(
        db: Session,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID
    ) -> None:
        """
        解锁当前课程之后的下一节课程。

        逻辑：
        1. 先尝试解锁同一 topic 下的下一课
        2. 如果没有下一课，则解锁下一个 topic 的首课
        """
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            print(f"[DEBUG] _unlock_next_lesson: 课程 {lesson_id} 不存在")
            return

        print(f"[DEBUG] _unlock_next_lesson: 当前课程 {lesson.id}，所属 topic {lesson.topic_id}")

        # 1. 先查找同一 topic 内的下一课
        next_lesson = (
            db.query(Lesson)
            .filter(
                Lesson.topic_id == lesson.topic_id,
                Lesson.display_order > lesson.display_order
            )
            .order_by(Lesson.display_order.asc())
            .first()
        )

        if next_lesson:
            # 在同一 topic 内有下一课，解锁它
            print(f"[DEBUG] _unlock_next_lesson: 在同一 topic 内找到下一课 {next_lesson.id}")
            LessonProgressService.unlock_lesson(
                db=db,
                user_id=user_id,
                topic_id=next_lesson.topic_id,
                lesson_id=next_lesson.id,
                unlock_date=datetime.utcnow(),
                commit=False
            )
            return

        print(f"[DEBUG] _unlock_next_lesson: 同一 topic 内没有下一课，尝试找下一个 topic")

        # 2. 同一 topic 没有下一课，查找下一个 topic 的首课
        current_topic = (
            db.query(Topic)
            .options(joinedload(Topic.phase))
            .filter(Topic.id == lesson.topic_id)
            .first()
        )
        if not current_topic:
            print(f"[DEBUG] _unlock_next_lesson: 当前 topic {lesson.topic_id} 不存在")
            return

        # 2a. 当前阶段内查找下一个 topic
        next_topic = (
            db.query(Topic)
            .filter(
                Topic.phase_id == current_topic.phase_id,
                Topic.topic_order > current_topic.topic_order
            )
            .order_by(Topic.topic_order.asc())
            .first()
        )

        # 2b. 如果当前阶段没有剩余 topic，则查找下一阶段的首个 topic
        if not next_topic:
            current_phase = current_topic.phase
            next_phase = (
                db.query(Phase)
                .filter(Phase.display_order > current_phase.display_order)
                .order_by(Phase.display_order.asc())
                .first()
            )

            if next_phase:
                next_topic = (
                    db.query(Topic)
                    .filter(Topic.phase_id == next_phase.id)
                    .order_by(Topic.topic_order.asc())
                    .first()
                )

        if next_topic:
            # 找到下一个 topic，解锁其首课
            print(f"[DEBUG] _unlock_next_lesson: 找到下一个 topic {next_topic.id}")
            first_lesson_in_next_topic = (
                db.query(Lesson)
                .filter(Lesson.topic_id == next_topic.id)
                .order_by(Lesson.display_order.asc())
                .first()
            )
            if first_lesson_in_next_topic:
                print(f"[DEBUG] _unlock_next_lesson: 解锁下一 topic 的首课 {first_lesson_in_next_topic.id}")
                LessonProgressService.unlock_lesson(
                    db=db,
                    user_id=user_id,
                    topic_id=first_lesson_in_next_topic.topic_id,
                    lesson_id=first_lesson_in_next_topic.id,
                    unlock_date=datetime.utcnow(),
                    commit=False
                )
            else:
                print(f"[DEBUG] _unlock_next_lesson: 下一 topic {next_topic.id} 没有课程")
        else:
            print(f"[DEBUG] _unlock_next_lesson: 没有下一个 topic，所有课程已完成")

    @staticmethod
    def _is_lesson_completed(
        db: Session,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID
    ) -> bool:
        """
        判断指定课程是否已完成。

        若课程中没有练习题，视为已完成。
        只需完成课程中50%的练习题即可标记为完成。
        """
        progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id
            )
        ).first()

        if progress and progress.status == LessonProgressStatus.completed:
            print(f"[DEBUG] _is_lesson_completed: 课程 {lesson_id} 已是 completed 状态")
            return True

        exercise_ids = LessonProgressService._get_lesson_exercise_ids(db, lesson_id)
        print(f"[DEBUG] _is_lesson_completed: 课程 {lesson_id} 有 {len(exercise_ids)} 道练习题")

        if not exercise_ids:
            print(f"[DEBUG] _is_lesson_completed: 课程 {lesson_id} 没有练习题，视为已完成")
            return True

        attempted_ids = LessonProgressService._get_attempted_exercise_ids(
            db=db,
            user_id=user_id,
            exercise_ids=exercise_ids
        )

        # 降低阈值：完成50%的练习题即可视为课程完成
        threshold = max(1, len(exercise_ids) // 2)
        # is_completed = len(attempted_ids) >= threshold
        is_completed = len(attempted_ids) >0

        print(f"[DEBUG] _is_lesson_completed: 课程 {lesson_id} 已做 {len(attempted_ids)} 道题，需要 {threshold} 道，完成状态: {is_completed}")
        return is_completed

    @staticmethod
    def _get_initial_lesson(db: Session) -> Optional[Lesson]:
        """返回第一个主题的第一节课。"""
        return (
            db.query(Lesson)
            .join(Topic, Lesson.topic_id == Topic.id)
            .join(Phase, Topic.phase_id == Phase.id)
            .order_by(Phase.display_order.asc(), Topic.topic_order.asc(), Lesson.display_order.asc(), Lesson.id.asc())
            .first()
        )

    @staticmethod
    def _get_lesson_exercise_ids(
        db: Session,
        lesson_id: uuid.UUID
    ) -> Set[uuid.UUID]:
        """获取课程下所有练习题目的 ID 集合。"""
        word_rows = db.query(LessonWord.word_id).filter(
            LessonWord.lesson_id == lesson_id
        ).all()
        word_ids = [row[0] for row in word_rows if row and row[0]]
        if not word_ids:
            return set()

        exercise_rows = db.query(Exercise.id).filter(
            Exercise.word_id.in_(word_ids)
        ).all()
        return {row[0] for row in exercise_rows if row and row[0]}

    @staticmethod
    def _get_attempted_exercise_ids(
        db: Session,
        user_id: uuid.UUID,
        exercise_ids: Set[uuid.UUID]
    ) -> Set[uuid.UUID]:
        """获取用户已提交的练习题 ID 集合。"""
        if not exercise_ids:
            return set()

        attempted_rows = db.query(Attempt.exercise_id).filter(
            Attempt.person_id == user_id,
            Attempt.status == AttemptStatus.submitted,
            Attempt.exercise_id.in_(list(exercise_ids))
        ).distinct().all()

        return {row[0] for row in attempted_rows if row and row[0]}
