#!/usr/bin/env python3
"""
Quick helper to inspect lesson_progress records for a given user.

Usage:
    DATABASE_URL=postgresql://... python3 scripts/check_user_progress.py ae354a89-19f2-44b2-9973-edd8832f07e6
"""
import os
import sys
import uuid
from datetime import timezone

from sqlalchemy import create_engine, text


def utc_iso(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check_user_progress.py <user_id>")
        sys.exit(1)

    try:
        user_id = uuid.UUID(sys.argv[1])
    except ValueError:
        print("Invalid UUID provided.")
        sys.exit(1)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Please set DATABASE_URL before running this script.")
        sys.exit(1)

    engine = create_engine(db_url)

    query = text(
        """
        SELECT
            lp.topic_id,
            lp.lesson_id,
            lp.status,
            lp.unlock_date,
            lp.first_accessed_at,
            lp.completed_at
        FROM events.lesson_progress lp
        WHERE lp.user_id = :user_id
        ORDER BY lp.updated_at DESC;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query, {"user_id": str(user_id)}).fetchall()

    if not rows:
        print(f"No lesson_progress records found for user {user_id}.")
        return

    print(f"Lesson progress for user {user_id}:")
    for row in rows:
        topic_id, lesson_id, status, unlock_date, first_accessed_at, completed_at = row
        print(
            f"- topic_id: {topic_id}, lesson_id: {lesson_id}, status: {status}, "
            f"unlock_date: {utc_iso(unlock_date)}, "
            f"first_accessed_at: {utc_iso(first_accessed_at)}, "
            f"completed_at: {utc_iso(completed_at)}"
        )


if __name__ == "__main__":
    main()
