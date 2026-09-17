import asyncio
import logging
import time

import nest_asyncio
import streamlit as st

from anki_agent.config import MissingBedrockConfigError
from anki_agent.agent.agent import (
    build_prompt,
    create_new_agent_session,
    load_agent_session,
    delete_session_if_empty,
    retrieve_sessions_list,
)

from strands.types.exceptions import SessionException

from streamlit.runtime.uploaded_file_manager import UploadedFile

logger = logging.getLogger(__name__)
nest_asyncio.apply()

st.set_page_config(page_title="Anki Agent Chat", page_icon="\U0001F4D8")


def init_session_state() -> bool:
    """Ensures this browser session has its own session id / manager / agent.

    Returns False (and renders a setup error) if Bedrock isn't configured yet.
    """
    if "agent_session_id" in st.session_state:
        return True

    try:
        session_id, session_manager, agent = create_new_agent_session()
    except MissingBedrockConfigError as e:
        st.error(
            "Bedrock isn't configured yet.\n\n"
            f"{e}"
        )
        st.stop()
        return False

    st.session_state.agent_session_id = session_id
    st.session_state.session_manager = session_manager
    st.session_state.agent = agent
    st.session_state.chat_history = []
    st.session_state.loaded_session_id = None
    st.session_state.file_uploader_key = 0
    return True


def switch_session_state(session_id: str, fresh: bool) -> None:
    """Points this browser session at a new or existing agent session."""
    old_manager = st.session_state.get("session_manager")
    old_session_id = st.session_state.get("agent_session_id")
    old_agent = st.session_state.get("agent")
    if old_manager is not None and old_session_id is not None and old_agent is not None:
        delete_session_if_empty(old_manager, old_session_id, old_agent)

    if fresh:
        session_id, session_manager, agent = create_new_agent_session()
    else:
        session_id, session_manager, agent = load_agent_session(session_id)

    st.session_state.agent_session_id = session_id
    st.session_state.session_manager = session_manager
    st.session_state.agent = agent
    st.session_state.file_uploader_key += 1


async def get_response(user_message: str | None, uploaded_file: UploadedFile | None):
    content_block = build_prompt(
        user_message,
        uploaded_file.type.split("/")[-1] if uploaded_file else None,
        f"{uploaded_file.name.split('.')[0]}_{int(time.time())}" if uploaded_file else None,
        uploaded_file.read() if uploaded_file else None,
    )
    response_parts = []
    async for event in st.session_state.agent.stream_async(content_block):
        if "data" in event:
            response_parts.append(event["data"])
    return "".join(response_parts)


if not init_session_state():
    st.stop()

agent = st.session_state.agent
session_manager = st.session_state.session_manager
session_id = st.session_state.agent_session_id

# Load chat history for this session (only when it changes, e.g. after a switch)
if st.session_state.loaded_session_id != session_id:
    messages = []
    try:
        messages = session_manager.list_messages(session_id, agent.agent_id)
    except SessionException as e:
        if "Messages directory missing" not in str(e):
            raise

    st.session_state.chat_history = []
    for message in messages:
        content = message.message.get("content")
        if content and content[0].get("text") is not None:
            role = "You" if message.message.get("role") == "user" else "Agent"
            st.session_state.chat_history.append((role, content[0].get("text")))
    st.session_state.loaded_session_id = session_id

with st.sidebar:
    st.header("Anki Agent")
    if st.button("+ Start New Session"):
        switch_session_state(session_id=None, fresh=True)
        st.rerun()

    st.markdown("### Recent Sessions")
    with st.spinner("Loading Recent Sessions..."):
        for session in retrieve_sessions_list():
            other_id = session["session_id"]
            has_messages = False
            try:
                has_messages = bool(session_manager.list_messages(other_id, agent.agent_id))
            except Exception:
                has_messages = False

            if not has_messages:
                continue

            if other_id == session_id:
                st.button(f"{other_id} - [Active]", disabled=True, key=f"session_{other_id}")
            else:
                if st.button(other_id, key=f"session_{other_id}"):
                    switch_session_state(session_id=other_id, fresh=False)
                    st.rerun()

st.title("Anki Agent Chat")
st.markdown("Interact with your Strands-based agent using this simple Streamlit interface.")

prompt = st.chat_input(
    placeholder="Type your message here...",
    accept_file=True,
    file_type=["docx", "txt", "pdf"],
    key=f"chat_input_{st.session_state.file_uploader_key}",
)

user_message = prompt.text if prompt and prompt.text else None
uploaded_file = prompt.files[0] if prompt and prompt["files"] else None

if user_message or uploaded_file:
    st.session_state.chat_history.append(("You", user_message))
    with st.spinner("Agent is thinking..."):
        try:
            agent_response = asyncio.run(get_response(user_message, uploaded_file))
        except Exception:
            logger.exception("Agent call failed")
            agent_response = "Sorry, something went wrong handling that message. Please try again."
        st.session_state.file_uploader_key += 1

    st.session_state.chat_history.append(("Agent", agent_response))
    st.rerun()

for speaker, text in st.session_state.chat_history:
    role = "user" if speaker == "You" else "assistant"
    with st.chat_message(role):
        st.markdown(text)
