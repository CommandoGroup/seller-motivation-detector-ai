# Architecture

Seller Motivation Detector AI is a standalone Flask application embedded in the members' My Resources page.

`app.py` serves the page from app.py (HTML_TEMPLATE). `POST /api/analyze-transcript`, `POST /api/analyze-audio`, `GET /api/job-status/<job_id>`, `GET /api/usage-stats` and `POST /api/export-pdf`. `ai_analyzer.py` calls OpenAI. `async_worker.py` transcribes and analyzes uploads in a background thread. `usage_tracker.py` tracks usage.

The members interface is bundled in `static/members/`: `app.css`, `look.css`, `tool.css`, and the images they use. Cross-origin frames cannot inherit their parent's styles. The template's stylesheet query values are the first 10 characters of each file's SHA-256; update them when CSS changes. `tool.css` adapts the existing layout.

`requirements.txt` pins dependencies and `Procfile` defines the hosted entry point.
