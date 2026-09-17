# Anki Agent
A Streamlit chat app for creating Anki flashcard decks with an AI agent. Describe what you want to learn, optionally upload a document (PDF, DOCX, or TXT), and the agent turns it into an Anki-importable plaintext deck.
Built with [Strands Agents](https://github.com/strands-agents/sdk-python) and Amazon Bedrock.
 
## Features
- Conversational flashcard creation — the agent asks about content and note types before generating cards
- Supports Basic, Basic (reversed), Basic (optional reversed), and Cloze note types
- Upload a PDF, DOCX, or TXT file as source material
- Exports notes as a tab-delimited plaintext file ready to import into Anki
- Persistent chat sessions with history, stored locally under `sessions/`
## Requirements
 
- Python 3.11+
- AWS credentials configured for Bedrock access (the agent uses `global.amazon.nova-2-lite-v1:0` in `us-west-2`)
## Setup
 
```bash
pip install -e .
```
 
## Usage
```bash
streamlit run src/anki_agent/app.py
```
Then open the app in your browser, type a message (or attach a file) describing what you'd like to study, and follow the agent's prompts. When you confirm the deck content, it writes a plaintext export file you can import directly into Anki (File → Import).
 
## Project Structure
```
src/anki_agent/
├── app.py                  # Streamlit UI
└── agent/
    ├── agent.py             # Agent setup, model, and session management
    └── agent_tools.py       # Anki note-building and export tools
sessions/                    # Saved chat sessions (auto-generated)
```
 
## Status
This project is a work in progress. Known gaps include: no image occlusion support yet, limited error handling, and session management is still rough around the edges. See inline `TODO`s in the code for details.
