"""
Streamlit 프론트엔드. app.py(FastAPI)의 /ask, /select, /quiz 엔드포인트를
순서대로 호출해 화면을 그리는 역할만 담당한다. RAG/LLM 로직은 rag_pipeline.py 참고.
"""

import requests
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

API_URL = "http://localhost:8000"

st.title("Trace - 수학 개념 역추적 학습")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.prerequisites = []
    st.session_state.explanation = None
    st.session_state.quiz = None
    st.session_state.selected_names = set()
    st.session_state.last_clicked_id = None

question = st.text_input("무엇이 궁금한가요?")

if st.button("질문하기") and question:
    res = requests.post(f"{API_URL}/ask", json={"question": question})
    res.raise_for_status()
    data = res.json()
    st.session_state.session_id = data["session_id"]
    st.session_state.prerequisites = data["prerequisites"]
    st.session_state.explanation = None
    st.session_state.quiz = None
    st.session_state.selected_names = set()
    st.session_state.last_clicked_id = None

if st.session_state.prerequisites:
    st.subheader("모르는 선수개념을 선택하세요 (노드를 클릭해서 선택/해제)")

    nodes = [Node(id="__question__", label=question or "질문", size=25, color="#4CAF50", shape="dot")]
    edges = []
    for p in st.session_state.prerequisites:
        is_selected = p["name"] in st.session_state.selected_names
        nodes.append(
            Node(
                id=p["name"],
                label=p["name"],
                size=20,
                color="#FF6B6B" if is_selected else "#97C2FC",
            )
        )
        edges.append(Edge(source="__question__", target=p["name"]))

    config = Config(width=750, height=450, directed=True, physics=True, hierarchical=False)
    clicked_id = agraph(nodes=nodes, edges=edges, config=config)

    # agraph는 새로 클릭이 없어도 리런될 때마다 마지막 클릭 id를 다시 반환하므로,
    # 직전에 이미 처리한 클릭이면 무시해서 무한 rerun 루프(=버튼이 안 보이는 현상)를 막는다.
    if clicked_id and clicked_id != "__question__" and clicked_id != st.session_state.get("last_clicked_id"):
        st.session_state.last_clicked_id = clicked_id
        if clicked_id in st.session_state.selected_names:
            st.session_state.selected_names.discard(clicked_id)
        else:
            st.session_state.selected_names.add(clicked_id)
        st.rerun()

    selected = list(st.session_state.selected_names)
    st.write("선택된 개념:", ", ".join(selected) if selected else "없음")

    if st.button("선택 완료") and selected:
        res = requests.post(
            f"{API_URL}/select",
            json={"session_id": st.session_state.session_id, "selected": selected},
        )
        res.raise_for_status()
        st.session_state.explanation = res.json()["explanation"]
        st.session_state.quiz = None
    
if st.session_state.explanation:
    st.subheader("설명")
    st.write(st.session_state.explanation)

    if st.button("이해했어, 이제 퀴즈를 풀게"):
        res = requests.post(f"{API_URL}/quiz", json={"session_id": st.session_state.session_id})
        res.raise_for_status()
        st.session_state.quiz = res.json()["quiz"]

if st.session_state.quiz:
    st.subheader("퀴즈")
    for quiz in st.session_state.quiz:
        st.write(f"- {quiz['question']}")

# 실행 순서:
# 1) rag/ 폴더에서 `uvicorn app:app --reload`  (FastAPI 서버 먼저 실행)
# 2) `streamlit run streamlit_app.py`
