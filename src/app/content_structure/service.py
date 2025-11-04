import json
from typing import List, Dict, Any,Optional


async def get_full_content_structure(cur) -> List[Dict[str, Any]]:
    """
    从数据库中获取完整的 Phase -> Topic -> Lesson 结构。
    
    修改逻辑:
    1. 保留 ID 为 "a78afe03-5614-47be-8d0b-b6cc854c07e2" 的特定主题。
    2. 其他主题，仅保留课程数 (lessons) >= 3 的主题。
    3. 对所有最终保留的 Topic，进行 *全局* 重新编号 (topic_order 从 1 开始，跨 Phase 连续)。
    """
    
    cur.execute(
        """
        SELECT id, topic_id, lesson_name, display_order 
        FROM content_new.lessons
        ORDER BY topic_id, display_order;
        """
    )
    lessons_by_topic: Dict[str, List[Dict[str, Any]]] = {}
    for row in cur.fetchall():
        lesson_data = {
            "id": row[0],
            "lesson_name": row[2],
            "display_order": row[3]
        }
        topic_id = str(row[1]) 
        if topic_id not in lessons_by_topic:
            lessons_by_topic[topic_id] = []
        lessons_by_topic[topic_id].append(lesson_data)


    cur.execute(
        """
        SELECT id, phase_id, topic_name, topic_order
        FROM content_new.topics
        ORDER BY phase_id, topic_order;
        """
    )
    topics_by_phase: Dict[str, List[Dict[str, Any]]] = {}
    for row in cur.fetchall():
        topic_id = str(row[0]) # 这是 Topic 的 ID
        topic_name = row[2] 
        
        topic_lessons = lessons_by_topic.get(topic_id, [])

        # --- MODIFICATION: 筛选逻辑 ---
        # 检查是否为 *指定的* "个人信息" ID
        is_specific_topic = (topic_id == "a78afe03-5614-47be-8d0b-b6cc854c07e2")
        # 检查课程数是否达标
        has_enough_lessons = (len(topic_lessons) >= 3)
        
        # 如果 不是 "指定ID" 且 课程数不足，则跳过
        if not is_specific_topic and not has_enough_lessons:
            continue 
        # --- END MODIFICATION ---

        topic_data = {
            "id": topic_id,
            "topic_name": topic_name,
            "topic_order": row[3], # 暂时保留数据库中的 order，用于维持 Phase 内的原始顺序
            "lessons": topic_lessons
        }
        phase_id = str(row[1])
        if phase_id not in topics_by_phase:
            topics_by_phase[phase_id] = []
        topics_by_phase[phase_id].append(topic_data)

    cur.execute(
        """
        SELECT id, name, display_order
        FROM content_new.phases
        ORDER BY display_order;
        """
    )
    result_list: List[Dict[str, Any]] = []
    
    # 全局 Topic 计数器
    global_topic_order_counter = 1 
    
    for row in cur.fetchall():
        phase_id = str(row[0])
        
        # 获取该 phase 下所有已通过筛选的 topics (保持原始数据库顺序)
        phase_topics_filtered = topics_by_phase.get(phase_id, [])
        
        if not phase_topics_filtered:
             continue
        
        # 重新编号逻辑
        phase_topics_renumbered = []
        
        # 遍历该 Phase 下已过滤的 topic 列表
        for topic_data in phase_topics_filtered:
            # 使用全局计数器覆盖 topic_order
            topic_data['topic_order'] = global_topic_order_counter
            phase_topics_renumbered.append(topic_data)
            global_topic_order_counter += 1 # 计数器递增
        
        phase_data = {
            "id": phase_id,
            "name": row[1],
            "display_order": row[2],
            "topics": phase_topics_renumbered # 使用重新编号后的列表
        }
        result_list.append(phase_data)

    return result_list


async def get_dialogue_by_lesson_id(cur, lesson_id: str) -> Optional[Dict[str, Any]]:
    """
    根据 lesson_id 从数据库获取 dialogue 字段并将其解析为 Python 字典。
    """
    cur.execute(
        """
        SELECT dialogue
        FROM content_new.lessons
        WHERE id = %s;
        """,
        (lesson_id,)
    )
    
    row = cur.fetchone() # 获取单行结果

    if not row:
        # 课程序号不存在
        return None 
    
    dialogue_str = row[0]
    
    if not dialogue_str:
        # 课程存在，但 dialogue 字段为 NULL (尚未生成)
        return None 
    
    # 尝试将 JSON 字符串解析为字典
    # (如果解析失败，异常将由 router.py 捕获)
    dialogue_data = json.loads(dialogue_str)
    
    return dialogue_data

async def get_all_scenarios_with_lessons(cur) -> List[Dict[str, Any]]:
    """
    从数据库中获取所有场景及其关联的课程详情。
    """
    # 联接 scenarios, scenario_lessons, lessons 三张表获取所有必要数据
    cur.execute(
        """
        SELECT
            s.id AS scenario_id,
            s.name AS scenario_name,
            s.description,
            s.display_order,
            l.id AS lesson_id,
            l.lesson_name,
            sl.relevance_order
        FROM
            content_new.scenarios AS s
        JOIN
            content_new.scenario_lessons AS sl ON s.id = sl.scenario_id
        JOIN
            content_new.lessons AS l ON sl.lesson_id = l.id
        ORDER BY
            s.display_order, sl.relevance_order;
        """
    )
    
    records = cur.fetchall()
    if not records:
        return []

    # 使用字典进行数据重塑，将课程嵌套到其对应的场景下
    scenarios_map: Dict[str, Dict[str, Any]] = {}

    for row in records:
        # PostgreSQL 游标默认返回的是元组，这里按位置索引获取字段
        scenario_id = str(row[0])
        
        # 1. 初始化场景数据 (如果尚未存在)
        if scenario_id not in scenarios_map:
            scenarios_map[scenario_id] = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "display_order": row[3],
                "lessons": []
            }
        
        # 2. 添加嵌套的课程详情
        lesson_detail = {
            "lesson_id": row[4],
            "lesson_name": row[5],
            "relevance_order": row[6]
        }
        scenarios_map[scenario_id]["lessons"].append(lesson_detail)
        
    # 返回重塑后的场景列表
    result_list = list(scenarios_map.values())
    return result_list