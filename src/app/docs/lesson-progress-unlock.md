# 课程解锁逻辑改动说明

## 背景
为满足以下新需求，对课程解锁相关逻辑进行了调整：

1. 所有 Topic 的第 1 节课（lesson1）应自动解锁。
2. 学员完成当前课程全部练习题后，自动解锁下一节课，并将当前课程标记为 completed。

## 主要改动

### 数据模型
- `exercise_query/models.py`
  - 为 `Lesson` 增加 `display_order` 字段，用于确定 “lesson1” 及排序下一节课。

### 课程进度服务
- `features/lesson_progress/service.py`
  - `get_lesson_progress` 获取数据前调用 `ensure_first_lessons_unlocked`，仅保证 Phase/Topic 全局顺序中的第一个课程解锁（Phase 按 `display_order`、Topic 按 `topic_order`）。
  - `unlock_lesson` / `mark_lesson_in_progress` / `mark_lesson_completed` 支持跳过自动提交（`commit=False`）以便和外部事务配合。
  - 新增：
    - `ensure_first_lessons_unlocked`：确保只有第一个 Topic 的首节课为 `in_progress`，不会强制回锁用户已解锁的其它课程。
    - `handle_post_submission_progress`：在答题提交后统一处理课程状态（标记进行中，完成后标记 completed 并解锁下一课）。
    - `_unlock_next_lesson`：在课程完成时解锁下一节课。
    - `_get_initial_lesson` / `_get_lesson_exercise_ids` / `_get_attempted_exercise_ids`：分别获取起始课程（Phase.display_order → Topic.topic_order → Lesson.display_order）、课程练习集合、用户已提交练习集合等基础数据。

### 提交答案流程
- `features/user/service.py`
  - 在 `submit_answers` 成功保存单条答题记录后（且 `is_practice` 为 `False`），调用 `LessonProgressService.handle_post_submission_progress`，实时触发解锁判断；练习模式下会跳过课程进度更新。

## 实现步骤
1. **梳理课程结构数据**：确认 `Lesson` 是否具备顺序字段，若无则新增 `display_order` 以确定首节课及下一节课。
2. **完善解锁服务**：
   - 统一入口 `get_lesson_progress` 自动保障首节课解锁。
   - 引入提交后自动处理逻辑，避免在其他地方重复写解锁判断。
3. **集成到提交流程**：在 `submit_answers` 中每条提交成功后调用新的处理函数，实现提交即触发的解锁流程（练习模式 `is_practice=True` 时跳过），并在课程完成时按照 Phase.display_order → Topic.topic_order → Lesson.display_order 的顺序解锁后续课程/主题。
4. **回滚控制**：核心服务支持 `commit=False`，以便在提交事务失败时由调用方统一回滚。

## 测试建议
1. 创建新用户，调用 `get_lesson_progress`，确认仅第一个 Topic 的 lesson1 处于解锁状态。
2. 选择某节已解锁课程，提交练习：
   - 在未完成全部练习前，下一课保持锁定，当前课程状态为 `in_progress`。
   - 完成所有练习后，当前课程状态变为 `completed`，下一课自动解锁。
3. 覆盖提交失败场景（数据库异常等），确认回滚后不会残留半完成的数据。

> 当前环境未安装 `pytest`，执行 `python -m pytest` 会提示缺少模块；如需自动化测试，请先安装依赖。
