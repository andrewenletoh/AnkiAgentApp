import logging
import time
import os
import json

from strands import Agent
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.types.content import ContentBlock
from strands.types.session import SessionAgent
from strands_tools import calculator, current_time

from .agent_tools import (
    write_anki_notes_plaintext,
    create_basic_note,
    create_basic_reversed_note,
    create_basic_optional_reversed_note,
    create_cloze_note,
    # create_image_occlusion_note
)


# Enables Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG)
logging.getLogger("strands.models.bedrock").setLevel(logging.WARNING)


# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)


def uid_generator() :
    """Generates a unique session ID using the current time in milliseconds."""
    return str(int(time.time() * 1000))


conversation_manager = SummarizingConversationManager(
    summary_ratio=0.3,  # Summarize 30% of messages when context reduction is needed
    preserve_recent_messages=10,  # Always keep 10 most recent messages
)


def build_session_manager(s_id: str) -> FileSessionManager:
    return FileSessionManager(
        session_id=s_id,
        storage_dir="./sessions"
    )


bedrock_model = BedrockModel(
    model_id="global.amazon.nova-2-lite-v1:0",
    region_name="us-west-2",
)


# # Create an agent with tools from the community-driven strand-tools package
# # as well as aour custom letter_counter tool
def build_agent(session_manager: FileSessionManager) -> Agent:
    agent = Agent(
        # model="us.anthropic.claude-sonnet-4-6",
        model=bedrock_model,
        tools=[
            calculator,
            current_time,
            write_anki_notes_plaintext,
            create_basic_note,
            create_basic_reversed_note,
            create_basic_optional_reversed_note,
            create_cloze_note,
            # create_image_occlusion_note,
        ],
        system_prompt="""
        You are an assistant for creating and editing Anki flashcards and decks. 
    
        - help the user create flashcards by asking them questions about the content they want to learn
        - ask the note types they want to use if not specified
        - generate or edit flashcards and decks based on their answers
        - request for confirmation of deck content before committing to a plaintext file output
        """,
        callback_handler=None,
        conversation_manager=conversation_manager,
        session_manager=session_manager,
    )
    print(f"DEBUG | session_manager.session_id: {session_manager.session_id}")
    print(f"DEBUG | session_manager.session.session_id: {session_manager.session.session_id}")
    print(f"DEBUG | agent.agent_id: {agent.agent_id}")

    session_agent = SessionAgent.from_agent(agent)
    print(f"DEBUG | SessionAgent.agent_id: {session_agent.agent_id}")

    try:
        session_manager.create_agent(session_manager.session.session_id, session_agent)
        print("DEBUG | create_agent succeeded")
        
        # Verify it was actually written
        result = session_manager.read_agent(session_manager.session.session_id, agent.agent_id)
        print(f"DEBUG | read_agent after create: {result}")
    except Exception as e:
        print(f"DEBUG | create_agent failed: {type(e).__name__}: {e}")
        raise

    return agent


def build_prompt(text: str | None, file_format: str | None, file_name: str | None, file_bytes: bytes | None) -> list[ContentBlock]:
    content_payload = []
    if text is not None:
        content_payload.append({"text": text})
    if file_format is not None and file_name is not None and file_bytes is not None:
        print("DEBUG | FILE DETECTED IN PROMPT BUILDING: " + file_name.split(".")[0])
        if file_format == "pdf" or file_format == "docx" or file_format == "txt":
            content_payload.append({
                "document": {
                    "format": file_format,  # Extracts 'pdf', 'docx', or 'txt' from the MIME type
                    "name": file_name,
                    "source": {
                        "bytes": file_bytes
                    }
                }
        })
    return content_payload


current_session_id = uid_generator()
current_session_manager = build_session_manager(current_session_id)
current_agent = build_agent(current_session_manager)


def retrieve_sessions_list() -> list[dict]:
    sessions = []
    for entry in os.scandir("./sessions"):
        if entry.is_dir() and entry.name.startswith("session_"):
            session_id = entry.name.removeprefix("session_")
            # Optionally read metadata
            meta_path = os.path.join(entry.path, "session.json")
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    metadata = json.load(f)
            sessions.append({"session_id": session_id, **metadata})
    return sessions

def start_new_chat_session():
    global current_session_id, current_agent, current_session_manager

    try:
        if not current_session_manager.list_messages(current_session_id, current_agent.agent_id):
            current_session_manager.delete_session(current_session_id)
    except Exception:
        current_session_manager.delete_session(current_session_id)

    current_session_id = uid_generator()
    current_session_manager = build_session_manager(current_session_id)
    current_agent = build_agent(current_session_manager)


def switch_to_session(session_id: str):
    global current_session_id, current_agent, current_session_manager

    if session_id == current_session_id:
        return

    try:
        if not current_session_manager.list_messages(current_session_id, current_agent.agent_id):
            current_session_manager.delete_session(current_session_id)
    except Exception:
        current_session_manager.delete_session(current_session_id)

    current_session_id = session_id
    current_session_manager = build_session_manager(current_session_id)
    current_agent = build_agent(current_session_manager)

# print(result.metrics.get_summary())
