import time

import streamlit as st

from interviewer import ask_question, evaluate_answer
from loader import load_github_repo, load_pasted_text, load_readme_file
from store import build_index

st.set_page_config(page_title="Project Interviewer", page_icon="🎤")
st.title("🎤 Mock Interview Bot")

TOPICS = [
    "tech stack and architecture",
    "database and storage",
    "machine learning model",
    "frontend and dashboard",
    "limitations and future work",
]

defaults = {"messages": [], "question": None, "context": None,
            "topic_idx": 0, "project_id": None}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_chat():
    st.session_state.messages = []
    st.session_state.question = None
    st.session_state.context = None
    st.session_state.topic_idx = 0


def index_project(loader_fn, *args):
    try:
        with st.status("Project load ho raha hai...", expanded=True) as status:
            t0 = time.time()
            st.write("Files padh raha hoon...")
            docs, pid = loader_fn(*args)
            t1 = time.time()
            st.write(f"{len(docs)} files mili ({t1 - t0:.1f}s). Embedding ho rahi hai...")
            n_chunks, cached = build_index(docs, pid)
            t2 = time.time()
            if cached:
                st.write("Ye project pehle se indexed tha, skip kar diya.")
            else:
                st.write(f"{n_chunks} chunks embed hue ({t2 - t1:.1f}s).")
            status.update(label="Project ready!", state="complete")
        reset_chat()
        st.session_state.project_id = pid
    except Exception as e:
        st.error(f"Project load nahi hua: {e}")


def next_question():
    pid = st.session_state.project_id
    for _ in range(2):
        topic = TOPICS[st.session_state.topic_idx % len(TOPICS)]
        st.session_state.topic_idx += 1
        q, ctx = ask_question(topic, pid)
        if "NOT ENOUGH INFO" not in q:
            st.session_state.question = q
            st.session_state.context = ctx
            st.session_state.messages.append({"role": "assistant", "content": q})
            return
    st.session_state.question = None
    st.session_state.messages.append(
        {"role": "assistant",
         "content": "Mere paas aur sawaal banane ke liye kaafi info nahi bachi. Interview yahin khatam!"}
    )


# ---------- Sidebar ----------
with st.sidebar:
    st.header("1. Apna project do")
    tab_file, tab_paste, tab_git = st.tabs(["README file", "Paste", "GitHub"])

    with tab_file:
        up = st.file_uploader("README (.md / .txt)", type=["md", "txt"])
        if up and st.button("Load file"):
            index_project(load_readme_file, up)

    with tab_paste:
        pasted = st.text_area("README text paste karo", height=150)
        if st.button("Load text") and pasted.strip():
            index_project(load_pasted_text, pasted)

    with tab_git:
        link = st.text_input("GitHub repo link")
        if st.button("Load repo") and link.strip():
            index_project(load_github_repo, link)

    st.header("2. Interview")
    if st.session_state.project_id and not st.session_state.messages:
        if st.button("Start interview"):
            with st.spinner("Pehla sawaal soch raha hoon..."):
                try:
                    next_question()
                except Exception as e:
                    st.error(f"LLM error: {e}")
            st.rerun()
    elif not st.session_state.project_id:
        st.caption("Pehle upar se project load karo.")

    if st.button("New interview"):
        reset_chat()
        st.rerun()

# ---------- Chat ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

answer = st.chat_input("Apna jawab yahan likho...")
if answer:
    if not st.session_state.question:
        st.warning("Pehle project load karo aur 'Start interview' dabao.")
    else:
        st.session_state.messages.append({"role": "user", "content": answer})
        with st.spinner("Tumhara jawab check kar raha hoon..."):
            try:
                feedback = evaluate_answer(
                    st.session_state.question, answer, st.session_state.context
                )
                st.session_state.messages.append({"role": "assistant", "content": feedback})
                next_question()
            except Exception as e:
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"LLM error: {e}"}
                )
        st.rerun()