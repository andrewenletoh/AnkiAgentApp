TODO:
    - Handle async in Streamlit properly (consider using threads or asyncio.run)
    - Add error handling for agent responses
    - Improve UI/UX (e.g., show loading spinner, better message formatting)
    - Add support for images or other media in responses (downloading created decks, uploading files, etc.) [WIP]
        - Offer to download files for usage [TODO]
        - Handle image files for image occlusion cards [TODO]
    - More Sessions management capabilities [WIP]
        - Add conversation histories limit/expiry [TODO]
        - Implement functionality to manually delete past chat sessions [TODO]
        - Fix handling of starting empty sessions (sometimes they are not deleted/handled properly) [TODO]
    - SWITCH TO TYPESCRIPT, DEPRECATE THIS PROJECT ONCE DONE

pip install -e .
python -m py_compile src/anki_agent/app.py
streamlit run .\src\anki_agent\app.py
