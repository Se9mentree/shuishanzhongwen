from pydantic import BaseModel,Field,validator
from typing import Optional,Dict,Any,List
class GenerateReq(BaseModel):
    keyword: str
    hskLevel: int = Field(..., ge=1, le=6)
    isCorrect: bool = True
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)
    seed: Optional[int] = None

class ListenImageTfResp(BaseModel):
    exercise_id: str
    hsk_level: int
    difficulty: int
    metadata: Dict[str, Any]
    assets: Dict[str, str]

class MCReq(BaseModel):
    correctKeyword: str
    hskLevel: int = Field(..., ge=1, le=6)
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)

class MCResp(BaseModel):
    exercise_id: str
    question_type: str
    hsk_level: int
    listening_text: str
    audio_url: str # 这里应该是 asset_id
    options: Dict[str, Dict[str, Any]]
    correct_answer: str

class MatchReq(BaseModel):
    keywords: List[str]               # 至少 2~6 个关键词（每个关键词生成一条音频 + 一张图片）
    hskLevel: int = Field(..., ge=1, le=6)
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)
    seed: Optional[int] = None        # 选填：用于固定打乱顺序的随机种子（可复现）

class MatchResp(BaseModel):
    exercise_id: str
    question_type: str = "听录音·看图配对"
    hsk_level: int
    difficulty: int
    audios: Dict[str, Dict[str, Any]]
    images: Dict[str, Dict[str, Any]]
    answer_map: Dict[str, str]
class MatchReq(BaseModel):
    """听力·看图配对 —— 请求体"""
    keywords: List[str]               # 至少 2~6 个关键词（每个关键词生成一条音频 + 一张图片）
    hskLevel: int = Field(..., ge=1, le=6)
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)
    seed: Optional[int] = None        # 选填：用于固定打乱顺序的随机种子（可复现）

class MatchResp(BaseModel):
    """
    听力·看图配对 —— 响应体（与 MCResp 风格一致：字段扁平、直出 URL、选项用 dict 按 label 索引）
    - audios: 以 A/B/C... 为 key，value 含 子题ID/音频URL/（可选）文本
    - images: 以 A/B/C... 为 key，value 含 图片URL
    - answer_map: 标准答案映射（audio_label -> image_label）
      （若学生端不应暴露答案，可在路由层移除该字段）
    """
    exercise_id: str
    question_type: str = "听录音·看图配对"
    hsk_level: int
    difficulty: int
    audios: Dict[str, Dict[str, Any]]
    images: Dict[str, Dict[str, Any]]
    answer_map: Dict[str, str]


class ListenSentenceQAReq(BaseModel):
    keyword: str                         # 关联系统词（用于 words 外键）
    hskLevel: int = Field(..., ge=1, le=6)
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)
    optionCount: int = Field(3, ge=3, le=6)   # 选项数量，默认3
    seed: Optional[int] = None                # 可选：控制选项打乱的随机种子


class ListenDialogueQAResp(BaseModel):
    exercise_id: str
    question_type: str = "听录音·对话问答（单选）"
    hsk_level: int
    listening_text: str
    question: str
    question_pinyin:str
    audio_url: str
    options: Dict[str, Dict[str, Any]]        # {"A":{"text":"..."}, "B":{...}}
    correct_answer: str                        # "A" / "B" / ...

class ListenParagraphQAReq(BaseModel):
    keyword: str                         # 关联系统词（用于 words 外键）
    hskLevel: int = Field(..., ge=1, le=6)
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)
    optionCount: int = Field(3, ge=3, le=6)   # 选项数量，默认3
    seed: Optional[int] = None                # 可选：控制选项打乱的随机种子


class ListenParagraphQAResp(BaseModel):
    exercise_id: str
    question_type: str = "听录音·段落问答（单选）"
    hsk_level: int
    listening_text: str
    question: str
    question_pinyin:str
    audio_url: str
    options: Dict[str, Dict[str, Any]]        # {"A":{"text":"..."}, "B":{...}}
    correct_answer: str                        # "A" / "B" / ...


class ListenDialogueQAReq(BaseModel):
    keyword: str                         # 关联系统词（用于 words 外键）
    hskLevel: int = Field(..., ge=1, le=6)
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)
    optionCount: int = Field(3, ge=3, le=6)   # 选项数量，默认3
    seed: Optional[int] = None                # 可选：控制选项打乱的随机种子


class ListenSentenceQAResp(BaseModel):
    exercise_id: str
    question_type: str = "听录音·句子问答（单选）"
    hsk_level: int
    listening_text: str
    question: str
    question_pinyin:str
    audio_url: str
    options: Dict[str, Dict[str, Any]]        # {"A":{"text":"..."}, "B":{...}}
    correct_answer: str                        # "A" / "B" / ...


class ListenSentenceTfReq(BaseModel):
    keyword: str                         # 关联系统词（用于 words 外键）
    hskLevel: int = Field(..., ge=1, le=6)
    isCorrect: bool = True               # True: 陳述与音频一致；False: 作为干扰项           # 复用 TEXT_TYPE_INSTRUCTIONS
    lang: str = "zh-CN"
    difficulty: int = Field(2, ge=1, le=5)
    seed: Optional[int] = None           # 可选：若后续需要复现随机性

class ListenSentenceTfResp(BaseModel):
    exercise_id: str
    question_type: str = "听录音·句子判断"
    hsk_level: int
    difficulty: int
    listening_text: str                  # 音频对应文本（如需隐藏，路由层去掉即可）
    statement: str
    statement_pinyin:str                       # 用于判断的文本陈述
    audio_url: str                       # 题干音频 URL
    correct_answer: bool                 # 标准答案（True/False）

class ReadImageTfReq(BaseModel):
    keyword: str
    hskLevel: int = Field(..., ge=1, le=2)
    isCorrect: bool = True           
    difficulty: int = Field(2, ge=1, le=5)

class ReadImageTfResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·图片·判断"
    hsk_level: int
    difficulty: int
    word: str
    pinyin: str
    image_url: str
    correct_answer: bool


class ReadImageMatchReq(BaseModel):
    keywords: List[str]                 # 3–5 个词语
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    seed: Optional[int] = None          # 控制乱序的随机种子（可复现）

    @validator("keywords")
    def _check_len(cls, v):
        if not v or not (3 <= len(v) <= 5):
            raise ValueError("阅读·看图配对必须提供 3–5 个关键词")
        if any((not isinstance(w, str) or not w.strip()) for w in v):
            raise ValueError("关键词不能为空字符串")
        return [w.strip() for w in v]

class ReadImageMatchResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·看图配对"
    hsk_level: int
    difficulty: int
    texts: Dict[str, Dict[str, Any]]
    images: Dict[str, Dict[str, Any]]

    answer_map: Dict[str, str]


class ReadingDialogMatchReq(BaseModel):
    keyword: str
    numPairs: int = Field(..., ge=3, le=6)      # 3~6 组
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    lang: str = "zh-CN"
    seed: Optional[int] = None                  # 固定乱序（可复现）

    @validator("keyword")
    def _kw_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("keyword 不能为空")
        return v.strip()

class ReadingDialogMatchResp(BaseModel):
    question_type: str = "阅读·对话配对"
    hsk_level: int
    difficulty: int
    shuffled_questions: Dict[str, Dict[str, str]]   # {"A":{"text":"...","pinyin":"..."}}
    shuffled_answers: Dict[str, Dict[str, str]]     # {"B":{"text":"...","pinyin":"..."}}
    answers: Dict[str, str]                         # {"A":"C", ...}  左label -> 右label
    exercise_id: str

class ReadingGapFillReq(BaseModel):
    keyword: str                         # 主题词/限定词
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    optionCount: int = 3  
    lang: str = "zh-CN"
    seed: Optional[int] = None


class ReadingGapFillResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·选词填空"
    hsk_level: int
    difficulty: int
    sentence_with_blank: str                 # 例：我 想 __ 一杯茶。
    options: Dict[str, Dict[str, str]]       # {"A":{"text":"点","pinyin":"diǎn"}, ...}
    correct_answer: str                      # 例："B"

class SentenceTransReq(BaseModel):
    keyword: str                          # 关联词（强制要求在 words 表存在）
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    seed: Optional[int] = None            # 预留，可做随机性控制（此题型用不到也可记录）

class SentenceTransResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·句子翻译"
    hsk_level: int
    difficulty: int
    sentence_cn: str
    sentence_en: str

class ReadSentenceCompChoReq(BaseModel):
    keyword: str
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    seed: Optional[int] = None          

class ReadSentenceCompChoResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·句子理解"
    hsk_level: int
    difficulty: int
    passage: str
    question: str
    options: Dict[str, Dict[str, str]]  # {"A":{"text":"..."}, "B":{"text":"..."}, "C":{"text":"..."}}
    correct_answer: str                  # "A"/"B"/"C"

class ReadSentenceTfReq(BaseModel):
    keyword: str
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    isCorrect: Optional[bool] = None
    seed: Optional[int] = None

class ReadSentenceTfResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·句子判断"
    hsk_level: int
    difficulty: int
    passage: str
    statement: str
    correct_answer: bool


class ReadParagraphComprReq(BaseModel):
    topic: str
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    textLength: int = Field(100, ge=50, le=400)   # 文章目标字数（±10%）
    numQuestions: int = Field(3, ge=1, le=8)      # 生成题目数量
    seed: Optional[int] = None                    # 控制整体和选项打乱

class RPQuestionItem(BaseModel):
    sub_exercise_id: str
    stem: str
    options: Dict[str, Dict[str, str]]            # {"A":{"text":"..."}, ...}
    correct_answer: str                           # "A"~"D"

class ReadParagraphComprResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·段落理解"
    hsk_level: int
    difficulty: int
    passage: str
    highlighted_word: Optional[str] = None        # 文章中被 /.../ 包裹的词（若存在）
    questions: List[RPQuestionItem]



class WordOrderReq(BaseModel):
    keyword: str
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    lang: str = "zh-CN"
    seed: Optional[int] = None
    minPieces: int = Field(3, ge=2, le=10)
    maxPieces: int = Field(7, ge=3, le=12)

class WordOrderResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·连词成句"
    hsk_level: int
    difficulty: int
    # 乱序展示：每个词片含 id / text / pinyin
    pieces: Dict[str, Dict[str, str]]           # {"A":{"id":"...","text":"...","pinyin":"..."}}
    # 正确顺序：按“标签”的顺序 or 直接返回按原顺序的 piece_id 列表（更稳）
    answer_order: List[str]                      # 例如 ["C","A","B","D"]
    answer_ids: List[str]                        # 例如 ["id3","id1","id2","id4"]
    sentence: str                                # 可在学生端隐藏



class SentenceOrderReq(BaseModel):
    keyword: str
    hskLevel: int = Field(..., ge=1, le=6)
    difficulty: int = Field(2, ge=1, le=5)
    lang: str = "zh-CN"
    seed: Optional[int] = None


class SentenceOrderResp(BaseModel):
    exercise_id: str
    question_type: str = "阅读·连词成句"
    hsk_level: int
    difficulty: int
    # 乱序展示：每个词片含 id / text / pinyin
    pieces: Dict[str, Dict[str, str]]           # {"A":{"id":"...","text":"...","pinyin":"..."}}
    # 正确顺序：按“标签”的顺序 or 直接返回按原顺序的 piece_id 列表（更稳）
    answer_order: List[str]                      # 例如 ["C","A","B","D"]
    answer_ids: List[str]                        # 例如 ["id3","id1","id2","id4"]
    sentence: str            