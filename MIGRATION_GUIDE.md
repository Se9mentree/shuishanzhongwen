# API 迁移指南：从 Query 参数改为从请求头读取 Token

## 概述

已更新以下 API 端点，从而不再需要在请求中显式传递 `user_id`，而是直接从请求头中的 `Authorization` token 读取用户信息：

1. **GET /lesson-progress** - 获取课程进度
2. **GET /user/word-learning-analytics** - 获取词汇粒度学情分析
3. **GET /user/topic-learning-analytics** - 获取主题粒度学情分析

## 变更详情

### 之前（旧方式）

```bash
# 需要在 Query 参数中传递 user_id
GET /lesson-progress?user_id=550e8400-e29b-41d4-a716-446655440000

GET /user/word-learning-analytics?user_id=550e8400-e29b-41d4-a716-446655440000

GET /user/topic-learning-analytics?user_id=550e8400-e29b-41d4-a716-446655440000
```

### 之后（新方式）

```bash
# 在 Authorization 请求头中传递 token
GET /lesson-progress
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

GET /user/word-learning-analytics
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

GET /user/topic-learning-analytics
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 前端使用方法

### 使用 JavaScript/Fetch API

```javascript
// 获取课程进度
const token = localStorage.getItem('access_token'); // 从登录时保存的 token

fetch('/lesson-progress', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));

// 获取词汇粒度学情分析
fetch('/user/word-learning-analytics', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));

// 获取主题粒度学情分析
fetch('/user/topic-learning-analytics', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### 使用 Axios

```javascript
const token = localStorage.getItem('access_token');
const axiosInstance = axios.create({
    baseURL: 'http://your-api-server',
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// 获取课程进度
axiosInstance.get('/lesson-progress')
    .then(response => console.log(response.data))
    .catch(error => console.error('Error:', error));

// 获取词汇粒度学情分析
axiosInstance.get('/user/word-learning-analytics')
    .then(response => console.log(response.data))
    .catch(error => console.error('Error:', error));

// 获取主题粒度学情分析
axiosInstance.get('/user/topic-learning-analytics')
    .then(response => console.log(response.data))
    .catch(error => console.error('Error:', error));
```

### 使用 cURL

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 获取课程进度
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/lesson-progress

# 获取词汇粒度学情分析
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/user/word-learning-analytics

# 获取主题粒度学情分析
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/user/topic-learning-analytics
```

## 错误处理

### 401 Unauthorized 错误

如果收到以下错误之一，说明认证失败：

```json
{
    "detail": "缺少 Authorization 请求头"
}
```
**原因**：没有在请求头中添加 `Authorization`

```json
{
    "detail": "无效的 Authorization 格式，应为 'Bearer <token>'"
}
```
**原因**：`Authorization` 的格式不正确，应该是 `Bearer <token>` 的形式

```json
{
    "detail": "无效或过期的 token"
}
```
**原因**：Token 无效或已过期，需要重新登录获取新的 token

```json
{
    "detail": "Token 中缺少 user_id"
}
```
**原因**：Token 中没有包含 `user_id`（这通常表示 token 是由旧版本生成的）

## Token 获取方式

在登录时，服务器会返回一个 `access_token`（JWT token）：

```bash
POST /auth/login
{
    "phone": "18888888888",
    "password": "password123"
}

# 响应示例
{
    "code": 1,
    "message": "登录成功",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

**前端应该**：
1. 在登录成功时，将 `access_token` 保存到本地存储（localStorage）或会话存储（sessionStorage）
2. 在后续的 API 请求中，从本地存储中读取 token，并在 Authorization 请求头中使用

## 后端实现细节

### 新的依赖函数

在 `app/core/dependencies.py` 中添加了 `get_current_user_id` 函数，该函数：

1. 从请求头中读取 `Authorization` 值
2. 验证格式是否为 `Bearer <token>`
3. 使用 `verify_token()` 验证 JWT token 的有效性
4. 从 token payload 中提取 `user_id`
5. 如果验证失败，返回 401 Unauthorized 错误

### 路由更新

```python
from app.core.dependencies import get_current_user_id

@router.get("/lesson-progress")
def get_lesson_progress(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # user_id 会自动从 token 中提取
    ...
```

## 向后兼容性

⚠️ **重要**：这些 API 变更是**破坏性的**（breaking change）。

旧的请求方式将不再有效：
```bash
GET /lesson-progress?user_id=550e8400-e29b-41d4-a716-446655440000  ❌ 不再工作
```

## 建议的迁移步骤

1. **更新登录流程**：确保登录接口返回 JWT token
2. **更新前端代码**：从本地存储中读取 token，在请求头中使用
3. **测试验证**：使用新的请求方式测试这三个 API
4. **部署**：在准备好后部署更新

## FAQ

**Q: 如何在 Swagger/OpenAPI 中测试？**

A: 在 Swagger UI 中，点击右上角的 "Authorize" 按钮，输入你的 token（不需要 "Bearer" 前缀），然后就可以直接调用 API 了。

**Q: Token 有过期时间吗？**

A: 是的。Token 的过期时间由环境变量 `ACCESS_TOKEN_EXPIRE_MINUTES` 定义（默认 120 分钟）。过期后需要重新登录。

**Q: 可以同时支持旧方式和新方式吗？**

A: 可以，但不推荐。如果需要，可以修改路由以同时接受两种方式，但这会使代码复杂。

---

有任何问题，请联系开发团队！
