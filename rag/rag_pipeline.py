"""
Pydantic 스키마, 벡터DB(Chroma) 연결, LLM 체인(개념 추출/설명/퀴즈 검색) 조립.
FastAPI와 무관한 RAG 로직만 담당한다.

각 셀의 실행 결과(출력)까지 보고 싶으면 rag.ipynb 를 참고.
"""

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field

load_dotenv()

if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY가 없습니다. .env 파일을 확인하세요")


# --- Pydantic 스키마 ---
class CoreConcept(BaseModel):
    """사용자 질문에서 핵심 개념 추출을 위한 pydantic 모델"""

    core_concepts: list[str] = Field(description="사용자의 질문에서 핵심이 되는 수학 개념들을 추출해라")


class Prerequisite(BaseModel):
    name: str
    chapter: str | None = None
    depth: int = 1


class QuizItem(BaseModel):
    quiz_id: str
    question: str
    answer: str
    concept: str


# --- 벡터 DB ---
# rag_pipeline.py는 rag/ 폴더에 있으므로, 프로젝트 루트는 한 단계 위 폴더다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "chromadb")

embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
chroma_client = chromadb.PersistentClient(path=DB_PATH)
vectorstore = Chroma(
    client=chroma_client,
    collection_name="problem_collection",
    embedding_function=embeddings,
)


# --- LLM & 체인 조립 ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
structured_answer = llm.with_structured_output(CoreConcept)

extract_prompt = ChatPromptTemplate.from_messages([
    ("system", " 수학 개념 추출하세요 ~  (지식 그래프 개념 노드를 프롬포트에 넣을 예정)  \n"),
    ("human", "질문:{question}\n\n 이 질문에서 핵심이 되는 수학 개념들을 추출해주세요. \n"),
])
extract_chain = extract_prompt | structured_answer


def mock_graph_query(core_concept: CoreConcept) -> list[Prerequisite]:
    """[MOCK] 가영님 담당: 지식그래프 검색 모듈. 진짜 구현으로 교체 예정."""
    return [
        Prerequisite(name=f"{concept} - 선수개념(mock)", chapter=None, depth=1)
        for concept in core_concept.core_concepts
    ]


chain_a = extract_chain | RunnableLambda(mock_graph_query)

explain_prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 수포자에게 수학 개념을 쉽고 친절하게 설명해주는 선생님이야. 예시를 들어 설명해줘."),
    ("human", "다음 개념들을 설명해줘: {selected}"),
])
explainer = explain_prompt | llm | StrOutputParser()


def quiz_retriever(selected: list[str]) -> list[QuizItem]:
    """벡터DB 퀴즈 검색 모듈. 개념별로 vectorstore.similarity_search(concept, k=5)로 문제 5개씩 가져온다."""
    quizzes = []
    for concept in selected:
        docs = vectorstore.similarity_search(concept, k=5)
        for i, doc in enumerate(docs):
            quizzes.append(
                QuizItem(
                    quiz_id=f"{concept}-{i}",
                    question=doc.page_content,
                    answer=doc.page_content,
                    concept=concept,
                )
            )
    return quizzes
