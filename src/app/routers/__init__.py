from app.features import auth_router, user_router
from app.features.lesson_progress.router import router as lesson_progress_router
from app.exercise_generate.router import router as generator_router
from app.exercise_query.router import router as exercise_query_router
from app.content_structure.router import router as content_structure_router
from app.lesson_words_query.router import router as lesson_words_query_router

# 所有启用的路由
all_routers = [
    auth_router,         # 认证相关接口
    user_router,         # 用户相关接口
    lesson_progress_router,  # 课程进度
    generator_router,    # 题目生成器
    exercise_query_router,  # 题目查询
    content_structure_router,
    lesson_words_query_router
]

__all__ = ["all_routers"]
