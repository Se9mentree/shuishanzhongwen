from enum import Enum
from typing import Any, Dict, List, Literal, Union, Optional

from typing_extensions import Annotated
from pydantic import BaseModel, Field,ConfigDict


class ExerciseRequest(BaseModel):
    lessonId: str = Field(..., description="课程ID")
    duration: int = Field(..., gt=0, description="期望的练习总时长（秒）")
    exerciseTypes: List[str] = Field(..., description="期望练习的题型名称列表")

class McOptionImage(BaseModel): label: str; imageUrl: Optional[str]
class McOptionText(BaseModel): label: str; text: str; pinyin: str
class GapFillBlankItem(BaseModel):
    """定义多项填空题中单个空格的结构 (ABCD 模式)"""
    blankIndex: int
    options: Dict[str, Dict[str, str]]  
    correctAnswer: str
class MatchItemAudio(BaseModel): label: str; audioUrl: Optional[str]; listeningText: str
class MatchItemImage(BaseModel): label: str; imageUrl: Optional[str]
class MatchItemText(BaseModel): label: str; text: str; pinyin: str
class WordOrderItem(BaseModel):
    label: str
    text: str = Field(..., alias="word")
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
class SentenceOrderItem(BaseModel):
    label: str
    text: str  

class ListenImageTrueFalseContent(BaseModel): prompt: str; audioUrl: Optional[str]; listeningText: str; imageUrl: Optional[str]
class ReadImageTrueFalseContent(BaseModel): prompt: str; statement: str; imageUrl: Optional[str]
class ListenSentenceTfContent(BaseModel): prompt: str; audioUrl: Optional[str]; listeningText: str; statement: str
class ReadSentenceTfContent(BaseModel): prompt: str; passage: str; statement: str
class ListenImageMcContent(BaseModel): prompt: str; audioUrl: Optional[str]; listeningText: str; options: List[McOptionImage]
class ListenSentenceQaContent(BaseModel): prompt: str; audioUrl: Optional[str]; listeningText: str; question: str; options: List[McOptionText]
class ReadSentenceComprehensionChoiceContent(BaseModel): prompt: str; passage: str; question: str; options: List[McOptionText]
class ReadWordGapFillContent(BaseModel):
    """定义多项填空题的 'content' 结构 (ABCD 模式)"""
    prompt: str
    text: str  
    blanks: List[GapFillBlankItem]
class ListenImageMatchContent(BaseModel): prompt: str; leftItems: List[MatchItemAudio]; rightItems: List[MatchItemImage]
class ReadImageMatchContent(BaseModel): prompt: str; leftItems: List[MatchItemText]; rightItems: List[MatchItemImage]
class ReadDialogueMatchContent(BaseModel): prompt: str; leftItems: List[MatchItemText]; rightItems: List[MatchItemText]
class ReadWordOrderContent(BaseModel):
    prompt: str
    items: List[WordOrderItem] = Field(..., alias="words")
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
class ReadParagraphSubQuestionContent(BaseModel):
    prompt: str
    passage: str  
    highlightedWord: Optional[str] = None
    question: str 
    options: List[Dict[str, str]] = Field(..., description="选项列表，例如 [{'label':'A', 'text':'...'}]")

class ReadSentenceOrderContent(BaseModel):
    prompt: str
    items: List[SentenceOrderItem] = Field(..., alias="sentences") # 定义一个更语义化的别名
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

class TranslateWordOrderContent(BaseModel):
    prompt: str             
    originalSentence: str   
    items: List[WordOrderItem] = Field(..., alias="words")
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

class SpeakFollowContent(BaseModel):
    prompt: str            
    sentence: str           
    pinyin: str             
    sampleAudioUrl: str   
class CharacterImageItem(BaseModel):
    character: str         
    pinyin: Optional[str] 
    animationUrl: Optional[str] = None 


class CharacterImagesContent(BaseModel):
    prompt: str
    word: str 
    items: List[CharacterImageItem]

class StrokeOrderWritingContent(BaseModel):
    prompt: str                
    character: str             
    pinyin: Optional[str] = None  
    animationUrl: Optional[str] = None 
    definition:Optional[str]=None



class ListenImageTrueFalseExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_IMAGE_TRUE_FALSE"]; content: ListenImageTrueFalseContent; correctAnswer: bool
class ReadImageTrueFalseExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_IMAGE_TRUE_FALSE"]; content: ReadImageTrueFalseContent; correctAnswer: bool
class ListenSentenceTfExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_SENTENCE_TF"]; content: ListenSentenceTfContent; correctAnswer: bool
class ReadSentenceTfExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_SENTENCE_TF"]; content: ReadSentenceTfContent; correctAnswer: bool
class ListenImageMcExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_IMAGE_MC"]; content: ListenImageMcContent; correctAnswer: str
class ListenSentenceQaExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_SENTENCE_QA"]; content: ListenSentenceQaContent; correctAnswer: str
class ReadSentenceComprehensionChoiceExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_SENTENCE_COMPREHENSION_CHOICE"]; content: ReadSentenceComprehensionChoiceContent; correctAnswer: str
class ReadWordGapFillExercise(BaseModel):
    """阅读·选词填空（多空版·ABCD）- 响应体"""
    exerciseId: str
    exerciseType: Literal["READ_WORD_GAP_FILL"]
    content: ReadWordGapFillContent  
    correctAnswer: Dict[str, str]       
class ListenImageMatchExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_IMAGE_MATCH"]; content: ListenImageMatchContent; correctAnswer: Dict[str, str]
class ReadImageMatchExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_IMAGE_MATCH"]; content: ReadImageMatchContent; correctAnswer: Dict[str, str]
class ReadDialogueMatchExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_DIALOGUE_MATCH"]; content: ReadDialogueMatchContent; correctAnswer: Dict[str, str]
class ReadWordOrderExercise(BaseModel):
    exerciseId: str
    exerciseType: Literal["READ_WORD_ORDER"]
    content: ReadWordOrderContent
    correctAnswer: List[str]

class RpSubQuestion(BaseModel):
    subExerciseId:str=Field(...,description="子题ID")
class ReadParagraphSubQuestionExercise(BaseModel):
    exerciseId: str 
    exerciseType: Literal["READ_PARAGRAPH_COMPREHENSION"]
    content: ReadParagraphSubQuestionContent
    correctAnswer: str = Field(..., description="正确答案的标签, 例如 'A'")
class ListenDialogueQaExercise(BaseModel):
    exerciseId: str
    exerciseType: Literal["LISTEN_DIALOGUE_QA"]
    content: ListenSentenceQaContent  
    correctAnswer: str

class ListenParagraphQaExercise(BaseModel):
    exerciseId: str
    exerciseType: Literal["LISTEN_PARAGRAPH_QA"]
    content: ListenSentenceQaContent  # 复用完全相同的 content 结构
    correctAnswer: str

class ReadSentenceOrderExercise(BaseModel):
    exerciseId: str
    exerciseType: Literal["READ_SENTENCE_ORDER"]
    content: ReadSentenceOrderContent
    correctAnswer: List[str]



class TranslateWordOrderExercise(BaseModel):
    exerciseId: str
    exerciseType: Literal["TRANSLATE_WORD_ORDER"]
    content: TranslateWordOrderContent
    correctAnswer: List[str]

class SpeakFollowExercise(BaseModel):
    exerciseId: str
    exerciseType: Literal["SPEAK_FOLLOW"]
    content: SpeakFollowContent

class StrokeOrderWritingExercise(BaseModel):
    exerciseId: str
    exerciseType: Literal["STROKE_ORDER_WRITING"] 
    content: StrokeOrderWritingContent

AnyExercise = Union[
    ListenImageTrueFalseExercise,
    ReadImageTrueFalseExercise,
    ListenSentenceTfExercise,
    ReadSentenceTfExercise,
    ListenImageMcExercise,
    ListenSentenceQaExercise,
    ReadSentenceComprehensionChoiceExercise,
    ReadWordGapFillExercise,
    ListenImageMatchExercise,
    ReadImageMatchExercise,
    ReadDialogueMatchExercise,
    ReadWordOrderExercise,
    ReadParagraphSubQuestionExercise,
    ListenDialogueQaExercise,
    ListenParagraphQaExercise ,
    ReadSentenceOrderExercise,
    TranslateWordOrderExercise,
    SpeakFollowExercise,
    StrokeOrderWritingExercise
]

class ExerciseResponse(BaseModel):
    phaseId: str
    topicId: str
    duration: int
    count: int
    sessionId: str
    exercises: List[
        Annotated[AnyExercise, Field(discriminator='exerciseType')]
    ]

class PracticeSkill(str, Enum):
    listen = "听"
    speak = "说"
    reading = "读"
    writing = "写"
    translation = "译"

class PracticeDimension(str, Enum):
    listen = "listen"
    speak = "speak"
    reading = "reading"
    writing = "writing"
    translation = "translation"

class PracticeResponse(BaseModel):
    skills: List[PracticeSkill]
    dimensions: List[PracticeDimension]
    count: int
    exerciseTypes: List[str]
    exercises: List[Annotated[AnyExercise, Field(discriminator='exerciseType')]]


class WordDetail(BaseModel):
    """
    定义单个词语的详细信息。
    """
    id: str = Field(description="词语的 UUID")
    characters: str = Field(description="词语汉字")
    pinyin: Optional[str] = Field(None, description="拼音")
    translation: Optional[str] = Field(None, description="翻译")
    hsk_level: Optional[int] = Field(None, description="HSK 等级")
    audio_url: Optional[str] = Field(None, description="词语发音的绝对 URL")
    
    # 允许从 SQLAlchemy 模型属性自动映射
    model_config = ConfigDict(from_attributes=True) 

class LessonWordListResponse(BaseModel):
    """
    定义 /lesson/words/{lesson_id} 端点的完整响应体。
    """
    lesson_id: str = Field(description="课程 ID")
    count: int = Field(description="返回的词语总数")
    words: List[WordDetail] = Field(description="词语详细信息列表")
