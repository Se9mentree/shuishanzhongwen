import os
AVERAGE_DURATIONS_PER_TYPE = {
    "LISTEN_IMAGE_TRUE_FALSE": 20,
    "LISTEN_IMAGE_MC": 25,
    "LISTEN_IMAGE_MATCH": 90, # 配对题有多组，总时间长
    "LISTEN_SENTENCE_QA": 30,
    "LISTEN_SENTENCE_TF": 20,

    # 阅读题 (判断和简单选择较快，配对和篇章较慢)
    "READ_IMAGE_TRUE_FALSE": 15,
    "READ_IMAGE_MATCH": 60,
    "READ_DIALOGUE_MATCH": 75,
    "READ_WORD_GAP_FILL": 25,
    "READ_SENTENCE_TRANSLATION": 20,
    "READ_SENTENCE_COMPREHENSION_CHOICE": 45,
    "READ_SENTENCE_TF": 40,
    "READ_PARAGRAPH_COMPREHENSION": 180, # 段落理解最耗时
    "READ_WORD_ORDER": 30,
    
    "DEFAULT": 25
}

DATABASE_URL = os.getenv("DATABASE_URL")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/data/media")
MEDIA_PUBLIC_BASE = os.getenv("MEDIA_PUBLIC_BASE", "/media")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
APP_ID=os.getenv("APP_ID","")
HSK_LEVEL_DESCRIPTIONS = {
  'HSK1': '目标为HSK一级水平。这要求使用最基础的词汇（约150个）和句型，描述非常简单的日常活动，如问候、自我介绍、数字、时间等。句子结构应为简单主谓宾。',
  'HSK2': '目标为HSK二级水平。这要求能围绕熟悉的日常话题（如购物、问路、天气）进行简单直接的交流，使用约300个词汇。可以包含简单的修饰成分。',
  'HSK3': '目标为HSK三级水平。这要求能在生活、学习、工作等场景中进行基本沟通，使用约600个词汇。句子可以稍微复杂一些，包含简单的复句。',
  'HSK4': '目标为HSK四级水平。这要求能就较广泛领域的话题进行谈论，并能与母语者进行较为流利的交流，使用约1200个词汇。可以使用多种复句和一些固定搭配。',
  'HSK5': '目标为HSK五级水平。这要求能阅读报刊杂志，欣赏影视节目，并进行较为完整的演讲，使用约2500个词汇。语言表达需要地道、得体。',
  'HSK6': '目标为HSK六级水平。这要求能轻松地理解听读信息，并流利地用口头或书面形式表达自己的见解，使用5000个以上词汇。语言运用要灵活、准确，并具有一定的逻辑性和说服力。'
}

TEXT_TYPE_INSTRUCTIONS = {
  '一句话': '请生成一个单一、完整的句子。',
  '一段话': '请生成一个由3到5个句子组成的连贯段落，共同描述一个场景或事件。',
  '一段独白': '请以第一人称“我”的视角，生成一段内心独白或口头陈述，内容要连贯。',
  '一段对话': "请生成一段至少一轮（例如，A问B答）的简短对话。必须使用角色标识且以说结尾，例如 '小明说：' 和 '小红说：' 或 'A说：' 和 'B说：'。"
}


