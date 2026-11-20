"""Streamlit-App: Chat mit dem RAG-Leitfaden."""

from datetime import datetime
import streamlit as st
import rag_core


# ============================================================================
# Hilfsfunktionen
# ============================================================================

def _generate_chat_markdown() -> str:
    """Erzeugt den Chat-Verlauf als Markdown mit Quellen."""
    lines = ["# Chat mit dem RAG-Leitfaden\n"]

    for i, msg in enumerate(st.session_state.assistant.history):
        if msg["role"] == "user":
            lines.append(f"## Du\n{msg['content']}\n")
        else:
            lines.append(f"## KI\n{msg['content']}\n")
            # Quellen für diese Antwort hinzufügen, falls vorhanden
            if i in st.session_state.sources_history:
                sources = st.session_state.sources_history[i]
                if sources:
                    lines.append("### Quellen")
                    for source in sources:
                        page = source.get("page", "?")
                        text = source.get("text", "")[:300]
                        lines.append(f"- **Seite {page}**: {text}...")
                    lines.append("")

    return "\n".join(lines)


def _format_sources(sources: list[dict], max_chars: int = 300) -> str:
    """Formatiert Quellen als Markdown mit Zeichenbegrenzung."""
    if not sources:
        return "Keine Quellen gefunden."

    result = []
    for i, source in enumerate(sources, 1):
        text = source.get("text", "")[:max_chars]
        page = source.get("page", "?")
        score = source.get("score", 0)
        result.append(f"{i}. **Seite {page}** (Relevanz: {score:.2f})\n   {text}...")

    return "\n".join(result)


# ============================================================================
# Session State Initialisierung
# ============================================================================

if "assistant" not in st.session_state:
    with st.spinner("🔄 Leitfaden wird indexiert..."):
        st.session_state.assistant = rag_core.Assistant()

if "k_sources" not in st.session_state:
    st.session_state.k_sources = 3

if "summary" not in st.session_state:
    st.session_state.summary = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "sources_history" not in st.session_state:
    st.session_state.sources_history = {}


# ============================================================================
# UI: Sidebar
# ============================================================================

with st.sidebar:
    st.subheader("Einstellungen")

    st.session_state.k_sources = st.slider(
        "Anzahl Quellen",
        min_value=1,
        max_value=5,
        value=st.session_state.k_sources,
        help="Wie viele Quellen sollen zur Beantwortung herangezogen werden?"
    )

    if st.button("Neuer Chat", use_container_width=True):
        st.session_state.assistant.reset()
        st.session_state.summary = None
        st.session_state.sources_history = {}
        st.rerun()

    # Download-Button für Chat-Verlauf
    if st.session_state.assistant.history:
        chat_md = _generate_chat_markdown()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        st.download_button(
            label="Chat herunterladen",
            data=chat_md,
            file_name=f"rag_chat_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True
        )


# ============================================================================
# UI: Hauptbereich
# ============================================================================

st.title("Chat mit dem RAG-Leitfaden")

# Disclaimer
st.info("ℹ️ Antworten stammen ausschließlich aus dem RAG-Leitfaden.")

# Button "Dokument zusammenfassen"
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("Dokument zusammenfassen", use_container_width=True):
        with st.spinner("📄 Zusammenfassung wird erstellt..."):
            st.session_state.summary = st.session_state.assistant.summarize()

# Zusammenfassung anzeigen, falls vorhanden
if st.session_state.summary:
    with st.expander("📋 Zusammenfassung", expanded=True):
        st.markdown(st.session_state.summary)

# Beispielfragen
st.subheader("Beispielfragen")
example_questions = [
    "Was ist RAG?",
    "Wie funktioniert Retrieval?",
    "Wann lohnt sich RAG?"
]

cols = st.columns(3)
for col, question in zip(cols, example_questions):
    with col:
        if st.button(question, use_container_width=True, key=f"btn_{question}"):
            st.session_state.pending_question = question

# Chat-Verlauf anzeigen
st.subheader("Chat")
chat_container = st.container()

with chat_container:
    for msg in st.session_state.assistant.history:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(msg["content"])

                # Quellen unter der Antwort anzeigen
                # (Wir zeigen die Quellen der letzten Antwort an, falls vorhanden)
                if st.session_state.assistant.last_sources:
                    with st.expander(f"📚 Quellen ({len(st.session_state.assistant.last_sources)})"):
                        st.markdown(_format_sources(st.session_state.assistant.last_sources))

                st.caption("Quelle: RAG-Leitfaden")

# Input-Feld für neue Fragen
user_input = st.chat_input("Deine Frage zum Leitfaden...")

# Falls eine Beispielfrage angeklickt wurde, diese verarbeiten
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

if user_input:
    # Frage zum Verlauf hinzufügen und anzeigen
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)

    # Antwort streamen
    with st.chat_message("assistant", avatar="🤖"), st.spinner("💭 Antwort wird generiert..."):
        # Streamen der Antwort
        response_placeholder = st.empty()
        full_response = ""

        try:
            for chunk in st.session_state.assistant.ask_stream(user_input, k=st.session_state.k_sources):
                full_response += chunk
                response_placeholder.write(full_response)

            # Quellen speichern für Download
            answer_index = len(st.session_state.assistant.history) - 1
            st.session_state.sources_history[answer_index] = st.session_state.assistant.last_sources

            # Quellen anzeigen
            if st.session_state.assistant.last_sources:
                with st.expander(f"📚 Quellen ({len(st.session_state.assistant.last_sources)})"):
                    st.markdown(_format_sources(st.session_state.assistant.last_sources))
            else:
                st.warning("⚠️ Keine passenden Quellen im Leitfaden gefunden.")

            st.caption("Quelle: RAG-Leitfaden")

        except Exception as e:  # noqa: BLE001
            st.error(f"❌ Fehler bei der Antwortgenerierung: {e!r}")
