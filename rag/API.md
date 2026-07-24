# API 엔드포인트

베이스 URL: `http://localhost:8000` (uvicorn 기본값)

3개 엔드포인트를 순서대로 호출한다. 각 호출은 이전 응답에서 받은 `session_id`를 실어 보내야 한다 (`/ask` 제외 — 여기서 `session_id`가 발급됨).

---

### `POST /ask`
질문에서 핵심개념을 뽑고, 선수개념 목록을 반환한다. (1, 2번 노드)

**Request**
```json
{ "question": "이차방정식의 근의 공식을 잘 모르겠어요" }
```

**Response**
```json
{
  "session_id": "5b1e...-uuid",
  "prerequisites": [
    { "name": "이차방정식 - 선수개념(mock)", "chapter": null, "depth": 1 },
    { "name": "근의 공식 - 선수개념(mock)", "chapter": null, "depth": 1 }
  ]
}
```

**Errors**: 없음 (항상 새 세션 발급)

---

### `POST /select`
사용자가 모른다고 선택한 선수개념을 LLM이 설명한다. (3번 노드)

**Request**
```json
{
  "session_id": "5b1e...-uuid",
  "selected": ["이차방정식 - 선수개념(mock)"]
}
```

**Response**
```json
{ "explanation": "이차방정식은 ... (LLM이 생성한 설명)" }
```

**Errors**: `404` — `session_id`를 찾을 수 없음 (`/ask`를 먼저 호출해야 함)

---

### `POST /quiz`
"이해했어, 이제 퀴즈를 풀게" 버튼 클릭 시 호출. `/select`에서 저장해둔 `selected`로 퀴즈를 낸다. (4번 노드)

**Request**
```json
{ "session_id": "5b1e...-uuid" }
```

**Response**
```json
{
  "quiz": [
    {
      "quiz_id": "mock-0",
      "question": "이차방정식 - 선수개념(mock) 관련 예시 문제(mock)",
      "answer": "mock answer",
      "concept": "이차방정식 - 선수개념(mock)"
    }
  ]
}
```

**Errors**: `404` — 세션이 없거나 `/select`를 먼저 호출하지 않음

---

## 호출 순서 요약

```
POST /ask     → session_id 발급
POST /select  → session_id 필요
POST /quiz    → session_id 필요 (select 선행)
```

## 한계

- `session_store`가 인메모리 dict라서 서버를 재시작하면 모든 세션이 소실된다. (프로토타입 단계라 허용한다.)
- `/select`, `/quiz`의 로직 일부는 아직 mock이다. 추후 담당 개발자의 실제 구현으로 교체될 예정이다.
