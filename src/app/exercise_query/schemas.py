from typing import Any, Dict, List, Literal, Union, Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field,ConfigDict


class ExerciseRequest(BaseModel):
    lessonId: str = Field(..., description="课程ID")
    duration: int = Field(..., gt=0, description="期望的练习总时长（秒）")
    exerciseTypes: List[str] = Field(..., description="期望练习的题型名称列表")

class McOptionImage(BaseModel): label: str; imageUrl: Optional[str]
class McOptionText(BaseModel): label: str; text: str; pinyin: str
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
class ReadWordGapFillContent(BaseModel): prompt: str; question: str; options: List[McOptionText]
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



class ListenImageTrueFalseExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_IMAGE_TRUE_FALSE"]; content: ListenImageTrueFalseContent; correctAnswer: bool
class ReadImageTrueFalseExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_IMAGE_TRUE_FALSE"]; content: ReadImageTrueFalseContent; correctAnswer: bool
class ListenSentenceTfExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_SENTENCE_TF"]; content: ListenSentenceTfContent; correctAnswer: bool
class ReadSentenceTfExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_SENTENCE_TF"]; content: ReadSentenceTfContent; correctAnswer: bool
class ListenImageMcExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_IMAGE_MC"]; content: ListenImageMcContent; correctAnswer: str
class ListenSentenceQaExercise(BaseModel): exerciseId: str; exerciseType: Literal["LISTEN_SENTENCE_QA"]; content: ListenSentenceQaContent; correctAnswer: str
class ReadSentenceComprehensionChoiceExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_SENTENCE_COMPREHENSION_CHOICE"]; content: ReadSentenceComprehensionChoiceContent; correctAnswer: str
class ReadWordGapFillExercise(BaseModel): exerciseId: str; exerciseType: Literal["READ_WORD_GAP_FILL"]; content: ReadWordGapFillContent; correctAnswer: str
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
    ReadSentenceOrderExercise
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
