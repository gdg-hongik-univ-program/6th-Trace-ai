// Trace 수학 지식체계 - Neo4j 데이터 적재
//
// 사전 준비:
//   1. schema.cypher 먼저 실행
//   2. chapters.csv, concepts.csv, achievements.csv, relations.csv 를
//      Neo4j DBMS의 import 폴더에 복사
//      (Neo4j Desktop 기준: <DBMS 경로>/import/, DBMS 카드 하단 "Open folder"에서 확인 가능)
//
// 원본 CSV 위치: data/8.수학지식체계_데이터셋/
// 모든 단계는 MERGE 기반이라 재실행해도 중복 생성되지 않는다 (idempotent).
// 아래 블록을 순서대로 하나씩 실행할 것.

// ── 1. Chapter 노드 (기대 결과: 646개) ──────────────────────────────
LOAD CSV WITH HEADERS FROM 'file:///chapters.csv' AS row
MERGE (c:Chapter {id: toInteger(row.id)})
SET c.name = row.name;

// ── 2. Achievement 노드 (기대 결과: 378개) ──────────────────────────
LOAD CSV WITH HEADERS FROM 'file:///achievements.csv' AS row
MERGE (a:Achievement {id: toInteger(row.id)})
SET a.name = row.name;

// ── 3. Concept 노드 (기대 결과: 1,633개) ────────────────────────────
LOAD CSV WITH HEADERS FROM 'file:///concepts.csv' AS row
MERGE (c:Concept {id: toInteger(row.id)})
SET c.name = row.name,
    c.semester = row.semester,
    c.description = row.description;

// ── 4. Concept -> Chapter (기대 결과: 1,631개, chapter_id 없는 concept 2개 제외) ──
LOAD CSV WITH HEADERS FROM 'file:///concepts.csv' AS row
WITH row WHERE row.chapter_id IS NOT NULL AND row.chapter_id <> ""
MATCH (c:Concept {id: toInteger(row.id)})
MATCH (ch:Chapter {id: toInteger(row.chapter_id)})
MERGE (c)-[:BELONGS_TO_CHAPTER]->(ch);

// ── 5. Concept -> Achievement (기대 결과: 1,633개) ──────────────────
LOAD CSV WITH HEADERS FROM 'file:///concepts.csv' AS row
WITH row WHERE row.achievement_id IS NOT NULL AND row.achievement_id <> ""
MATCH (c:Concept {id: toInteger(row.id)})
MATCH (a:Achievement {id: toInteger(row.achievement_id)})
MERGE (c)-[:HAS_ACHIEVEMENT]->(a);

// ── 6. 선수개념 관계 (기대 결과: 3,446개) ───────────────────────────
// relations.csv 컬럼 의미: from_concept_id = 기준개념, to_concept_id = 선행개념(선수개념)
// PREREQUISITE_OF 방향 = "학습 순서" 방향이므로 (선수개념) -> (기준개념) 으로 만든다.
LOAD CSV WITH HEADERS FROM 'file:///relations.csv' AS row
MATCH (base:Concept {id: toInteger(row.from_concept_id)})
MATCH (prereq:Concept {id: toInteger(row.to_concept_id)})
MERGE (prereq)-[:PREREQUISITE_OF]->(base);

// ── 검증 ─────────────────────────────────────────────────────────
// MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt;
// MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt;
//
// 기대값:
//   Chapter 646 / Achievement 378 / Concept 1,633
//   BELONGS_TO_CHAPTER 1,631 / HAS_ACHIEVEMENT 1,633 / PREREQUISITE_OF 3,446
