"""
FastAPI 라우팅과 세션 관리만 담당한다.
RAG/LLM 체인 로직은 rag_pipeline.py 참고."""

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rag_pipeline import QuizItem, chain_a, explainer, quiz_retriever


class AskRequest(BaseModel):
    question: str


class SelectRequest(BaseModel):
    session_id: str
    selected: list[str]


class QuizRequest(BaseModel):
    session_id: str


# --- FastAPI ---
app = FastAPI()
session_store: dict[str, dict] = {}  # TODO: 나중에 Redis 등으로 교체


@app.post("/ask")
def ask(req: AskRequest):
    prerequisites = chain_a.invoke({"question": req.question})
    session_id = str(uuid.uuid4())
    session_store[session_id] = {"question": req.question, "prerequisites": prerequisites}
    return {
        "session_id": session_id,
        "prerequisites": [p.model_dump() for p in prerequisites],
    }


@app.post("/select")
def select(req: SelectRequest):
    """선수개념 선택 -> llm 설명만 반환 (퀴즈는 아직 안 냄)"""
    ctx = session_store.get(req.session_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="session_id를 찾을 수 없습니다.")
    explanation = explainer.invoke({"selected": req.selected})
    ctx["selected"] = req.selected
    ctx["explanation"] = explanation
    return {"explanation": explanation}


@app.post("/quiz")
def quiz(req: QuizRequest):
    """[이해했어, 이제 퀴즈를 풀게] 버튼 -> 앞서 선택한 개념으로 퀴즈 출제"""
    ctx = session_store.get(req.session_id)
    if ctx is None or "selected" not in ctx:
        raise HTTPException(status_code=404, detail="먼저 /select로 개념을 선택하세요.")
    quiz_items: list[QuizItem] = quiz_retriever(ctx["selected"])
    ctx["quiz"] = quiz_items
    return {"quiz": [q.model_dump() for q in quiz_items]}


# 실행: rag/ 폴더에서 `uvicorn app:app --reload`
