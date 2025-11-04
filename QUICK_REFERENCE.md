# 快速参考 - Token-Based Authentication 改动

## 核心改动总结

### ✅ 三个 API 已更新

| 接口 | 之前 | 之后 |
|------|------|------|
| **GET /lesson-progress** | `?user_id=...` | `Authorization: Bearer ...` |
| **GET /user/word-learning-analytics** | `?user_id=...` | `Authorization: Bearer ...` |
| **GET /user/topic-learning-analytics** | `?user_id=...` | `Authorization: Bearer ...` |

## 前端调用方式

### 最简单的方式：使用 Fetch API

```javascript
const token = localStorage.getItem('access_token');

// 获取课程进度
fetch('/lesson-progress', {
    headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(data => console.log(data));
```

### 使用 Axios（推荐）

```javascript
const token = localStorage.getItem('access_token');
const api = axios.create({
    headers: { 'Authorization': `Bearer ${token}` }
});

api.get('/lesson-progress').then(r => console.log(r.data));
api.get('/user/word-learning-analytics').then(r => console.log(r.data));
api.get('/user/topic-learning-analytics').then(r => console.log(r.data));
```

### 使用 cURL（测试）

```bash
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/lesson-progress
```

## 后端技术细节

### 1. 新增文件
- ✨ **app/core/dependencies.py** - 包含 `get_current_user_id()` 依赖函数

### 2. 修改文件
- 📝 **app/features/lesson_progress/router.py** - 移除 Query 参数，使用依赖
- 📝 **app/features/user/router.py** - 两个学情分析接口更新

### 3. 依赖函数实现

```python
async def get_current_user_id(authorization: Optional[str] = Header(None)) -> uuid.UUID:
    """从 Authorization 请求头自动提取 user_id"""
    # 1. 检查头是否存在
    # 2. 验证 Bearer 格式
    # 3. 解析 JWT token
    # 4. 提取 user_id
    # 5. 返回或抛出 401
```

## 错误处理

### 401 Unauthorized - 常见错误

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| 缺少 Authorization 请求头 | 没有添加请求头 | 加上 `Authorization: Bearer <token>` |
| 无效的 Authorization 格式 | 格式不对 | 使用 `Bearer <token>` 格式（注意空格） |
| 无效或过期的 token | Token 过期 | 重新登录获取新 token |
| Token 中缺少 user_id | Token 生成有问题 | 检查登录接口返回内容 |

## 兼容性

- ⚠️ **破坏性更改** - 旧的 Query 参数方式不再工作
- 需要更新所有前端代码
- 后端已验证编译通过

## 文档位置

- 📖 **详细迁移指南**: `MIGRATION_GUIDE.md`
- 📊 **实现总结**: `IMPLEMENTATION_SUMMARY.md`
- 🧪 **测试脚本**: `test_token_auth.py`

## 快速检查清单

- [ ] 登录接口返回 `access_token`（JWT）
- [ ] 前端存储 token 到 localStorage
- [ ] 所有请求都在 Authorization 头添加 token
- [ ] Token 格式为 `Bearer <token>`（注意大小写和空格）
- [ ] 测试三个接口都能正常工作
- [ ] 处理 401 错误和 token 过期

## 工作流程图

```
用户登录
    ↓
返回 access_token
    ↓
存到 localStorage
    ↓
后续请求添加到 Authorization 头
    ↓
get_current_user_id() 自动验证和提取
    ↓
执行业务逻辑
    ↓
返回数据
```

## 常见问题

**Q: Swagger/OpenAPI 如何测试？**
A: 点击右上角"Authorize"，粘贴 token（无需 Bearer 前缀）

**Q: Token 多久过期？**
A: 默认 120 分钟（可通过 `ACCESS_TOKEN_EXPIRE_MINUTES` 配置）

**Q: 需要在 URL 中传递 user_id 吗？**
A: 不需要，现在从 token 中自动提取

**Q: 支持 OAuth/三方登录吗？**
A: 目前只支持 JWT token，可扩展支持

---

更新日期: 2025-10-29
