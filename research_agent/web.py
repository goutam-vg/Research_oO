"""Streamlit web app: streamlit run app.py"""

import threading
from datetime import datetime

import streamlit as st

from research_agent.agent import research_stream, warm_up
from research_agent.config import LENGTH_CHOICES, get_model_name
from research_agent.health import check_ollama, installed_models
from research_agent.storage import build_filename, format_summary, list_summaries, save_summary


@st.cache_resource
def _start_warm_up(model: str) -> bool:
    """Load the model in the background once, while the user types a topic."""
    threading.Thread(target=warm_up, args=(model,), daemon=True).start()
    return True


@st.cache_data(ttl=30)
def _installed_models() -> list[str]:
    try:
        return installed_models()
    except ConnectionError:
        return []


def _sidebar() -> tuple[str, str, str]:
    st.sidebar.header("Settings")
    default = get_model_name()
    models = _installed_models()
    if models:
        model = st.sidebar.selectbox("Model", models, index=models.index(default) if default in models else 0)
    else:
        model = st.sidebar.text_input("Model", value=default)
    length = st.sidebar.selectbox("Length", LENGTH_CHOICES, index=1)
    lang = st.sidebar.text_input("Language", value="English").strip() or "English"
    return model, length, lang


def _run(topic: str, model: str, length: str, lang: str) -> None:
    st.session_state.pop("result", None)
    status = st.status("Starting...", expanded=True)
    box = st.empty()
    typed, summary, sources = "", "", []
    try:
        for event in research_stream(topic, model, length, lang):
            kind = event["type"]
            if kind == "status":
                status.update(label=event["text"] + "...")
            elif kind == "token":
                typed += event["text"]
                box.markdown(typed + " ▌")  # blinking-cursor look while typing
            elif kind == "done":
                summary, sources = event["summary"], event["sources"]
    except Exception as error:
        status.update(label="Failed", state="error")
        st.error(str(error))
        return

    box.empty()
    status.update(label="Done", state="complete", expanded=False)
    when = datetime.now()
    txt = format_summary(topic, summary, model, sources, "txt", when)
    md = format_summary(topic, summary, model, sources, "md", when)
    save_summary(topic, txt)
    st.session_state["result"] = {
        "txt": txt,
        "md": md,
        "txt_name": build_filename(topic, "txt", when),
        "md_name": build_filename(topic, "md", when),
    }


def _show_result() -> None:
    result = st.session_state.get("result")
    if not result:
        return
    st.text_area("Summary", result["txt"], height=400, key="result_text")
    left, right = st.columns(2)
    left.download_button("⬇️ Download .txt", result["txt"], result["txt_name"], "text/plain", key="dl_txt")
    right.download_button("⬇️ Download .md", result["md"], result["md_name"], "text/markdown", key="dl_md")


def _show_history() -> None:
    st.sidebar.header("History")
    files = list_summaries()
    if not files:
        st.sidebar.caption("Saved summaries will appear here.")
        return
    choice = st.sidebar.selectbox(
        "Past summaries", files, format_func=lambda p: p.name, index=None, placeholder="Open a summary..."
    )
    if choice:
        text = choice.read_text(encoding="utf-8")
        with st.expander(f"Saved: {choice.name}", expanded=True):
            st.text_area("Saved summary", text, height=300, key="history_text", label_visibility="collapsed")
            st.download_button("⬇️ Download", text, choice.name, "text/plain", key="history_dl")


def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="🔎")
    model, length, lang = _sidebar()
    _start_warm_up(model)

    st.title("🔎 Research Agent")
    st.caption("Enter a topic, watch the summary being written, download it with references.")
    topic = st.text_input("Topic", placeholder="e.g. Quantum computing").strip()

    if st.button("Summarize", type="primary", disabled=not topic):
        problem = check_ollama(model)
        if problem:
            st.error(problem)
        else:
            _run(topic, model, length, lang)

    _show_result()
    _show_history()
