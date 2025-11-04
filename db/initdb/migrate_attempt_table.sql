-- 迁移脚本: 删除 attempt 表中的多余列
-- 执行时间: $(date)
-- 说明: 删除 exercise_format, exercise_skill, exercise_hsk_level, exercise_difficulty, full_marks, exercise_points 列

BEGIN;

-- 检查并删除 exercise_format 列
ALTER TABLE events.attempt
DROP COLUMN IF EXISTS exercise_format;

-- 检查并删除 exercise_skill 列
ALTER TABLE events.attempt
DROP COLUMN IF EXISTS exercise_skill;

-- 检查并删除 exercise_hsk_level 列
ALTER TABLE events.attempt
DROP COLUMN IF EXISTS exercise_hsk_level;

-- 检查并删除 exercise_difficulty 列
ALTER TABLE events.attempt
DROP COLUMN IF EXISTS exercise_difficulty;

-- 检查并删除 full_marks 列
ALTER TABLE events.attempt
DROP COLUMN IF EXISTS full_marks;

-- 检查并删除 exercise_points 列
ALTER TABLE events.attempt
DROP COLUMN IF EXISTS exercise_points;

-- 为 total_score 列添加注释
COMMENT ON COLUMN events.attempt.total_score IS '做完一题后给用户的奖励积分';

COMMIT;
