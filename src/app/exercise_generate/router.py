from fastapi import APIRouter, HTTPException
from app.exercise_generate.schema import (GenerateReq,ListenImageTfResp,MCReq,MCResp,MatchReq,MatchResp,ListenSentenceQAReq,ListenSentenceQAResp,ListenSentenceTfReq,ListenSentenceTfResp,
                                          ReadImageTfReq,ReadImageTfResp,ReadImageMatchReq,ReadImageMatchResp,ReadingDialogMatchReq,ReadingDialogMatchResp,ReadingGapFillReq,ReadingGapFillResp,
                                          SentenceTransReq,SentenceTransResp,ReadSentenceCompChoReq,ReadSentenceCompChoResp,ReadSentenceTfReq,ReadSentenceTfResp,ReadParagraphComprReq,ReadParagraphComprResp,
                                          WordOrderReq,WordOrderResp,ListenDialogueQAResp,ListenParagraphQAResp,ListenParagraphQAReq,ListenDialogueQAReq,SentenceOrderReq,SentenceOrderResp,TranslateWordOrderResp,
                                          SpeakAlongReq,SpeakAlongResp
                                          )

from app.exercise_generate.service import (create_listen_image_match_exercise,create_listen_image_mc_exercise,create_listen_image_tf_exercise,create_listen_sentence_qa_exercise,create_listen_sentence_tf_exercise,
                                           create_read_image_match_exercise,create_read_image_tf_exercise,create_read_paragraph_comprehension_exercise,create_read_sentence_comprehension_choice_exercise,
                                           create_read_sentence_tf_exercise,create_reading_dialog_matching,create_reading_gap_fill_exercise,create_sentence_translation_exercise,create_word_order_exercise,
                                           create_listen_dialogue_qa_exercise,create_listen_paragraph_qa_exercise,create_sentence_order_exercise,create_translate_word_order_exercise,create_speak_along_exercise)
from app.utils.util import _db

router=APIRouter()
@router.post("/api/generate-v2/listen-image-tf", response_model=ListenImageTfResp,tags=["Exercise Generation"])
async def generate_listen_image_tf_v2(req: GenerateReq):
    """
    生成一个“听录音,看图判断”的题目。
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        result = await create_listen_image_tf_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/listen-image-choice", response_model=MCResp,tags=["Exercise Generation"])
async def generate_listen_image_mc(req: MCReq):
    """
    生成【听录音·看图选择（单选）】并落库
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_listen_image_mc_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'听录音看图选择'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/listen-image-match", response_model=MatchResp,tags=["Exercise Generation"])
async def generate_listen_image_match(req: MatchReq):
    """
    生成听录音，看图配对题目
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_listen_image_match_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'听录音看图选择'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/listen-sentence-QA", response_model=ListenSentenceQAResp,tags=["Exercise Generation"])
async def generate_listen_sentence_qa(req: ListenSentenceQAReq):
    """
    生成听录音，句子问答(选择)
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_listen_sentence_qa_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'听录音句子问答（选择）'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/listen-sentence-TF", response_model=ListenSentenceTfResp,tags=["Exercise Generation"])
async def generate_listen_sentence_tf(req: ListenSentenceTfReq):
    """
    生成听录音，句子判断
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_listen_sentence_tf_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'听录音句子判断'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/read-image-TF", response_model=ReadImageTfResp,tags=["Exercise Generation"])
async def generate_read_picture_tf(req: ReadImageTfReq):
    """
    生成阅读，看图判断
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_read_image_tf_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'阅读看图判断'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/read-image-match", response_model=ReadImageMatchResp,tags=["Exercise Generation"])
async def generate_read_picture_match(req: ReadImageMatchReq):
    """
    生成阅读，看图配对题目
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_read_image_match_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'阅读看图配对'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/read-dialog-match", response_model=ReadingDialogMatchResp,tags=["Exercise Generation"])
async def generate_read_dialog_match(req: ReadingDialogMatchReq):
    """
    生成阅读，对话配对题目
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_reading_dialog_matching(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'阅读对话配对'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/read-gap-fill", response_model=ReadingGapFillResp,tags=["Exercise Generation"])
async def generate_read_gap_fill(req: ReadingGapFillReq):
    """
    生成选词填空题目
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_reading_gap_fill_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'选词填空'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/sentence-translate", response_model=SentenceTransResp,tags=["Exercise Generation"])
async def generate_sentence_translation(req: SentenceTransReq):
    """
    生成句子翻译题目
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_sentence_translation_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'句子翻译'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/read-sentence-comprehension-choice", response_model=ReadSentenceCompChoResp,tags=["Exercise Generation"])
async def generate_read_sentence_comprehension_choice(req: ReadSentenceCompChoReq):
    """
    生成阅读，句子理解选择
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_read_sentence_comprehension_choice_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'阅读句子理解选择'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/read-sentence-comprehension-tf", response_model=ReadSentenceTfResp,tags=["Exercise Generation"])
async def generate_read_sentence_comprehension_tf(req: ReadSentenceTfReq):
    """
    生成阅读，句子理解选择
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_read_sentence_tf_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'阅读句子理解选择'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/read-paragraph-comprehension", response_model=ReadParagraphComprResp,tags=["Exercise Generation"])
async def generate_read_paragraph_comprehension(req:ReadParagraphComprReq):
    """
    生成段落理解选择
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        

        result = await create_read_paragraph_comprehension_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'段落理解选择'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/word_order", response_model=WordOrderResp,tags=["Exercise Generation"])
async def generate_word_order(req:WordOrderReq):
    """
    生成连词成句
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        

        result = await create_word_order_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'连词成句'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()


@router.post("/api/generate-v2/listen-dialogue-QA", response_model=ListenDialogueQAResp,tags=["Exercise Generation"])
async def generate_dialogue_sentence_qa(req: ListenDialogueQAReq):
    """
    生成听录音，对话问答(选择)
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_listen_dialogue_qa_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'听录音对话问答（选择）'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()


@router.post("/api/generate-v2/listen-paragraph-QA", response_model=ListenParagraphQAResp,tags=["Exercise Generation"])
async def generate_paragraph_sentence_qa(req: ListenParagraphQAReq):
    """
    生成听录音，段落问答(选择)
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        # 调用核心业务逻辑函数
        result = await create_listen_paragraph_qa_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'听录音段落问答（选择）'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@router.post("/api/generate-v2/sentence_order", response_model=SentenceOrderResp,tags=["Exercise Generation"])
async def generate_sentence_order(req:SentenceOrderReq):
    """
    生成连句成段
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        

        result = await create_sentence_order_exercise(cur, req)
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'连句成段'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()


@router.post("/api/generate-v2/translate-word-order", response_model=TranslateWordOrderResp, tags=["Exercise Generation"])
async def generate_translate_word_order(req: WordOrderReq):

    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        result = await create_translate_word_order_exercise(cur, req) 
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'翻译连词成句'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()


@router.post("/api/generate-v2/read-along-sentence", response_model=SpeakAlongResp, tags=["Exercise Generation"])
async def generate_read_along_sentence(req: SpeakAlongReq):
    """
    生成 跟读句子 题目 (speak-Along)
    """
    conn = None
    try:
        conn = _db()
        cur = conn.cursor()
        
        result = await create_speak_along_exercise(cur, req) 
        
        conn.commit()
        return result

    except (Exception, ValueError) as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成'跟读句子'题目时发生错误: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()



































































































































