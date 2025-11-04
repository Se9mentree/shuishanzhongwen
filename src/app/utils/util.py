import os
import psycopg2
from pypinyin import lazy_pinyin,Style
import jieba
from typing import List
import os
import io
import json
import mimetypes
import hashlib
import asyncio
import re
import subprocess
from datetime import datetime
from typing import Optional, Tuple,Dict,Any,List

import uuid
import psycopg2
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field,validator
from PIL import Image
import random

from app.utils.const import DATABASE_URL,MEDIA_ROOT,MEDIA_PUBLIC_BASE,LLM_API_KEY,APP_ID,QUESTION_TYPE_MAPPING

PUNCTUATION_REGEX = re.compile(
    r"^[!" + re.escape(r"\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~") + r"\u3000-\u303f\uff00-\uffef\u2000-\u206f]+$"
)
DATABASE_URL = os.getenv("DATABASE_URL")

def _db():
    return psycopg2.connect(DATABASE_URL)


def to_pinyin_sentence(text: str) -> str:
    """将一个中文字符串转换为带声调的、以空格分隔的拼音字符串。"""
    if not text:
        return ""
    pinyin_list = lazy_pinyin(text, style=Style.TONE)
    return ' '.join(p for p in pinyin_list if p.strip())

def segment_sentence(sentence: str) -> List[str]:
    """
    使用 jieba 对句子进行分词，并自动过滤掉所有纯标点符号。
    """
    words = list(jieba.cut(sentence))

    filtered_words = []
    for word in words:
        cleaned_word = word.strip()

        if cleaned_word and not PUNCTUATION_REGEX.match(cleaned_word):
            filtered_words.append(cleaned_word)
            
    return filtered_words

def _sha256(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def _date_parts():
    d = datetime.utcnow()
    return d.strftime("%Y"), d.strftime("%m"), d.strftime("%d")

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _guess_ext(mime_type: str, fallback: str) -> str:
    ext = mimetypes.guess_extension(mime_type or "") or fallback
    return {".jpe": ".jpg"}.get(ext, ext)

def _db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL 未配置")
    return psycopg2.connect(DATABASE_URL)

def _ffprobe_duration_ms(abs_path: str) -> Optional[int]:
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", abs_path
        ], stderr=subprocess.DEVNULL)
        dur = float(out.decode().strip())
        return int(dur * 1000)
    except Exception:
        return None

def save_image_asset(cur, data: bytes, mime_type: str) -> str:
    """
    将图片字节码保存到文件系统, 并在media_assets表中创建记录。
    
    Args:
        cur: 数据库游标对象。
        data: 图片的二进制数据。
        mime_type: 图片的MIME类型。

    Returns:
        新创建的媒体资产在数据库中的UUID。
    """
    # 1. 保留原有的文件保存逻辑
    sha = _sha256(data)
    y, m, d = _date_parts()
    prefix = sha[:2]
    ext = _guess_ext(mime_type, ".jpg")
    # 注意：我们存储的是相对路径，这与我们的方案B设计一致
    rel_path = f"images/{y}/{m}/{d}/{prefix}/{sha}{ext}"
    abs_path = os.path.join(MEDIA_ROOT, rel_path)
    _ensure_dir(os.path.dirname(abs_path))
    
    img = Image.open(io.BytesIO(data))
    w, h = img.size
    with open(abs_path, "wb") as f:
        f.write(data)

    # 2. 【新增】将元数据存入数据库
    # 使用 ON CONFLICT 可以在文件已存在时避免重复插入和报错，保证幂等性。
    sql = """
        INSERT INTO content_new.media_assets (file_url, file_type, mime_type, description)
        VALUES (%s, 'image', %s, %s)
        ON CONFLICT (file_url) DO UPDATE SET updated_at = NOW()
        RETURNING id;
    """
    description = f"Image asset, SHA256: {sha}, Dimensions: {w}x{h}"
    cur.execute(sql, (rel_path, mime_type, description))
    media_asset_id = cur.fetchone()[0]

    # 3. 【修改】返回数据库中的ID
    return media_asset_id


def save_audio_asset(cur, data: bytes, mime_type: str) -> str:
    """
    将音频字节码保存到文件系统, 并在media_assets表中创建记录。

    Args:
        cur: 数据库游标对象。
        data: 音频的二进制数据。
        mime_type: 音频的MIME类型。

    Returns:
        新创建的媒体资产在数据库中的UUID。
    """
    # 1. 保留原有的文件保存逻辑
    sha = _sha256(data)
    y, m, d = _date_parts()
    prefix = sha[:2]
    ext = _guess_ext(mime_type, ".mp3")
    rel_path = f"audios/{y}/{m}/{d}/{prefix}/{sha}{ext}"
    abs_path = os.path.join(MEDIA_ROOT, rel_path)
    _ensure_dir(os.path.dirname(abs_path))
    with open(abs_path, "wb") as f:
        f.write(data)

    # 2. 【新增】将元数据存入数据库
    sql = """
        INSERT INTO content_new.media_assets (file_url, file_type, mime_type, description)
        VALUES (%s, 'audio', %s, %s)
        ON CONFLICT (file_url) DO UPDATE SET updated_at = NOW()
        RETURNING id;
    """
    description = f"Audio asset, SHA256: {sha}"
    cur.execute(sql, (rel_path, mime_type, description))
    media_asset_id = cur.fetchone()[0]

    # 3. 【修改】返回数据库中的ID
    return media_asset_id


def generate_from_llm(prompt: str) -> str:
    url = f"https://dashscope.aliyuncs.com/api/v1/apps/{APP_ID}/completion"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "input": { "prompt": prompt },
        "parameters": {},
        "debug": {}
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()
        if 'output' in result and 'text' in result['output']:
            return result['output']['text']
        else:
            return "API响应格式不正确，无法提取文本。"
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return "发生错误，无法生成文本。"
    except json.JSONDecodeError:
        print("API响应不是有效的JSON格式。")
        return "发生错误，无法解析API响应。"

def generate_voice(text: str) -> str:
    if not LLM_API_KEY:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")
    url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation' 
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-tts",
        "input": { "text": text, "voice":"Chelsie" }
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result=response.json()
        audio_url = result.get('output', {}).get('audio', {}).get('url')
        if not audio_url:
            raise RuntimeError("TTS 响应成功，但未找到音频 URL")
        return audio_url
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API 请求失败: {e}")

def url_without_course(url: Optional[str]) -> Optional[str]:
    return url

def generate_image(prompt: str, negative: str):
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    payload = {
        "model": "wanx2.1-t2i-turbo",
        "input": {
            "prompt": prompt,
            "negative_prompt": negative
        },
        "parameters": {
            "size": "1024*1024",
            "n": 1
        }
    }
    try:
        response = requests.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"提交文生图任务失败: {e}")

def get_text_to_image_task_status(task_id: str):
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    try:
        response = requests.get(status_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"查询任务状态失败: {e}")

async def _poll_image_task(task_id: str, max_try: int = 20, interval_s: float = 1.5) -> Optional[str]:
    """轮询文生图任务直至拿到图片URL；失败/超时返回 None"""
    for _ in range(max_try):
        status = get_text_to_image_task_status(task_id)
        out = status.get("output") or {}
        if out.get("task_status") == "SUCCEEDED":
            return (out.get("results") or [{}])[0].get("url")
        if out.get("task_status") == "FAILED":
            return None
        await asyncio.sleep(interval_s)
    return None

def segment_paragraph_to_sentences(paragraph: str) -> List[str]:
    """
    使用正则表达式将段落切分为句子列表，并保留结尾标点。
    """
    paragraph = paragraph.strip()
    if not paragraph:
        return []

    parts = re.split(r'([。！？])', paragraph)

    sentences = []
    for i in range(0, len(parts) - 1, 2):
        sentence_text = (parts[i] + parts[i+1]).strip()
        if sentence_text:
            sentences.append(sentence_text)

    if len(parts) % 2 == 1 and parts[-1].strip():
        sentences.append(parts[-1].strip())

    return sentences


def convert_chinese_types_to_english(chinese_types: List[str]) -> List[str]:
    """
    将用户输入的中文题型名称转换为数据库中的英文题型标识符。

    参数：
    - chinese_types: 中文题型列表，例如 ['听', '读']

    返回：
    - 对应的英文题型列表，例如 ['LISTEN_IMAGE_TRUE_FALSE', 'LISTEN_IMAGE_MC', ...]

    示例：
    >>> convert_chinese_types_to_english(['听'])
    ['LISTEN_IMAGE_TRUE_FALSE', 'LISTEN_IMAGE_MC', 'LISTEN_IMAGE_MATCH', ...]
    """
    english_types = []

    for chinese_type in chinese_types:
        if chinese_type in QUESTION_TYPE_MAPPING:
            # 将该中文题型对应的所有英文类型加入列表
            english_types.extend(QUESTION_TYPE_MAPPING[chinese_type])

    return english_types


