import logging
import time
import os
import json

import streamlit as st
from strands import Agent
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.types.content import ContentBlock
from strands.types.session import SessionAgent
from strands_tools import calculator, current_time

from ..config import get_bedrock_config
from .agent_tools import (
    write_anki_notes_plaintext,
    create_basic_note,
    create_basic_reversed_note,
    create_basic_optional_reversed_note,
    create_cloze_note,
    # create_image_occlusion_note
)

logger = logging.getLogger(__name__)


def uid_generator() -> str:
    """Generates a unique session ID using the current time in milliseconds."""
    return str(int(time.time() * 1000))


def build_session_manager(s_id: str) -> FileSessionManager:
    return FileSessionManager(
        session_id=s_id,
        storage_dir="./sessions",
    )


@st.cache_resource
def get_bedrock_model() -> BedrockModel:
    """Builds the (stateless, shareable) Bedrock model client.

    Cached per-process: safe to share across every user's session since it
    holds no per-conversation state. Region/model come entirely from the
    environment (see anki_agent.config) — nothing here is tied to a specific
    AWS account.
    """
    config = get_bedrock_config()
    return BedrockModel(
        model_id=config["model_id"],
        region_name=config["region_name"],
    )


def build_agent(session_manager: FileSessionManager) -> Agent:
    """Builds a fresh Agent bound to the given session manager.

    Call this once per chat session (new session or session switch), not on
    every rerun — construction does real I/O against session storage.
    """
    conversation_manager = SummarizingConversationManager(
        summary_ratio=0.3,  # Summarize 30% of messages when context reduction is needed
        preserve_recent_messages=10,  # Always keep 10 most recent messages
    )

    agent = Agent(
        model=get_bedrock_model(),
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

    session_agent = SessionAgent.from_agent(agent)
    try:
        session_manager.create_agent(session_manager.session.session_id, session_agent)
    except Exception:
        logger.exception("Failed to persist new agent to session storage")
        raise

    logger.debug(
        "Built agent %s for session %s",
        agent.agent_id,
        session_manager.session.session_id,
    )
    return agent


def build_prompt(text: str | None, file_format: str | None, file_name: str | None, file_bytes: bytes | None) -> list[ContentBlock]:
    content_payload = []
    if text is not None:
        content_payload.append({"text": text})
    if file_format is not None and file_name is not None and file_bytes is not None:
        logger.debug("File attached to prompt: %s", file_name)
        if file_format in ("pdf", "docx", "txt"):
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


def create_new_agent_session() -> tuple[str, FileSessionManager, Agent]:
    """Creates a brand-new chat session: session id, session manager, and agent."""
    session_id = uid_generator()
    session_manager = build_session_manager(session_id)
    agent = build_agent(session_manager)
    return session_id, session_manager, agent


def load_agent_session(session_id: str) -> tuple[str, FileSessionManager, Agent]:
    """Loads (or resumes) an existing chat session by id."""
    session_manager = build_session_manager(session_id)
    agent = build_agent(session_manager)
    return session_id, session_manager, agent


def delete_session_if_empty(session_manager: FileSessionManager, session_id: str, agent: Agent) -> None:
    """Cleans up a session that was started but never used."""
    try:
        has_messages = bool(session_manager.list_messages(session_id, agent.agent_id))
    except Exception:
        has_messages = False

    if not has_messages:
        try:
            session_manager.delete_session(session_id)
        except Exception:
            logger.exception("Failed to delete empty session %s", session_id)


def retrieve_sessions_list() -> list[dict]:
    sessions = []
    if not os.path.isdir("./sessions"):
        return sessions
    for entry in os.scandir("./sessions"):
        if entry.is_dir() and entry.name.startswith("session_"):
            session_id = entry.name.removeprefix("session_")
            meta_path = os.path.join(entry.path, "session.json")
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    metadata = json.load(f)
            sessions.append({"session_id": session_id, **metadata})
    return sessions
