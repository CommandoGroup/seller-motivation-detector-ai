# Operations

Railway service: `seller-motivation-detector-ai`. Production URL: https://web-production-7542e.up.railway.app/

The GitHub repository's `main` branch is connected to automatic production deployment. A push to `main` is the live trigger. Tags and review branches do not establish that production is running their source.

## Local preparation

Install `requirements.txt` in an isolated Python environment. Set any required key through the environment without printing it. Run `python app.py` and use the local address printed by Flask.

Set `OPENAI_API_KEY` in Railway. The Procfile starts 2 Gunicorn workers with a 600-second timeout. Use 1 Railway instance. `AUDIO_JOB_DB` optionally selects a writable shared SQLite file; default `uploads/audio-jobs.sqlite3`. Every worker on the instance must use the same path. New jobs prune status records older than 24 hours. Preserve the database across worker restarts to retain status; multiple instances need an external shared store. Large audio conversion uses pydub and requires FFmpeg on the host.

## Release

1. Prepare the reviewed commit on a branch. Fetch `origin` and verify that the candidate includes the current `origin/main`. Run the focused validation before publishing it.
2. Test the candidate in a nonproduction running environment at both supported widths. Record the source commit and results before the live step.
3. The owner advances `main` to the exact validated candidate with an ordinary fast-forward push. This starts Railway production deployment. Do not rewrite history.
4. Read Railway's deployment status and deployed source commit. Require a successful deployment of that exact candidate.
5. Open the tool inside My Resources on the live member site at 1280 and 390 pixels. Analyze a transcript and download its PDF. Upload audio and poll the returned job until its completed analysis appears. Repeated polls must never alternate between a valid result and 404.
6. Record the deployed SHA, verification and screenshots before releasing the next app.

## Rollback

In Railway, select the preceding successful deployment and use its redeploy action. Record its source SHA and rerun the affected live checks. Do not force-push a branch as rollback.
