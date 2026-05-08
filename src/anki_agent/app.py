import asyncio
import time
import nest_asyncio

import streamlit as st

from anki_agent.agent.agent import (
    build_prompt,
    current_session_id,
    current_agent,
    current_session_manager,
    retrieve_sessions_list,
    start_new_chat_session,
    switch_to_session
)

from strands.types.exceptions import SessionException

from streamlit.runtime.uploaded_file_manager import UploadedFile

user_message = None
uploaded_file = None
fresh_session = True

nest_asyncio.apply()

async def get_response(user_message: str | None, uploaded_file: UploadedFile | None):
    content_block = build_prompt(
        user_message,
        uploaded_file.type.split("/")[-1] if uploaded_file else None,
        f"{uploaded_file.name.split('.')[0]}_{int(time.time())}" if uploaded_file else None,
        uploaded_file.read() if uploaded_file else None
    )
    response_parts = []
    async for event in current_agent.stream_async(content_block):
        if "data" in event:
            response_parts.append(event["data"])
    return "".join(response_parts)

def start_new_chat_callback() :
    global fresh_session
    start_new_chat_session()
    fresh_session = True

def switch_chat_callback( session_id: str):
    global fresh_session
    start_new_chat_session()
    fresh_session = True

messages = []
if current_session_id is not None:
    try:
        messages = current_session_manager.list_messages(
            current_session_id,
            current_agent.agent_id
        )
    except SessionException as e:
        if "Messages directory missing" in str(e):
            messages = []
        else:
            raise e
    
st.set_page_config(page_title="Anki Agent Chat", page_icon="📘")

if st.session_state.get("loaded_session_id") != current_session_id:
    st.session_state.chat_history = []
    for message in messages:
        content = message.message.get("content")
        if content and content[0].get("text") is not None:
            role = "You" if message.message.get("role") == "user" else "Agent"
            st.session_state.chat_history.append((role, content[0].get("text")))
    st.session_state.loaded_session_id = current_session_id

with st.sidebar:
    st.header("Anki Agent")
    st.button("+ Start New Session", on_click=start_new_chat_session)
    st.markdown("### Recent Sessions")
    with st.spinner("Loading Recent Sessions..."):
        if current_session_manager is not None:
            list_of_sessions = retrieve_sessions_list()

            for session in list_of_sessions:

                has_messages = False
                try:
                    has_messages = bool(current_session_manager.list_messages(session["session_id"], current_agent.agent_id))
                except Exception:
                    has_messages = False
                
                if has_messages:
                    
                    if session["session_id"] == current_session_manager.session.session_id:
                        st.button(f"{session['session_id']} - [Active]", disabled=True)
                    else:
                        st.button(f"{session['session_id']}", on_click=switch_to_session, args=(session["session_id"]))
                    



st.title("Anki Agent Chat")
st.markdown("Interact with your Strands-based agent using this simple Streamlit interface.")

DEV_MODE = False  # Set to True to disable file upload and extra file handling while iterating on the agent.

if DEV_MODE:
    st.info("Dev mode enabled: ")

if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

prompt = st.chat_input(placeholder="Type your message here...", accept_file=True, file_type=["docx", "txt", "pdf"])

if prompt and prompt.text:
    user_message = prompt.text
if prompt and prompt["files"]:
    uploaded_file = prompt.files[0]

if user_message or uploaded_file:
    st.session_state.chat_history.append(("You", user_message))
    with st.spinner("Agent is thinking..."):

        result = current_session_manager.read_agent(current_session_id, current_agent.agent_id)
        print(f"DEBUG | pre-call read_agent: {result}")
        print(f"DEBUG | current_session_id: {current_session_id}")
        print(f"DEBUG | current_agent.agent_id: {current_agent.agent_id}")

        agent_response = asyncio.run(get_response(user_message, uploaded_file))

        st.session_state.file_uploader_key += 1

    st.session_state.chat_history.append(("Agent", agent_response))
    st.rerun()

for speaker, text in st.session_state.chat_history:
    role = "user" if speaker == "You" else "assistant"
    with st.chat_message(role):
        st.markdown(text)
