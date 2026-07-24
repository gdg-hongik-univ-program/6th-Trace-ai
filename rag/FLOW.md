# 챗봇 흐름

사용자 질문 하나를 4단계로 처리한다. 중간에 사용자가 직접 고르는 지점(HITL)이 있어서, 웹 서비스에서는 그 지점을 기준으로 요청이 끊겼다가 다시 이어진다. 

```
1. 질문에서 핵심개념 추출        (extract_chain, LLM)
2. 핵심개념 → 지식그래프 검색     (mock_graph_query, [MOCK] 가영님 담당)
        → 선수개념 목록 반환, 여기서 요청 1 종료
   ─── 사용자가 모르는 선수개념을 선택 (프론트) ───
3. 선택한 선수개념을 LLM이 설명   (explainer, LLM)
        → 설명 반환, 여기서 요청 2 종료
   ─── 사용자가 "이해했어, 퀴즈 풀게" 클릭 ───
4. 선택한 개념으로 퀴즈 출제      (quiz_retriever, 벡터DB similarity_search)
        → 퀴즈 반환
```

## 세션 상태

요청 사이 상태는 `session_store: dict[session_id, dict]`(인메모리)로 이어붙인다. `/ask`에서 `session_id`를 발급하고, 이후 요청은 전부 `session_id`를 실어 보내 컨텍스트를 복원한다.

| 시점 | session_store[session_id]에 쌓이는 키 |
|---|---|
| `/ask` 이후 | `question`, `prerequisites` |
| `/select` 이후 | `selected`, `explanation` |
| `/quiz` 이후 | `quiz` |

서버 재시작하면 세션이 날아간다 — 지금은 프로토타입이라 허용, 나중에 Redis 등으로 교체 필요.

## mock으로 처리한 부분

- **2번 노드**(지식그래프 검색): 가영님 담당. `mock_graph_query`가 진짜 로직 없이 `"{개념} - 선수개념(mock)"` 형태의 더미 `Prerequisite`를 리턴.
- **4번 노드**(벡터DB 퀴즈 검색): `quiz_retriever`가 실제 Chroma `vectorstore.similarity_search`로 개념별 문제 5개씩 가져온다 (`rag/rag_pipeline.py`).

`mock_graph_query`도 입출력 스키마(`Prerequisite`)만 맞춰뒀기 때문에, 실제 구현으로 교체해도 앞뒤(`chain_a`) 코드는 안 건드려도 된다.

## 실행

```bash
# rag/ 폴더에서
uvicorn app:app --reload        # 1) API 서버
streamlit run streamlit_app.py  # 2) 새 터미널에서 프론트엔드
```

## 고도화 방향

- 단계가 늘어날수록 엔드포인트가 계속 늘어나는 구조라서 LangGraph의 interrupt + checkpointer로 옮기는 걸 고려 중. `extract_chain`/`explainer` 같은 체인 로직 자체는 그대로 노드 함수로 옮기면 됨.
