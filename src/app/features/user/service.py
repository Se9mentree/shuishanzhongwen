# app/features/user/service.py
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app import models
from app.exercise_query.models import (
    Exercise,
    LessonWord,
    Lesson,
    Word,
    Topic,
    ExerciseType,
    ExerciseMediaAsset,
)
from app.exercise_query.formatter import format_exercises_for_api
from app.features.lesson_progress.service import LessonProgressService
from app.core import security
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
import uuid
import json


class UserService:
    """用户服务"""

    @staticmethod
    def get_user_by_username(db: Session, user_name: str) -> Optional[models.User]:
        """
        根据用户名查询用户

        Args:
            db: 数据库会话
            user_name: 用户名

        Returns:
            用户对象或 None
        """
        return db.query(models.User).filter(models.User.user_name == user_name).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
        """
        根据用户ID查询用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户对象或 None
        """
        return db.query(models.User).filter(models.User.user_id == user_id).first()

    @staticmethod
    def get_user_by_session_id(db: Session, session_id: str) -> Optional[models.User]:
        """
        通过session_id查询用户

        Args:
            db: 数据库会话
            session_id: 会话ID

        Returns:
            用户对象或 None
        """
        if not session_id:
            return None

        try:
            session_uuid = uuid.UUID(session_id)
        except (ValueError, TypeError, AttributeError):
            return None

        session = db.query(models.UserSession).filter(
            models.UserSession.session_id == session_uuid,
            models.UserSession.logout_time.is_(None)
        ).first()

        if session:
            return db.query(models.User).filter(
                models.User.user_id == session.user_id
            ).first()
        return None

    @staticmethod
    def create_user(
        db: Session,
        user_name: str,
        raw_password: str,
        user_extra: Optional[Dict[str, Any]] = None
    ) -> models.User:
        """
        创建新用户

        Args:
            db: 数据库会话
            user_name: 用户名
            raw_password: 原始密码
            user_extra: 额外用户信息（country, job, phone, email, init_cn_level等）

        Returns:
            创建的用户对象
        """
        hashed = security.hash_password(raw_password)
        user_extra = user_extra or {}

        user = models.User(
            user_name=user_name,
            password_hash=hashed,
            country=user_extra.get("country"),
            job=user_extra.get("job"),
            phone=user_extra.get("phone"),
            email=user_extra.get("email"),
            init_cn_level=user_extra.get("init_cn_level", 1),
            points=user_extra.get("points", 0)
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # ✅ [新增] 在用户创建后，自动为其解锁每个主题的第一个课程
        LessonProgressService.initialize_first_lessons_for_new_user(db, user.user_id)

        return user

    @staticmethod
    def create_attempt(db: Session, attempt_data: Dict[str, Any]) -> models.Attempt:
        """
        创建attempt记录

        Args:
            db: 数据库会话
            attempt_data: attempt数据字典

        Returns:
            创建的attempt对象

        注意：此方法不调用db.commit()，由调用者统一管理事务提交
        """
        attempt = models.Attempt(**attempt_data)
        db.add(attempt)
        db.flush()  # 刷新以获取自动生成的ID
        return attempt

    @staticmethod
    def get_exercise_context(db: Session, exercise_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        通过exercise_id获取word_id, topic_id, lesson_id以及exercise_type

        Args:
            db: 数据库会话
            exercise_id: 题目ID

        Returns:
            包含word_id, lesson_id, topic_id, exercise_type的字典,如果查询失败返回None
        """
        try:
            # 查询 exercise 获取 word_id 和 exercise_type
            exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
            if not exercise or not exercise.word_id:
                return None

            # 通过 word_id 查找 lesson 和 topic
            lesson_word = db.query(LessonWord).filter(
                LessonWord.word_id == exercise.word_id
            ).first()

            if not lesson_word:
                return None

            lesson = db.query(Lesson).filter(
                Lesson.id == lesson_word.lesson_id
            ).first()

            if not lesson:
                return None

            # 获取题型名称
            exercise_type_name = exercise.type.name if exercise.type else None

            return {
                "word_id": exercise.word_id,
                "lesson_id": lesson.id,
                "topic_id": lesson.topic_id,
                "exercise_type": exercise_type_name
            }
        except Exception as e:
            print(f"Error getting exercise context: {e}")
            return None

    @staticmethod
    def update_user_word_performance(
        db: Session,
        user_id: uuid.UUID,
        word_id: uuid.UUID,
        topic_id: uuid.UUID,
        lesson_id: uuid.UUID,
        exercise_type: str,
        score: float
    ):
        """
        更新或创建用户单词表现记录

        Args:
            db: 数据库会话
            user_id: 用户ID
            word_id: 单词ID
            topic_id: 主题ID
            lesson_id: 课程ID (对应chapter_id字段)
            exercise_type: 题型名称
            score: 本次得分

        注意：此方法不调用db.commit()，由调用者统一管理事务提交
        """
        # 查找现有记录
        performance = db.query(models.UserWordPerformance).filter(
            models.UserWordPerformance.user_id == user_id,
            models.UserWordPerformance.word_id == word_id
        ).first()

        # 题型映射到字段
        type_field_map = {
            "LISTEN_IMAGE_TRUE_FALSE": "listen",
            "LISTEN_IMAGE_MC": "listen",
            "LISTEN_SENTENCE_TF": "listen",
            "LISTEN_SENTENCE_QA": "listen",
            "LISTEN_DIALOGUE_QA": "listen",
            "LISTEN_PARAGRAPH_QA": "listen",
            "LISTEN_IMAGE_MATCH": "listen",
            "SPEAK_FOLLOW": "speak",
            "READ_IMAGE_TRUE_FALSE": "reading",
            "READ_SENTENCE_TF": "reading",
            "READ_SENTENCE_COMPREHENSION_CHOICE": "reading",
            "READ_WORD_GAP_FILL": "reading",
            "READ_IMAGE_MATCH": "reading",
            "READ_DIALOGUE_MATCH": "reading",
            "READ_WORD_ORDER": "reading",
            "READ_PARAGRAPH_COMPREHENSION": "reading",
            "READ_SENTENCE_ORDER": "reading",
            "STROKE_ORDER_WRITING": "writing",
            "TRANSLATE_WORD_ORDER": "translation",
        }

        field_name = type_field_map.get(exercise_type)
        if not field_name:
            print(f"Unknown exercise type: {exercise_type}")
            return

        if performance:
            # 更新现有记录
            setattr(performance, field_name, Decimal(str(score)))

            # 重新计算平均分
            scores = []
            for field in ["listen", "speak", "reading", "writing", "translation"]:
                value = getattr(performance, field)
                if value is not None:
                    scores.append(float(value))

            if scores:
                performance.avg = Decimal(str(sum(scores) / len(scores)))

            performance.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            new_performance = models.UserWordPerformance(
                user_id=user_id,
                word_id=word_id,
                topic_id=topic_id,
                chapter_id=lesson_id,  # 使用 lesson_id 作为 chapter_id
                **{field_name: Decimal(str(score))},
                avg=Decimal(str(score))
            )
            db.add(new_performance)

    @staticmethod
    def record_wrong_exercise(
        db: Session,
        user_id: uuid.UUID,
        exercise_id: uuid.UUID,
        word_id: uuid.UUID,
        topic_id: uuid.UUID,
        lesson_id: uuid.UUID,
        exercise_type: str
    ):
        """
        记录或更新用户错题

        Args:
            db: 数据库会话
            user_id: 用户ID
            exercise_id: 题目ID
            word_id: 单词ID
            topic_id: 主题ID
            lesson_id: 课程ID (对应chapter_id字段)
            exercise_type: 题型名称

        注意：此方法不调用db.commit()，由调用者统一管理事务提交
        """
        # 查找是否已有该错题记录（包括exercise_id）
        wrong_exercise = db.query(models.UserWrongExercise).filter(
            models.UserWrongExercise.user_id == user_id,
            models.UserWrongExercise.exercise_id == exercise_id
        ).first()

        if wrong_exercise:
            # 更新现有记录：错题次数+1，更新最后做错时间
            wrong_exercise.wrong_count += 1
            wrong_exercise.last_wrong_at = datetime.utcnow()
            wrong_exercise.updated_at = datetime.utcnow()
        else:
            # 创建新的错题记录
            new_wrong_exercise = models.UserWrongExercise(
                user_id=user_id,
                exercise_id=exercise_id,
                word_id=word_id,
                topic_id=topic_id,
                chapter_id=lesson_id,
                exercise_type=exercise_type,
                wrong_count=1
            )
            db.add(new_wrong_exercise)

    @staticmethod
    def submit_answers(
        db: Session,
        user: models.User,
        session_id: str,
        submissions: List[Dict[str, Any]],
        is_practice: bool = False
    ) -> Dict[str, Any]:
        """
        提交答案并更新用户积分

        Args:
            db: 数据库会话
            user: 用户对象
            session_id: 会话ID
            submissions: 提交列表

        Returns:
            包含提交结果的字典
        """
        saved_attempts = []
        errors = []
        total_points_earned = 0

        try:
            for submission in submissions:
                try:
                    exercise_id = uuid.UUID(submission["exerciseId"])
                    is_full_correct = submission.get("is_full_correct", False)

                    # 先获取exercise相关信息，确保数据有效
                    exercise_context = UserService.get_exercise_context(db, exercise_id)
                    if not exercise_context:
                        error_msg = f"Cannot find exercise context for exercise {submission['exerciseId']}"
                        print(error_msg)
                        errors.append(error_msg)
                        continue  # 跳过此提交，继续处理下一个

                    # 构建attempt数据 - attempt_meta 必须序列化为 JSON 字符串
                    attempt_meta_dict = {
                        "user_answer": submission["userAnswer"],
                        "session_id": session_id
                    }
                    attempt_data = {
                        "person_id": user.user_id,
                        "exercise_id": exercise_id,
                        "submitted_at": datetime.utcnow(),
                        "status": "submitted",
                        "total_score": submission["points"],
                        "is_full_correct": is_full_correct,
                        "attempt_meta": json.dumps(attempt_meta_dict)
                    }

                    # 保存到数据库
                    attempt = UserService.create_attempt(db, attempt_data)

                    # 累加用户积分
                    user.points = (user.points or 0) + submission["points"]
                    total_points_earned += submission["points"]

                    # 更新user_word_performance
                    UserService.update_user_word_performance(
                        db=db,
                        user_id=user.user_id,
                        word_id=exercise_context["word_id"],
                        topic_id=exercise_context["topic_id"],
                        lesson_id=exercise_context["lesson_id"],
                        exercise_type=exercise_context["exercise_type"],
                        score=float(submission["points"])
                    )

                    # 只有在is_full_correct为False时才加入错题集
                    if not is_full_correct:
                        UserService.record_wrong_exercise(
                            db=db,
                            user_id=user.user_id,
                            exercise_id=exercise_id,
                            word_id=exercise_context["word_id"],
                            topic_id=exercise_context["topic_id"],
                            lesson_id=exercise_context["lesson_id"],
                            exercise_type=exercise_context["exercise_type"]
                        )

                    if not is_practice:
                        LessonProgressService.handle_post_submission_progress(
                            db=db,
                            user_id=user.user_id,
                            topic_id=exercise_context["topic_id"],
                            lesson_id=exercise_context["lesson_id"]
                        )
                        print(f"[DEBUG] submit_answers: 处理课程进度完毕")
                    else:
                        print(f"[DEBUG] submit_answers: practice 模式，跳过课程进度处理")

                    saved_attempts.append({
                        "attempt_id": str(attempt.id),
                        "exercise_id": submission["exerciseId"],
                        "points": submission["points"]
                    })

                except ValueError as e:
                    # UUID转换或其他值错误
                    error_msg = f"Invalid data for exercise {submission.get('exerciseId', 'unknown')}: {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
                except Exception as e:
                    # 记录单个题目的错误
                    error_msg = f"Error saving attempt for exercise {submission.get('exerciseId', 'unknown')}: {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
                    # 如果发生错误，尝试回滚
                    try:
                        db.rollback()
                    except:
                        pass

            # 统一提交所有更改
            if len(saved_attempts) > 0:
                try:
                    db.commit()
                    db.refresh(user)
                except Exception as e:
                    db.rollback()
                    error_msg = f"Error committing all changes: {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
                    saved_attempts = []  # 如果提交失败，清空已保存的记录

        except Exception as e:
            try:
                db.rollback()
            except:
                pass
            error_msg = f"Unexpected error during submission processing: {str(e)}"
            print(error_msg)
            errors.append(error_msg)

        return {
            "total_submissions": len(submissions),
            "saved_count": len(saved_attempts),
            "total_points_earned": total_points_earned if len(saved_attempts) > 0 else 0,
            "current_total_points": user.points,
            "attempts": saved_attempts,
            "errors": errors if errors else None
        }

    @staticmethod
    def unlock_topic_first_lesson(
        db: Session,
        user: models.User,
        topic_id: uuid.UUID,
        cost_points: int = 0
    ) -> Dict[str, Any]:
        """
        解锁指定 Topic 的首节课。
        """
        if not isinstance(topic_id, uuid.UUID):
            raise ValueError("topicId 参数无效")

        topic = (
            db.query(Topic)
            .options(joinedload(Topic.phase))
            .filter(Topic.id == topic_id)
            .first()
        )
        if not topic:
            raise ValueError("未找到指定的 Topic")

        lesson = (
            db.query(Lesson)
            .filter(Lesson.topic_id == topic.id)
            .order_by(Lesson.display_order.asc(), Lesson.id.asc())
            .first()
        )
        if not lesson:
            raise ValueError("该 Topic 下没有任何课程可供解锁")

        progress = db.query(models.LessonProgress).filter(
            models.LessonProgress.user_id == user.user_id,
            models.LessonProgress.topic_id == topic.id,
            models.LessonProgress.lesson_id == lesson.id
        ).first()

        already_unlocked = (
            progress is not None
            and progress.status != models.LessonProgressStatus.locked
        )

        current_points = user.points or 0
        if cost_points > 0 and current_points < cost_points:
            raise ValueError("积分不足，无法解锁该主题")

        if cost_points > 0:
            user.points = current_points - cost_points

        unlock_progress = LessonProgressService.unlock_lesson(
            db=db,
            user_id=user.user_id,
            topic_id=topic.id,
            lesson_id=lesson.id,
            unlock_date=datetime.utcnow(),
            commit=False
        )

        db.commit()
        db.refresh(user)

        return {
            "phaseId": str(topic.phase.id) if topic.phase else None,
            "topicId": str(topic.id),
            "lessonId": str(lesson.id),
            "costPoints": cost_points,
            "remainingPoints": user.points or 0,
            "alreadyUnlocked": already_unlocked,
            "lessonStatus": unlock_progress.status.value if unlock_progress else "unknown"
        }

    @staticmethod
    def get_weak_type_recommendations(
        db: Session,
        user_id: uuid.UUID,
        top_n: int = 2,
        per_type_limit: int = 5,
        base_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """基于错题记录推荐弱项题型练习。"""
        if top_n <= 0 or per_type_limit <= 0:
            return []

        # 排除的题型（暂时）
        excluded_exercise_types = ["READ_DIALOGUE_MATCH"]

        type_stats = (
            db.query(
                models.UserWrongExercise.exercise_type,
                func.sum(models.UserWrongExercise.wrong_count).label("total_wrong")
            )
            .filter(
                models.UserWrongExercise.user_id == user_id,
                ~models.UserWrongExercise.exercise_type.in_(excluded_exercise_types)
            )
            .group_by(models.UserWrongExercise.exercise_type)
            .order_by(func.sum(models.UserWrongExercise.wrong_count).desc())
            .limit(top_n)
            .all()
        )

        if not type_stats:
            return []

        recommendations: List[Dict[str, Any]] = []

        for exercise_type, _ in type_stats:
            if not exercise_type:
                continue

            wrong_items = (
                db.query(models.UserWrongExercise)
                .filter(
                    models.UserWrongExercise.user_id == user_id,
                    models.UserWrongExercise.exercise_type == exercise_type,
                )
                .order_by(models.UserWrongExercise.wrong_count.desc(), models.UserWrongExercise.updated_at.desc())
                .limit(per_type_limit)
                .all()
            )

            if not wrong_items:
                continue

            exercise_ids = [item.exercise_id for item in wrong_items if item.exercise_id]
            if not exercise_ids:
                continue

            exercises = (
                db.query(Exercise)
                .options(
                    joinedload(Exercise.type),
                    joinedload(Exercise.media_links).joinedload(ExerciseMediaAsset.media_asset),
                )
                .filter(Exercise.id.in_(exercise_ids))
                .all()
            )
            if not exercises:
                continue

            formatted = format_exercises_for_api(exercises, base_url=base_url)
            if not formatted:
                continue

            formatted_map = {uuid.UUID(item.exerciseId): item for item in formatted}
            ordered_payloads = []
            for wrong_item in wrong_items:
                payload = formatted_map.get(wrong_item.exercise_id)
                if payload:
                    ordered_payloads.append(payload.model_dump())

            if not ordered_payloads:
                continue

            recommendations.append(
                {
                    "exerciseType": exercise_type,
                    "exercises": ordered_payloads,
                }
            )

        return recommendations

    @staticmethod
    def get_wrong_exercise_recommendations(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 10,
        base_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户错题推荐，仅返回题目和答案信息。
        """
        # 排除的题型（暂时）
        excluded_exercise_types = ["READ_DIALOGUE_MATCH"]

        wrong_records = (
            db.query(models.UserWrongExercise)
            .filter(
                models.UserWrongExercise.user_id == user_id,
                ~models.UserWrongExercise.exercise_type.in_(excluded_exercise_types)
            )
            .order_by(models.UserWrongExercise.wrong_count.desc(), models.UserWrongExercise.updated_at.desc())
            .limit(limit)
            .all()
        )

        if not wrong_records:
            return []

        exercise_ids = [wrong.exercise_id for wrong in wrong_records]
        if not exercise_ids:
            return []

        exercises = (
            db.query(Exercise)
            .options(
                joinedload(Exercise.type),
                joinedload(Exercise.media_links).joinedload(ExerciseMediaAsset.media_asset)
            )
            .filter(Exercise.id.in_(exercise_ids))
            .all()
        )
        exercise_map = {ex.id: ex for ex in exercises}

        formatted = format_exercises_for_api(list(exercise_map.values()), base_url=base_url)
        formatted_map = {uuid.UUID(item.exerciseId): item for item in formatted}

        recommendations: List[Dict[str, Any]] = []
        for wrong in wrong_records:
            payload = formatted_map.get(wrong.exercise_id)
            if not payload:
                continue
            recommendations.append({
                "exercise": payload.model_dump(),
                "correctAnswer": getattr(payload, "correctAnswer", None)
            })

        return recommendations

    @staticmethod
    def get_learning_analytics(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户的学情分析数据（词汇粒度）

        各维度分数 = 该维度的正确率 * 100
        如果在某个维度没有做题记录则默认为 100
        词汇粒度的平均分 = 各维度平均分的平均值

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            包含学情分析数据的字典，如果查询失败返回None
        """
        try:
            # 题型映射到维度的映射表
            type_field_map = {
                "LISTEN_IMAGE_TRUE_FALSE": "listen",
                "LISTEN_IMAGE_MC": "listen",
                "LISTEN_SENTENCE_TF": "listen",
                "LISTEN_SENTENCE_QA": "listen",
                "LISTEN_DIALOGUE_QA": "listen",
                "LISTEN_PARAGRAPH_QA": "listen",
                "LISTEN_IMAGE_MATCH": "listen",
                "SPEAK_FOLLOW": "speak",
                "READ_IMAGE_TRUE_FALSE": "reading",
                "READ_SENTENCE_TF": "reading",
                "READ_SENTENCE_COMPREHENSION_CHOICE": "reading",
                "READ_WORD_GAP_FILL": "reading",
                "READ_IMAGE_MATCH": "reading",
                "READ_DIALOGUE_MATCH": "reading",
                "READ_WORD_ORDER": "reading",
                "READ_PARAGRAPH_COMPREHENSION": "reading",
                "READ_SENTENCE_ORDER": "reading",
                "STROKE_ORDER_WRITING": "writing",
                "TRANSLATE_WORD_ORDER": "translation",
            }

            # 查询用户所有的词汇学习表现
            word_performances = db.query(models.UserWordPerformance).filter(
                models.UserWordPerformance.user_id == user_id
            ).all()

            if not word_performances:
                return {
                    "user_id": str(user_id),
                    "total_words": 0,
                    "avg_score": 0.0,
                    "word_performances": []
                }

            # 查询用户所有的尝试记录用于计算正确率
            attempts = db.query(models.Attempt).filter(
                models.Attempt.person_id == user_id,
                models.Attempt.status == "submitted"
            ).all()

            # 构建词汇粒度的学情数据
            word_performance_list = []
            total_avg_scores = []

            for performance in word_performances:
                # 查询词汇的基本信息
                word = db.query(Word).filter(Word.id == performance.word_id).first()

                if not word:
                    continue

                # 查询这个单词相关的所有练习
                word_exercises = db.query(Exercise).filter(
                    Exercise.word_id == performance.word_id
                ).all()

                word_exercise_ids = {str(ex.id) for ex in word_exercises}

                # 计算各维度的正确率
                dimension_stats = {
                    "listen": {"correct": 0, "total": 0},
                    "speak": {"correct": 0, "total": 0},
                    "reading": {"correct": 0, "total": 0},
                    "writing": {"correct": 0, "total": 0},
                    "translation": {"correct": 0, "total": 0},
                }

                # 遍历这个单词的所有尝试
                for attempt in attempts:
                    exercise_id_str = str(attempt.exercise_id)
                    if exercise_id_str not in word_exercise_ids:
                        continue

                    # 获取该练习的题型
                    exercise = next((ex for ex in word_exercises if str(ex.id) == exercise_id_str), None)
                    if not exercise or not exercise.type:
                        continue

                    exercise_type = exercise.type.name
                    dimension = type_field_map.get(exercise_type)

                    if dimension:
                        dimension_stats[dimension]["total"] += 1
                        if attempt.is_full_correct:
                            dimension_stats[dimension]["correct"] += 1

                # 计算各维度的正确率 (正确率 * 100，如果无数据则默认 100)
                dimension_scores = {}
                valid_scores = []

                for dimension in ["listen", "speak", "reading", "writing", "translation"]:
                    total = dimension_stats[dimension]["total"]
                    if total == 0:
                        # 如果在某个维度没有做题记录则默认为 100
                        accuracy = 100.0
                    else:
                        correct = dimension_stats[dimension]["correct"]
                        accuracy = round((correct / total) * 100, 2)

                    dimension_scores[dimension] = accuracy
                    valid_scores.append(accuracy)

                # 词汇粒度的平均分 = 各维度平均分的平均值
                avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 100.0
                total_avg_scores.append(avg_score)

                word_data = {
                    "word_id": str(performance.word_id),
                    "characters": word.characters,
                    "pinyin": word.pinyin,
                    "translation": word.translation,
                    "hsk_level": word.hsk_level,
                    "avg_score": avg_score,
                    "listen": dimension_scores["listen"],
                    "speak": dimension_scores["speak"],
                    "reading": dimension_scores["reading"],
                    "writing": dimension_scores["writing"],
                    "translation_score": dimension_scores["translation"],
                }

                word_performance_list.append(word_data)

            # 计算全部词汇的平均分
            overall_avg_score = (
                sum(total_avg_scores) / len(total_avg_scores)
                if total_avg_scores
                else 0.0
            )

            return {
                "user_id": str(user_id),
                "total_words": len(word_performance_list),
                "avg_score": round(overall_avg_score, 2),
                "word_performances": word_performance_list
            }

        except Exception as e:
            print(f"Error getting learning analytics: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_topic_learning_analytics(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户的学情分析数据（主题粒度）

        主题的分数 = 该主题下所有lesson的分数的平均值
        lesson的分数 = 该lesson下所有词汇的分数的平均值
        各维度的分数 = 该维度的正确率 * 100

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            包含学情分析数据的字典，如果查询失败返回None
        """
        try:
            # 题型映射到维度的映射表
            type_field_map = {
                "LISTEN_IMAGE_TRUE_FALSE": "listen",
                "LISTEN_IMAGE_MC": "listen",
                "LISTEN_SENTENCE_TF": "listen",
                "LISTEN_SENTENCE_QA": "listen",
                "LISTEN_DIALOGUE_QA": "listen",
                "LISTEN_PARAGRAPH_QA": "listen",
                "LISTEN_IMAGE_MATCH": "listen",
                "SPEAK_FOLLOW": "speak",
                "READ_IMAGE_TRUE_FALSE": "reading",
                "READ_SENTENCE_TF": "reading",
                "READ_SENTENCE_COMPREHENSION_CHOICE": "reading",
                "READ_WORD_GAP_FILL": "reading",
                "READ_IMAGE_MATCH": "reading",
                "READ_DIALOGUE_MATCH": "reading",
                "READ_WORD_ORDER": "reading",
                "READ_PARAGRAPH_COMPREHENSION": "reading",
                "READ_SENTENCE_ORDER": "reading",
                "STROKE_ORDER_WRITING": "writing",
                "TRANSLATE_WORD_ORDER": "translation",
            }

            # 查询用户所有的词汇学习表现
            word_performances = db.query(models.UserWordPerformance).filter(
                models.UserWordPerformance.user_id == user_id
            ).all()

            if not word_performances:
                return {
                    "user_id": str(user_id),
                    "total_topics": 0,
                    "avg_score": 0.0,
                    "topic_performances": []
                }

            # 查询用户所有的尝试记录用于计算正确率
            attempts = db.query(models.Attempt).filter(
                models.Attempt.person_id == user_id,
                models.Attempt.status == "submitted"
            ).all()

            # 构建词汇ID到性能数据的映射
            word_perf_map = {str(perf.word_id): perf for perf in word_performances}

            # 构建词汇ID到维度分数的映射（用于后续lesson和topic的聚合）
            word_dimension_scores = {}

            for performance in word_performances:
                # 查询词汇的基本信息
                word = db.query(Word).filter(Word.id == performance.word_id).first()
                if not word:
                    continue

                # 查询这个单词相关的所有练习
                word_exercises = db.query(Exercise).filter(
                    Exercise.word_id == performance.word_id
                ).all()

                word_exercise_ids = {str(ex.id) for ex in word_exercises}

                # 计算各维度的正确率
                dimension_stats = {
                    "listen": {"correct": 0, "total": 0},
                    "speak": {"correct": 0, "total": 0},
                    "reading": {"correct": 0, "total": 0},
                    "writing": {"correct": 0, "total": 0},
                    "translation": {"correct": 0, "total": 0},
                }

                # 遍历这个单词的所有尝试
                for attempt in attempts:
                    exercise_id_str = str(attempt.exercise_id)
                    if exercise_id_str not in word_exercise_ids:
                        continue

                    # 获取该练习的题型
                    exercise = next((ex for ex in word_exercises if str(ex.id) == exercise_id_str), None)
                    if not exercise or not exercise.type:
                        continue

                    exercise_type = exercise.type.name
                    dimension = type_field_map.get(exercise_type)

                    if dimension:
                        dimension_stats[dimension]["total"] += 1
                        if attempt.is_full_correct:
                            dimension_stats[dimension]["correct"] += 1

                # 计算各维度的正确率
                dimension_scores = {}
                valid_scores = []

                for dimension in ["listen", "speak", "reading", "writing", "translation"]:
                    total = dimension_stats[dimension]["total"]
                    if total == 0:
                        accuracy = 100.0
                    else:
                        correct = dimension_stats[dimension]["correct"]
                        accuracy = round((correct / total) * 100, 2)

                    dimension_scores[dimension] = accuracy
                    valid_scores.append(accuracy)

                # 词汇的平均分
                avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 100.0
                word_dimension_scores[str(performance.word_id)] = {
                    "avg_score": avg_score,
                    "dimensions": dimension_scores
                }

            # 查询用户学过的所有Topic（通过LessonWord关系）
            from app.exercise_query.models import Topic

            lesson_word_records = db.query(LessonWord).filter(
                LessonWord.word_id.in_([str(p.word_id) for p in word_performances])
            ).all()

            if not lesson_word_records:
                return {
                    "user_id": str(user_id),
                    "total_topics": 0,
                    "avg_score": 0.0,
                    "topic_performances": []
                }

            # 构建lesson ID到words的映射
            lesson_words_map = {}
            for lw in lesson_word_records:
                lesson_id = str(lw.lesson_id)
                word_id = str(lw.word_id)
                if lesson_id not in lesson_words_map:
                    lesson_words_map[lesson_id] = []
                lesson_words_map[lesson_id].append(word_id)

            # 查询所有相关的lesson
            lesson_ids = list(lesson_words_map.keys())
            lessons = db.query(Lesson).filter(Lesson.id.in_(lesson_ids)).all()

            # 构建lesson到topic的映射
            topic_lessons_map = {}
            lesson_info_map = {}

            for lesson in lessons:
                lesson_id = str(lesson.id)
                topic_id = str(lesson.topic_id)
                lesson_info_map[lesson_id] = {
                    "id": lesson_id,
                    "name": lesson.lesson_name,
                    "topic_id": topic_id
                }

                if topic_id not in topic_lessons_map:
                    topic_lessons_map[topic_id] = []
                topic_lessons_map[topic_id].append(lesson_id)

            # 查询所有相关的topic
            topic_ids = list(topic_lessons_map.keys())
            topics = db.query(Topic).filter(Topic.id.in_(topic_ids)).all()

            # 计算lesson粒度的学情数据
            lesson_performance_map = {}

            for lesson_id, word_ids in lesson_words_map.items():
                valid_word_ids = [wid for wid in word_ids if wid in word_dimension_scores]
                if not valid_word_ids:
                    continue

                # 计算lesson的各维度分数
                lesson_dimension_stats = {
                    "listen": {"scores": []},
                    "speak": {"scores": []},
                    "reading": {"scores": []},
                    "writing": {"scores": []},
                    "translation": {"scores": []},
                }

                lesson_avg_scores = []

                for word_id in valid_word_ids:
                    word_scores = word_dimension_scores[word_id]
                    lesson_avg_scores.append(word_scores["avg_score"])

                    for dimension in ["listen", "speak", "reading", "writing", "translation"]:
                        lesson_dimension_stats[dimension]["scores"].append(
                            word_scores["dimensions"][dimension]
                        )

                # 计算lesson的各维度平均分
                lesson_dimension_scores = {}
                for dimension in ["listen", "speak", "reading", "writing", "translation"]:
                    scores = lesson_dimension_stats[dimension]["scores"]
                    if scores:
                        lesson_dimension_scores[dimension] = round(sum(scores) / len(scores), 2)
                    else:
                        lesson_dimension_scores[dimension] = 100.0

                # lesson的总体平均分
                lesson_avg_score = round(sum(lesson_avg_scores) / len(lesson_avg_scores), 2) if lesson_avg_scores else 100.0

                lesson_performance_map[lesson_id] = {
                    "avg_score": lesson_avg_score,
                    "dimensions": lesson_dimension_scores
                }

            # 计算topic粒度的学情数据
            topic_performance_list = []
            topic_avg_scores = []

            for topic in topics:
                topic_id = str(topic.id)
                lesson_ids = topic_lessons_map.get(topic_id, [])
                lesson_ids = [lid for lid in lesson_ids if lid in lesson_performance_map]

                if not lesson_ids:
                    continue

                # 计算topic的各维度分数
                topic_dimension_stats = {
                    "listen": {"scores": []},
                    "speak": {"scores": []},
                    "reading": {"scores": []},
                    "writing": {"scores": []},
                    "translation": {"scores": []},
                }

                topic_avg_scores_list = []

                # 构建lesson学情数据
                lesson_performance_list = []

                for lesson_id in lesson_ids:
                    lesson_info = lesson_info_map[lesson_id]
                    lesson_perf = lesson_performance_map[lesson_id]

                    lesson_data = {
                        "lesson_id": lesson_id,
                        "lesson_name": lesson_info["name"],
                        "avg_score": lesson_perf["avg_score"],
                        "listen": lesson_perf["dimensions"]["listen"],
                        "speak": lesson_perf["dimensions"]["speak"],
                        "reading": lesson_perf["dimensions"]["reading"],
                        "writing": lesson_perf["dimensions"]["writing"],
                        "translation_score": lesson_perf["dimensions"]["translation"],
                    }

                    lesson_performance_list.append(lesson_data)
                    topic_avg_scores_list.append(lesson_perf["avg_score"])

                    # 聚合维度分数
                    for dimension in ["listen", "speak", "reading", "writing", "translation"]:
                        topic_dimension_stats[dimension]["scores"].append(
                            lesson_perf["dimensions"][dimension]
                        )

                # 计算topic的各维度平均分
                topic_dimension_scores = {}
                for dimension in ["listen", "speak", "reading", "writing", "translation"]:
                    scores = topic_dimension_stats[dimension]["scores"]
                    if scores:
                        topic_dimension_scores[dimension] = round(sum(scores) / len(scores), 2)
                    else:
                        topic_dimension_scores[dimension] = 100.0

                # topic的总体平均分
                topic_avg_score = round(sum(topic_avg_scores_list) / len(topic_avg_scores_list), 2) if topic_avg_scores_list else 100.0
                topic_avg_scores.append(topic_avg_score)

                topic_data = {
                    "topic_id": topic_id,
                    "topic_name": topic.topic_name,
                    "avg_score": topic_avg_score,
                    "listen": topic_dimension_scores["listen"],
                    "speak": topic_dimension_scores["speak"],
                    "reading": topic_dimension_scores["reading"],
                    "writing": topic_dimension_scores["writing"],
                    "translation_score": topic_dimension_scores["translation"],
                    "lessons": lesson_performance_list
                }

                topic_performance_list.append(topic_data)

            # 计算全部topic的平均分
            overall_avg_score = (
                sum(topic_avg_scores) / len(topic_avg_scores)
                if topic_avg_scores
                else 0.0
            )

            return {
                "user_id": str(user_id),
                "total_topics": len(topic_performance_list),
                "avg_score": round(overall_avg_score, 2),
                "topic_performances": topic_performance_list
            }

        except Exception as e:
            print(f"Error getting topic learning analytics: {e}")
            import traceback
            traceback.print_exc()
            return None
