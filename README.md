# 6th-Trace-ai

수포자를 위한 튜터 챗봇 TRACE의 파이프라인.
질문에서 핵심 개념을 뽑고, 선수개념을 찾아 설명한 뒤, 이해도를 확인하는 퀴즈까지 이어주는 흐름을 구현한다.

## 프로젝트 구조

```
6th-Trace-ai/
├── rag/                 # RAG 파이프라인 + FastAPI 서버 + Streamlit 프론트 프로토타입
│   ├── rag.ipynb         # 전체 흐름을 셀 단위로 실행/확인하는 노트북
│   ├── rag_pipeline.py   # 벡터DB 연결 + LLM 체인(개념추출/설명/퀴즈검색) 조립
│   ├── app.py            # FastAPI 라우팅(/ask, /select, /quiz) + 세션 관리
│   ├── streamlit_app.py  # 프론트엔드 프로토타입
│   ├── FLOW.md           # 챗봇 4단계 흐름 및 세션 설계 문서
│   ├── API.md            # 엔드포인트별 요청/응답 명세
│   └── README.md         # rag/ 폴더 상세 설명
│
├── vectorDB/             # 벡터DB 구축 코드
│   ├── vectordb_v2.ipynb                          # 재구축 코드
│   ├── problem_data_chromadb_pipeline (1).ipynb   # 기존(v1) 구축 코드
│   └── README.md                                  
│
├── knowledge-graph/      # 선수개념 지식그래프 스키마 및 적재 (Neo4j Cypher)
│   ├── schema.cypher      # 그래프 스키마 정의
│   └── load.cypher        # 데이터 적재 쿼리
│
├── preprocessing/        # 원본 학습 데이터(JSON) 전처리 
│   ├── convert_to_csv.py  # JSON → CSV 변환 스크립트
│   └── eda.ipynb          
│
├── data/                 # 전처리한 CSV 데이터 + 벡터DB 저장소
│   ├── achievements.csv   # 성취기준 데이터
│   ├── chapters.csv       # 단원 데이터
│   ├── concepts.csv       # 개념 데이터
│   ├── relations.csv      # 개념 간 관계(선수개념 등) 데이터
│   └── chromadb/          # vectorDB/에서 구축한 Chroma 벡터DB 저장 경로 (rag_pipeline.py가 참조)
│
├── ai_sprint_week1_ocr.py  # 초기 OCR 실험 스크립트
├── requirements.txt         # Python 의존성 목록
└── trace/                   # Python 가상환경 (git 추적 제외)
```

## 환경 설정

```bash
pip install -r requirements.txt
```

주요 의존성 (`requirements.txt` 참고):

| 영역 | 패키지 |
|---|---|
| LLM / 체인 | `langchain`, `langchain-core`, `langchain-community`, `langchain-classic`, `langchain-google-genai` (Gemini) |
| 임베딩 | `langchain-huggingface`, `sentence-transformers` (`jhgan/ko-sroberta-multitask`) |
| 벡터DB | `chromadb`, `langchain-chroma` |
| API 서버 | `fastapi`, `uvicorn`, `httpx` |
| 프론트엔드 | `streamlit`, `streamlit-agraph`, `requests` |
| 설정/검증 | `python-dotenv`, `pydantic`, `pydantic-settings` |

`rag/` 아래 API 서버를 돌리려면 프로젝트 루트에 `.env` 파일로 `GOOGLE_API_KEY`를 설정해야 한다 (Gemini 사용).

## 더 알아보기

- RAG 파이프라인/API 상세: [`rag/README.md`](rag/README.md), [`rag/FLOW.md`](rag/FLOW.md), [`rag/API.md`](rag/API.md)
- 벡터DB 구축 배경(검색 품질 이슈, v1→v2): [`vectorDB/README.md`](vectorDB/README.md)
