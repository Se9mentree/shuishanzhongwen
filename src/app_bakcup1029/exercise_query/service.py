import math
import random
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from . import schemas, crud, models
from .formatter import format_exercises_for_api, build_public_url   # ← 新增 build_public_url
from app_1.utils.const import AVERAGE_DURATIONS_PER_TYPE

MAX_QUESTIONS_LIMIT = 50


def _calculate_average_duration(requested_types: List[str]) -> float:
    """计算请求题型的平均耗时"""
    if not requested_types:
        return AVERAGE_DURATIONS_PER_TYPE.get("DEFAULT", 15)
    total = sum(
        AVERAGE_DURATIONS_PER_TYPE.get(t, AVERAGE_DURATIONS_PER_TYPE["DEFAULT"])
        for t in requested_types
    )
    return total / len(requested_types)


def _reconstruct_composite_exercises(
    db: Session,
    exercises: List[models.Exercise],
    base_url: Optional[str] = None,
) -> List[models.Exercise]:
    """
    遍历题目列表，识别并重组复合题。
    - 对于配对题：将子题组合成一个父题，并返回父题。
    - 对于段落理解题：将父题的文章信息分发给每个子题，返回一个扁平化的子题列表。
    """
    reconstructed_list: List[models.Exercise] = []
    processed_parent_ids = set()
    MATCHING_TYPES = {"LISTEN_IMAGE_MATCH", "READ_IMAGE_MATCH", "READ_DIALOGUE_MATCH"}
    COMPREHENSION_TYPE = "READ_PARAGRAPH_COMPREHENSION"

    for exercise in exercises:
        ex_type_name = exercise.type.name if exercise.type else ""

        # 识别两种需要特殊处理的复合题
        is_matching_child = ex_type_name in MATCHING_TYPES and exercise.parent_exercise_id
        is_comprehension_parent = ex_type_name == COMPREHENSION_TYPE and not exercise.parent_exercise_id
        is_matching_parent = ex_type_name in MATCHING_TYPES and not exercise.parent_exercise_id
        is_comprehension_child = ex_type_name == COMPREHENSION_TYPE and exercise.parent_exercise_id
        if is_matching_child or is_comprehension_parent or is_matching_parent or is_comprehension_child:
            # 统一获取父题ID
            parent_id = exercise.parent_exercise_id if (is_matching_child or is_comprehension_child) else exercise.id

            if parent_id in processed_parent_ids:
                continue

            # 一次性高效查询父题及其所有子题
            parent_exercise = crud.get_parent_exercise_with_all_children(db, parent_id)
            if not parent_exercise:
                continue
            
            # 标记父题已处理，避免重复工作
            processed_parent_ids.add(parent_id)
            
            # 始终按 display_order 排序子题，确保顺序正确
            sorted_children = sorted(parent_exercise.children, key=lambda x: x.display_order)

            # --- 逻辑分支：根据题型决定是“组合”还是“分发” ---

            # 1. 段落理解题：分发父题信息，返回子题列表
            if ex_type_name == COMPREHENSION_TYPE:
                if not sorted_children:
                    continue # 如果父题下没有子题，则跳过

                parent_meta = parent_exercise.meta or {}
                passage = parent_meta.get("passage", "")
                highlighted_word = parent_meta.get("highlighted_word")

                for child in sorted_children:
                    # 将父题的文章信息和子题自身的信息合并
                    child_meta = child.meta or {}
                    enriched_meta = {
                        **child_meta,
                        "passage": passage,
                        "highlighted_word": highlighted_word
                    }
                    child.meta = enriched_meta
                    # 将“增强后”的子题直接添加到最终列表中
                    reconstructed_list.append(child)

            # 2. 配对题：组合子题信息，返回单个父题
            elif ex_type_name in MATCHING_TYPES:
                if not sorted_children:
                    continue
                
                parent_meta = parent_exercise.meta or {}
                seed = parent_meta.get("seed")
                rnd = random.Random(seed) if seed is not None else random
                reconstructed_meta = {}

                # A) 听图配对 / 读图配对
                if ex_type_name == "LISTEN_IMAGE_MATCH" or ex_type_name == "READ_IMAGE_MATCH":
                    left_items, right_items = [], []
                    for sub_ex in sorted_children:
                        sub_meta = sub_ex.meta or {}
                        media_map = {
                            link.usage_role: link.media_asset
                            for link in sub_ex.media_links
                            if link.media_asset
                        }

                        if ex_type_name == "LISTEN_IMAGE_MATCH" and "prompt_audio" in media_map:
                            audio_url = build_public_url(media_map["prompt_audio"].file_url, base_url)
                            left_items.append({
                                "audioUrl": audio_url,
                                "listeningText": sub_meta.get("listening_text", ""),
                            })
                        elif ex_type_name == "READ_IMAGE_MATCH":
                            left_items.append({
                                "text": sub_meta.get("word", ""),
                                "pinyin": sub_meta.get("pinyin", ""),
                            })

                        if "correct_image" in media_map:
                            image_url = build_public_url(media_map["correct_image"].file_url, base_url)
                            right_items.append({"imageUrl": image_url})

                    if len(left_items) != len(right_items) or not left_items:
                        continue

                    n = len(left_items)
                    labels = [chr(ord("A") + i) for i in range(n)]
                    left_indices, right_indices = list(range(n)), list(range(n))
                    rnd.shuffle(left_indices)
                    rnd.shuffle(right_indices)

                    final_left = [{"label": labels[i], **left_items[left_indices[i]]} for i in range(n)]
                    final_right = [{"label": labels[i], **right_items[right_indices[i]]} for i in range(n)]
                    answer_map = {labels[left_indices.index(i)]: labels[right_indices.index(i)] for i in range(n)}

                    if ex_type_name == "LISTEN_IMAGE_MATCH":
                        reconstructed_meta = {"audios": final_left, "images": final_right, "answer_map": answer_map}
                    else:
                        reconstructed_meta = {"texts": final_left, "images": final_right, "answer_map": answer_map}

                elif ex_type_name == "READ_DIALOGUE_MATCH":
                    questions, answers = [], []
                    for sub_ex in sorted_children:
                        sub_meta = sub_ex.meta or {}
                        questions.append({"text": sub_meta.get("utterance"), "pinyin": sub_meta.get("utter_pinyin")})
                        answers.append({"text": sub_meta.get("reply"), "pinyin": sub_meta.get("reply_pinyin")})

                    if not questions or len(questions) != len(answers):
                        continue

                    n = len(questions)
                    labels = [chr(ord("A") + i) for i in range(n)]
                    q_indices, a_indices = list(range(n)), list(range(n))
                    rnd.shuffle(q_indices)
                    rnd.shuffle(a_indices)

                    shuffled_questions = [{"label": labels[i], **questions[q_indices[i]]} for i in range(n)]
                    shuffled_answers = [{"label": labels[i], **answers[a_indices[i]]} for i in range(n)]
                    answer_map = {labels[q_indices.index(i)]: labels[a_indices.index(i)] for i in range(n)}

                    reconstructed_meta = {
                        "shuffled_questions": shuffled_questions,
                        "shuffled_answers": shuffled_answers,
                        "answers": answer_map,
                    }

                parent_exercise.meta = reconstructed_meta
                reconstructed_list.append(parent_exercise)

        elif (
            not exercise.parent_exercise_id and 
            ex_type_name != COMPREHENSION_TYPE and
            ex_type_name not in MATCHING_TYPES
        ):
            reconstructed_list.append(exercise)

    return reconstructed_list

def create_exercise_session(
    db: Session,
    request: schemas.ExerciseRequest,
    base_url: Optional[str] = None,          # ← 新增：从路由传入，用于拼绝对 URL
) -> Dict:
    """
    创建一次练习会话的主服务函数。
    """
    try:
        lesson_uuid = uuid.UUID(request.lessonId)
    except ValueError:
        return None

    lesson = crud.get_lesson_context(db, lesson_uuid)
    if not lesson:
        return None

    # 依据期望时长与题型耗时估算目标数量
    avg_duration = _calculate_average_duration(request.exerciseTypes)
    target_count = min(math.ceil(request.duration / avg_duration), MAX_QUESTIONS_LIMIT)
    target_count = max(1, int(target_count))

    # 候选题检索
    candidate_exercises = crud.get_candidate_exercises(
        db,
        lesson_id=request.lessonId,
        exercise_type_names=request.exerciseTypes,
    )

    if not candidate_exercises:
        return {}

    # 配对题重构（并在此阶段把媒体 URL 转为绝对 URL）
    reconstructed_candidates = _reconstruct_composite_exercises(
        db, candidate_exercises, base_url=base_url
    )

    # 去重（以父子重构后的父题为准）
    unique_exercises_dict = {ex.id: ex for ex in reconstructed_candidates}
    unique_candidate_exercises = list(unique_exercises_dict.values())

    # 采样
    if len(unique_candidate_exercises) <= target_count:
        selected_exercises = unique_candidate_exercises
    else:
        selected_exercises = random.sample(unique_candidate_exercises, k=target_count)

    # 统一格式化为对前端友好的结构
    # 传入 base_url，便于 formatter 在其它题型上也把 URL 拼成绝对地址
    try:
        formatted_exercises = format_exercises_for_api(
            selected_exercises,
            base_url=base_url,                      # ← 新增：继续传给 formatter
        )
    except TypeError:
        # 兼容旧签名：如果你尚未修改 formatter 的函数签名，这里会回退到旧用法
        formatted_exercises = format_exercises_for_api(selected_exercises)

    response_data: Dict = {
        "phaseId": str(lesson.topic.phase.id) if lesson.topic and lesson.topic.phase else "UNKNOWN",
        "topicId": str(lesson.topic.id) if lesson.topic else "UNKNOWN",
        "duration": request.duration,
        "count": len(formatted_exercises),
        "sessionId": f"session_{random.randint(1000, 9999)}",
        "exercises": formatted_exercises,
    }
    return response_data
