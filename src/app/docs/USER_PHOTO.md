# 个人信息接口文档

## 2. 上传用户头像

### 基本信息

| 项目 | 内容 |
|------|------|
| **接口名称** | 上传用户头像 |
| **请求方法** | POST |
| **请求路径** | `/user/avatar` |
| **Content-Type** | multipart/form-data |
| **认证方式** | Token (Bearer Token) |

### 请求参数

| 参数名 | 数据类型 | 必填 | 说明 |
|--------|---------|------|------|
| avatar | File | 是 | 头像图片文件，支持 jpg、png 等图片格式 |

### 文件限制

| 限制项 | 值 |
|--------|-----|
| **最大文件大小** | 10 MB（建议） |
| **支持格式** | jpg, jpeg, png, gif, webp |
| **推荐分辨率** | 200x200 px 或更高 |
| **推荐宽高比** | 1:1（正方形） |

### cURL 请求示例

```bash
curl -X POST http://api.example.com/user/avatar \
  -F "avatar=@/path/to/avatar.jpg"
```

### HTTP 请求示例

```http
POST /user/avatar HTTP/1.1
Host: api.example.com
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Length: 245821

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="avatar"; filename="avatar.jpg"
Content-Type: image/jpeg

[JPEG 二进制图片数据]

------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

**说明：**
- `boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW` 是分隔符，用于分隔表单字段
- `[JPEG 二进制图片数据]` 是实际的图片文件内容（二进制格式）
- `Content-Length` 是整个请求体的大小（字节数）
- `Authorization` 令牌由 HTTP 客户端库自动注入到请求头中

