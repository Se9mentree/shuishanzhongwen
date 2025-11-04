#!/usr/bin/env python3
"""
数据库清理脚本：删除那些存在于错题表里面但是在题目列表里面已经删除的错题记录和attempt记录
"""
import os
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@host:port/dbname")

# 创建数据库连接
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def cleanup_orphaned_records():
    """清理孤立的错题和attempt记录"""
    db = SessionLocal()
    try:
        # 第一步：找出那些exercise_id不存在于exercises表的错题记录
        print("=" * 60)
        print("开始检查并删除孤立的错题记录和attempt记录...")
        print("=" * 60)

        # 查询孤立的错题记录（在events.user_wrong_exercises中但exercise不存在）
        orphaned_wrong_exercises_query = """
        SELECT
            uwe.id,
            uwe.user_id,
            uwe.exercise_id,
            uwe.word_id,
            uwe.created_at
        FROM events.user_wrong_exercises AS uwe
        WHERE NOT EXISTS (
            SELECT 1 FROM content_new.exercises AS e
            WHERE e.id = uwe.exercise_id
        )
        ORDER BY uwe.created_at DESC;
        """

        orphaned_wrong_exercises = db.execute(text(orphaned_wrong_exercises_query)).fetchall()
        print(f"\n找到 {len(orphaned_wrong_exercises)} 条孤立的错题记录:")

        if orphaned_wrong_exercises:
            for i, record in enumerate(orphaned_wrong_exercises, 1):
                print(f"  {i}. 错题ID: {record[0]}, 用户ID: {record[1]}, 题目ID: {record[2]}, 词汇ID: {record[3]}, 创建时间: {record[4]}")

        # 第二步：找出对应这些孤立错题的attempt记录
        orphaned_attempts_query = """
        SELECT
            a.id,
            a.person_id,
            a.exercise_id,
            a.created_at,
            a.status
        FROM events.attempt AS a
        WHERE NOT EXISTS (
            SELECT 1 FROM content_new.exercises AS e
            WHERE e.id = a.exercise_id
        )
        ORDER BY a.created_at DESC;
        """

        orphaned_attempts = db.execute(text(orphaned_attempts_query)).fetchall()
        print(f"\n找到 {len(orphaned_attempts)} 条对应的孤立attempt记录:")

        if orphaned_attempts:
            for i, record in enumerate(orphaned_attempts, 1):
                print(f"  {i}. Attempt ID: {record[0]}, 用户ID: {record[1]}, 题目ID: {record[2]}, 创建时间: {record[3]}, 状态: {record[4]}")

        # 第三步：删除操作
        total_records_to_delete = len(orphaned_wrong_exercises) + len(orphaned_attempts)

        if total_records_to_delete == 0:
            print("\n✓ 数据库干净，没有孤立记录需要删除。")
            return

        print(f"\n{'=' * 60}")
        print(f"将要删除的总记录数: {total_records_to_delete}")
        print(f"  - 孤立的错题记录: {len(orphaned_wrong_exercises)}")
        print(f"  - 孤立的attempt记录: {len(orphaned_attempts)}")
        print(f"{'=' * 60}")

        # 要求用户确认
        user_input = input("\n是否确认删除这些孤立的记录? (yes/no): ").strip().lower()

        if user_input != 'yes':
            print("操作已取消。")
            return

        # 删除孤立的错题记录
        if orphaned_wrong_exercises:
            delete_wrong_exercises_query = """
            DELETE FROM events.user_wrong_exercises
            WHERE NOT EXISTS (
                SELECT 1 FROM content_new.exercises AS e
                WHERE e.id = exercise_id
            );
            """
            result = db.execute(text(delete_wrong_exercises_query))
            db.commit()
            deleted_count = result.rowcount
            print(f"\n✓ 已删除 {deleted_count} 条孤立的错题记录")

        # 删除孤立的attempt记录
        if orphaned_attempts:
            delete_attempts_query = """
            DELETE FROM events.attempt
            WHERE NOT EXISTS (
                SELECT 1 FROM content_new.exercises AS e
                WHERE e.id = exercise_id
            );
            """
            result = db.execute(text(delete_attempts_query))
            db.commit()
            deleted_count = result.rowcount
            print(f"✓ 已删除 {deleted_count} 条孤立的attempt记录")

        print("\n" + "=" * 60)
        print("数据库清理完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 发生错误: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_database_stats():
    """获取数据库统计信息"""
    db = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("数据库统计信息")
        print("=" * 60)

        # 题目总数
        exercises_count = db.execute(text("SELECT COUNT(*) FROM content_new.exercises")).scalar()
        print(f"exercises (题目总数): {exercises_count}")

        # 错题总数
        wrong_exercises_count = db.execute(text("SELECT COUNT(*) FROM events.user_wrong_exercises")).scalar()
        print(f"user_wrong_exercises (错题总数): {wrong_exercises_count}")

        # attempt总数
        attempts_count = db.execute(text("SELECT COUNT(*) FROM events.attempt")).scalar()
        print(f"attempt (attempt总数): {attempts_count}")

        # 孤立的错题记录
        orphaned_wrong = db.execute(text("""
            SELECT COUNT(*) FROM events.user_wrong_exercises
            WHERE NOT EXISTS (SELECT 1 FROM content_new.exercises WHERE id = exercise_id)
        """)).scalar()
        print(f"\n孤立的错题记录: {orphaned_wrong}")

        # 孤立的attempt记录
        orphaned_attempts = db.execute(text("""
            SELECT COUNT(*) FROM events.attempt
            WHERE NOT EXISTS (SELECT 1 FROM content_new.exercises WHERE id = exercise_id)
        """)).scalar()
        print(f"孤立的attempt记录: {orphaned_attempts}")

        print("=" * 60 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    try:
        # 先显示统计信息
        get_database_stats()

        # 执行清理
        cleanup_orphaned_records()

        # 显示清理后的统计信息
        get_database_stats()

    except Exception as e:
        print(f"脚本执行失败: {str(e)}")
        exit(1)
