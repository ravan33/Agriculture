# External Agriculture Corpus

Place large agriculture datasets here to scale chatbot knowledge.

Supported formats:
- CSV with columns: `text` and optional `suggestions` (pipe-separated)
- JSON list of objects: `{ "text": "...", "suggestions": ["..."] }`
- JSONL: one JSON object per line with same keys
- TXT: paragraph blocks separated by blank lines

Build index command:

python manage.py build_chatbot_index --input-dir data/agri_corpus --output model/chatbot_index.pkl

After building, chatbot will load `model/chatbot_index.pkl` on startup for faster responses.
