// Trace 수학 지식체계 - Neo4j 스키마 (제약조건)
//
// 실행 순서: schema.cypher → load.cypher
// 대상 DB: 빈 Neo4j database (기존 데이터가 있다면 먼저 MATCH (n) DETACH DELETE n; 으로 비울 것)

CREATE CONSTRAINT concept_id IF NOT EXISTS
FOR (c:Concept) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT chapter_id IF NOT EXISTS
FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE;

CREATE CONSTRAINT achievement_id IF NOT EXISTS
FOR (a:Achievement) REQUIRE a.id IS UNIQUE;
