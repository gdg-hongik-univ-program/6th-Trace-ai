# rag — RAG 파이프라인 & API

챗봇 한 턴의 흐름(질문 → 핵심개념 추출 → 선수개념 검색 → 설명 → 퀴즈)을 구현한 폴더. 상세 흐름은 [`FLOW.md`](FLOW.md), API 명세는 [`API.md`](API.md) 참고.

| 파일 | 역할 |
|---|---|
| `rag.ipynb` | **전체 과정을 셀 단위로 실행하며 눈으로 확인하는 노트북.** 각 노드(개념 추출 → 선수개념 검색 → 설명 → 퀴즈 검색)가 무슨 일을 하는지 셀 실행 결과로 바로 확인할 수 있다. 로직을 처음 파악할 때는 이 노트북부터 보는 걸 추천. |
| `rag_pipeline.py` | `rag.ipynb`의 로직을 서비스용으로 옮긴 모듈. Pydantic 스키마, 벡터DB 연결, LLM 체인 조립을 담당한다 |
| `app.py` | `rag_pipeline.py`를 얹은 FastAPI 서버. 라우팅(`/ask`, `/select`, `/quiz`)과 세션 관리를 담당한다.|
| `streamlit_app.py` | `app.py`의 API를 호출하는 간단한 Streamlit 프론트엔드. |
| `FLOW.md` | 챗봇 4단계 흐름, 세션 상태 설계, mock 처리된 부분(지식그래프 검색) 설명. |
| `API.md` | `/ask`, `/select`, `/quiz` 3개 엔드포인트의 요청/응답 스키마와 에러 케이스. |

## 실행

```bash
# rag/ 폴더에서
uvicorn app:app --reload        # API 서버
streamlit run streamlit_app.py  # 새 터미널에서 프론트엔드
```

API 서버를 돌리려면 프로젝트 루트에 `.env` 파일로 `GOOGLE_API_KEY`가 설정돼 있어야 한다 (Gemini 사용, `rag_pipeline.py`에서 로드).
