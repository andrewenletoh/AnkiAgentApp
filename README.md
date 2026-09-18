# Anki Agent
 
A Streamlit chat app for creating Anki flashcard decks with an AI agent. Describe what you want to learn, optionally upload a document (PDF, DOCX, or TXT), and the agent turns it into an Anki-importable plaintext deck.
 
Built with [Strands Agents](https://github.com/strands-agents/sdk-python) and Amazon Bedrock.
 
## Features
 
- Conversational flashcard creation: the agent asks about content and note types before generating cards
- Supports Basic, Basic (reversed), Basic (optional reversed), and Cloze note types
- Upload a PDF, DOCX, or TXT file as source material
- Exports notes as a tab-delimited plaintext file ready to import into Anki
- Persistent chat sessions with history, stored locally under `sessions/`
## Requirements
 
- Python 3.11+
- Your own AWS account with Amazon Bedrock access enabled for the model you want to use
## AWS / Bedrock Setup
 
This repo does **not** ship with, or connect to, any specific AWS account. Every person who runs it points it at their own AWS credentials and their own choice of region/model. If the required settings aren't configured, the app refuses to start rather than silently falling back to a default — so cloning this repo can never result in charges to anyone else's account.
 
To configure it:
 
1. Make sure you have AWS credentials available on your machine (via `aws configure`, an `AWS_PROFILE`, environment variables, or an IAM role) with access to Bedrock in your chosen region.
2. Copy the example env file and fill in your own values:
```bash
   cp .env.example .env
```
3. Edit `.env`:
```
   AWS_REGION=us-west-2
   BEDROCK_MODEL_ID=global.amazon.nova-2-lite-v1:0
```pythonb
   Use whichever region and model you've enabled access to in the Bedrock console. `.env` is gitignored and never committed.
 
All Bedrock usage is billed to whichever AWS credentials are active when you run the app.

## Setup
 
Set up a virtual environment so dependencies stay scoped to this project, then install:
 
```bash
python3 -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -e .
```

 
## Usage
 
```bash
streamlit run src/anki_agent/app.py
```
 
Then open the app in your browser, type a message (or attach a file) describing what you'd like to study, and follow the agent's prompts. When you confirm the deck content, it writes a plaintext export file you can import directly into Anki (File → Import).
 
Each browser session gets its own isolated chat session and agent instance — opening multiple tabs won't mix conversations together.
 
## Project Structure
 
```
src/anki_agent/
├── app.py                  # Streamlit UI (per-session state lives in st.session_state)
├── config.py                # Reads required AWS/Bedrock settings from the environment
└── agent/
    ├── agent.py             # Agent/session construction, Bedrock model client
    └── agent_tools.py       # Anki note-building and export tools
sessions/                    # Saved chat sessions (auto-generated, gitignored)
```
 
## Status
 
This project is a work in progress.

### To Do

- Tool call recording is still wonky, need to figure out what behaviors and consistent outputs I want to ensure
- Session and Agent invokation may be redundant, need to investigate and check docs on that.
-Fix loading sessions more efficiently in side bar. Also give each session a summarized one-liner instead of session id (might need a separate agent or something for that?)
- Figure out how to make a tool call work for image occlusion note types
- Fix anki deck plaintext import file generation and storage
- Gotta take another look at the context window and token limit, will have to consider some constraints and how to break up the tasks.
- User input from friends says that File uploading is somewhat hindered by poor file type accomodation and uncertainty on how the agent parses the information into actual cards. Need to look into how to give more directive control to user on generating cards without typing a prompt with the same volume as it would be to just create the card.
