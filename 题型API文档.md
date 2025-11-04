## 1. 听力选择题（纯文字）

```json
{
  "exercise_id": "string",
  "question_type": "听录音·句子问答（单选）/听录音·对话问答（单选）/听录音·段落问答（单选）",
  "hsk_level": 1,
  "listening_text": "听力文本内容",
  "question": "问题内容",
  "question_pinyin": "wèntí nèiróng",
  "audio_url": "https://...",
  "options": {
    "A": {"text": "选项A文本"},
    "B": {"text": "选项B文本"},
    "C": {"text": "选项C文本"}
  },
  "correct_answer": "A"
}
```
---

## 2. 听力判断题（纯文字）

```json
{
  "exercise_id": "string",
  "question_type": "听录音·句子判断",
  "hsk_level": 1,
  "difficulty": 2,
  "listening_text": "听力文本内容",
  "statement": "判断陈述内容",
  "statement_pinyin": "pànduàn chénshù nèiróng",
  "audio_url": "https://...",
  "correct_answer": true
}
```
---

## 3. 阅读选择题（纯文字）

### 3.1 句子理解

**返回数据格式：**
```json
{
  "exercise_id": "string",
  "question_type": "阅读·句子理解",
  "hsk_level": 1,
  "difficulty": 2,
  "passage": "阅读文本内容",
  "question": "问题内容",
  "options": {
    "A": {"text": "选项A文本"},
    "B": {"text": "选项B文本"},
    "C": {"text": "选项C文本"}
  },
  "correct_answer": "A"
}
```

### 3.2 段落理解

**返回数据格式：**
```json
{
  "exercise_id": "string",
  "question_type": "阅读·段落理解",
  "hsk_level": 1,
  "difficulty": 2,
  "passage": "段落文本内容",
  "highlighted_word": "关键词",
  "questions": [
    {
      "sub_exercise_id": "string",
      "stem": "问题1",
      "options": {
        "A": {"text": "选项A文本"},
        "B": {"text": "选项B文本"},
        "C": {"text": "选项C文本"}
      },
      "correct_answer": "A"
    }
  ]
}
```


## 4. 阅读判断题（纯文字）

**返回数据格式：**
```json
{
  "exercise_id": "string",
  "question_type": "阅读·句子判断",
  "hsk_level": 1,
  "difficulty": 2,
  "passage": "阅读文本内容",
  "statement": "判断陈述内容",
  "correct_answer": false
}
```

## 5. 阅读选词填空题

**返回数据格式：**
```json
{
  "exercise_id": "string",
  "question_type": "阅读·选词填空",
  "hsk_level": 1,
  "difficulty": 2,
  "sentence_with_blank": "我想__一杯茶。",
  "options": {
    "A": {"text": "点", "pinyin": "diǎn"},
    "B": {"text": "喝", "pinyin": "hē"},
    "C": {"text": "买", "pinyin": "mǎi"}
  },
  "correct_answer": "B"
}
```


## 6. 中译英

**返回数据格式：**
```json
{
  "exercise_id": "string",
  "question_type": "阅读·句子翻译",
  "hsk_level": 1,
  "difficulty": 2,
  "sentence_cn": "今天天气很好。",
  "sentence_en": "The weather is very good today."
}
```

## 7. 英译中

**返回数据格式：**
```json
{
  "exercise_id": "string",
  "question_type": "阅读·句子翻译",
  "hsk_level": 1,
  "difficulty": 2,
  "sentence_cn": "今天天气很好。",
  "sentence_en": "The weather is very good today."
}
```

