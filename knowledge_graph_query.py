"""Knowledge graph lookup helpers for prerequisite concepts.

Expected graph shape:
    (:Concept)-[:PREREQUISITE_OF]->(:Concept)

Example:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    result = get_prerequisites({"concepts": ["quadratic function"]}, driver)
    # {"prerequisites": ["..."]}
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from typing import Any

from pydantic import BaseModel


class Prerequisite(BaseModel):
    name: str
    chapter: str | None = None
    depth: int = 1


class QuizItem(BaseModel):
    quiz_id: str
    question: str
    answer: str
    concept: str


class GradeResult(BaseModel):
    quiz_id: str
    is_correct: bool
    feedback: str


class TraceState(BaseModel):
    question: str
    concepts: list[str] = []
    prerequisites: list[Prerequisite] = []
    selected: list[str] = []
    explanation: str = ""
    quiz: list[QuizItem] = []
    user_answers: dict[str, str] = {}
    grade_results: list[GradeResult] = []


PREREQUISITES_QUERY = """
UNWIND $concepts AS raw_name
WITH raw_name,
     toLower(replace(replace(trim(raw_name), ' ', ''), '\\t', '')) AS normalized_input
MATCH (target:Concept)
WITH raw_name, normalized_input, target,
     toLower(replace(replace(trim(target.name), ' ', ''), '\\t', '')) AS normalized_name
WHERE target.name = raw_name
   OR normalized_name = normalized_input
   OR normalized_name CONTAINS normalized_input
   OR normalized_input CONTAINS normalized_name
WITH raw_name, target,
     CASE
       WHEN target.name = raw_name THEN 0
       WHEN normalized_name = normalized_input THEN 1
       WHEN normalized_name STARTS WITH normalized_input THEN 2
       ELSE 3
     END AS match_rank
ORDER BY match_rank, size(target.name), target.id
WITH raw_name, collect({node: target, rank: match_rank})[..$target_limit] AS matches
UNWIND matches AS matched
WITH raw_name, matched.node AS target, matched.rank AS match_rank
MATCH (prerequisite:Concept)-[:PREREQUISITE_OF]->(target)
OPTIONAL MATCH (prerequisite)-[:BELONGS_TO_CHAPTER]->(chapter:Chapter)
RETURN DISTINCT
       raw_name AS input,
       target.id AS matched_concept_id,
       target.name AS matched_concept_name,
       match_rank AS match_rank,
       prerequisite.id AS prerequisite_id,
       prerequisite.name AS prerequisite_name,
       prerequisite.semester AS prerequisite_semester,
       chapter.name AS prerequisite_chapter
ORDER BY match_rank, matched_concept_id, prerequisite_name
"""


def get_prerequisites(
    payload: Mapping[str, Any],
    graph: Any,
    *,
    database: str | None = None,
    target_limit: int = 1,
    include_details: bool = False,
) -> dict[str, list[Any]]:
    """Return prerequisite concepts for concept names in ``payload``.

    Args:
        payload: A mapping shaped like ``{"concepts": ["quadratic function"]}``.
        graph: A Neo4j ``Driver`` or ``Session``.
        database: Optional Neo4j database name.
        target_limit: Number of matched concept nodes to use per input name.
            Keep the default ``1`` to avoid broad matches such as every concept
            whose name contains the input concept.
        include_details: If true, return dictionaries with ids and matched target
            concept metadata. Otherwise return Prerequisite-shaped dictionaries.

    Returns:
        ``{"prerequisites": [...]}``
    """

    concepts = _validate_concepts(payload)
    records = _run_prerequisite_query(
        graph,
        concepts,
        database=database,
        target_limit=target_limit,
    )

    if include_details:
        prerequisites: list[Any] = []
        seen: set[tuple[int | None, str]] = set()
        for record in records:
            key = (record.get("prerequisite_id"), record["prerequisite_name"])
            if key in seen:
                continue
            seen.add(key)
            prerequisites.append(
                {
                    "id": record.get("prerequisite_id"),
                    "name": record["prerequisite_name"],
                    "chapter": record.get("prerequisite_chapter"),
                    "depth": 1,
                    "semester": record.get("prerequisite_semester"),
                    "matched_concept": {
                        "id": record.get("matched_concept_id"),
                        "name": record.get("matched_concept_name"),
                        "input": record.get("input"),
                    },
                }
            )
        return {"prerequisites": prerequisites}

    prerequisites: list[dict[str, Any]] = []
    seen_names: set[tuple[str, str | None]] = set()
    for record in records:
        name = record["prerequisite_name"]
        chapter = record.get("prerequisite_chapter")
        key = (name, chapter)
        if key in seen_names:
            continue
        seen_names.add(key)
        prerequisites.append(_dump_model(Prerequisite(name=name, chapter=chapter, depth=1)))

    return {"prerequisites": prerequisites}


def apply_prerequisites_to_state(
    state: TraceState,
    graph: Any,
    *,
    database: str | None = None,
    target_limit: int = 1,
) -> TraceState:
    """Fill TraceState.prerequisites from TraceState.concepts."""

    if not state.concepts:
        return _copy_state(state, prerequisites=[])

    result = get_prerequisites(
        {"concepts": state.concepts},
        graph,
        database=database,
        target_limit=target_limit,
    )
    prerequisites = [Prerequisite(**item) for item in result["prerequisites"]]
    return _copy_state(state, prerequisites=prerequisites)


def _validate_concepts(payload: Mapping[str, Any]) -> list[str]:
    concepts = payload.get("concepts")
    if not isinstance(concepts, Sequence) or isinstance(concepts, (str, bytes)):
        raise ValueError('payload must be shaped like {"concepts": ["concept name"]}')

    cleaned = [concept.strip() for concept in concepts if isinstance(concept, str) and concept.strip()]
    if not cleaned:
        raise ValueError("payload.concepts must contain at least one non-empty concept name")

    return cleaned


def _dump_model(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _copy_state(state: TraceState, **updates: Any) -> TraceState:
    if hasattr(state, "model_copy"):
        return state.model_copy(update=updates)
    return state.copy(update=updates)


def _run_prerequisite_query(
    graph: Any,
    concepts: list[str],
    *,
    database: str | None,
    target_limit: int,
) -> list[dict[str, Any]]:
    if target_limit < 1:
        raise ValueError("target_limit must be greater than 0")

    params = {"concepts": concepts, "target_limit": target_limit}

    if hasattr(graph, "session"):
        session_context = graph.session(database=database) if database else graph.session()
    else:
        session_context = nullcontext(graph)

    with session_context as session:
        result = session.run(PREREQUISITES_QUERY, params)
        return [dict(record) for record in result]
