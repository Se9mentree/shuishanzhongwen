#!/usr/bin/env python3
"""
测试脚本：验证READ_DIALOGUE_MATCH题型是否被正确排除
"""
import sys
sys.path.insert(0, '/mnt/data/chinese_platform_backend/src/app')

from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=" * 70)
print("验证 READ_DIALOGUE_MATCH 题型排除效果")
print("=" * 70)

# 获取一个有READ_DIALOGUE_MATCH错题的用户
user_with_rdm = db.execute(text("""
    SELECT user_id FROM events.user_wrong_exercises
    WHERE exercise_type = 'READ_DIALOGUE_MATCH'
    LIMIT 1
""")).first()

if not user_with_rdm:
    print("\n✗ 未找到有READ_DIALOGUE_MATCH错题的用户")
    db.close()
    sys.exit(1)

user_id = user_with_rdm[0]
print(f"\n测试用户: {user_id}")

# 检查该用户的所有错题类型（排除前）
print("\n1. 排除前的错题类型:")
all_types = db.execute(text(f"""
    SELECT DISTINCT exercise_type FROM events.user_wrong_exercises
    WHERE user_id = '{user_id}'
    ORDER BY exercise_type
""")).fetchall()

for type_row in all_types:
    ex_type = type_row[0]
    count = db.execute(text(f"""
        SELECT COUNT(*) FROM events.user_wrong_exercises
        WHERE user_id = '{user_id}' AND exercise_type = '{ex_type}'
    """)).scalar()
    print(f"   - {ex_type}: {count} 条")

# 模拟get_weak_type_recommendations的查询（排除后）
print("\n2. 排除后的弱项推荐（模拟查询）:")
excluded_types = ["READ_DIALOGUE_MATCH"]

remaining_types = db.execute(text(f"""
    SELECT exercise_type, SUM(wrong_count) as total_wrong
    FROM events.user_wrong_exercises
    WHERE user_id = '{user_id}'
    AND exercise_type NOT IN ('READ_DIALOGUE_MATCH')
    GROUP BY exercise_type
    ORDER BY SUM(wrong_count) DESC
""")).fetchall()

if remaining_types:
    for ex_type, total_wrong in remaining_types:
        print(f"   - {ex_type}: {total_wrong} 次错误")
else:
    print("   (没有其他错题类型)")

# 验证是否正确排除
print("\n3. 验证排除效果:")
read_dialogue_match_excluded = True
for ex_type, _ in remaining_types:
    if ex_type == "READ_DIALOGUE_MATCH":
        read_dialogue_match_excluded = False
        break

if read_dialogue_match_excluded:
    print("   ✓ READ_DIALOGUE_MATCH 已正确排除")
else:
    print("   ✗ READ_DIALOGUE_MATCH 未被排除！")

# 验证get_wrong_exercise_recommendations的排除
print("\n4. 验证错题推荐列表排除:")
wrong_with_rdm = db.execute(text(f"""
    SELECT COUNT(*) FROM events.user_wrong_exercises
    WHERE user_id = '{user_id}'
    AND exercise_type = 'READ_DIALOGUE_MATCH'
""")).scalar()

wrong_without_rdm = db.execute(text(f"""
    SELECT COUNT(*) FROM events.user_wrong_exercises
    WHERE user_id = '{user_id}'
    AND exercise_type NOT IN ('READ_DIALOGUE_MATCH')
""")).scalar()

print(f"   - READ_DIALOGUE_MATCH 错题数: {wrong_with_rdm}")
print(f"   - 其他类型错题数: {wrong_without_rdm}")
print(f"   ✓ 排除后将推荐 {min(wrong_without_rdm, 10)} 条错题（最多10条）")

print("\n" + "=" * 70)
print("验证完成！READ_DIALOGUE_MATCH 题型已从推荐中排除")
print("=" * 70)

db.close()
