"""Short-lived audio job status shared by every web worker on this instance."""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


class JobQueue:
    def __init__(self, db_path=None):
        self.path = os.fspath(db_path or os.environ.get('AUDIO_JOB_DB', os.path.join(os.path.dirname(__file__), 'uploads', 'audio-jobs.sqlite3')))
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with self._connection() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS audio_jobs (
                job_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, status TEXT NOT NULL,
                progress INTEGER NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, result TEXT, error TEXT)''')
            db.execute('CREATE INDEX IF NOT EXISTS audio_jobs_created ON audio_jobs(created_at)')

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_job(self, user_id: str = "anonymous") -> str:
        job_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._connection() as db:
            db.execute('''INSERT INTO audio_jobs (job_id, user_id, status, progress, message, created_at, updated_at)
                VALUES (?, ?, 'queued', 0, 'Job queued for processing', ?, ?)''', (job_id, user_id, now, now))
            db.execute('DELETE FROM audio_jobs WHERE created_at < ?', ((datetime.now() - timedelta(hours=24)).isoformat(),))
        return job_id

    def update_job(self, job_id: str, status: str = None, progress: int = None,
                   message: str = None, result: Any = None, error: str = None):
        # Partial SQL writes avoid lost fields. No database lock spans a provider call.
        fields = {'updated_at': datetime.now().isoformat()}
        if status:
            fields['status'] = status
        if progress is not None:
            fields['progress'] = progress
        if message:
            fields['message'] = message
        if result is not None:
            fields['result'] = json.dumps(result)
        if error:
            fields['error'] = error
        with self._connection() as db:
            changed = db.execute('UPDATE audio_jobs SET ' + ', '.join(k + ' = ?' for k in fields) + ' WHERE job_id = ?', [*fields.values(), job_id])
            return changed.rowcount > 0

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._connection() as db:
            row = db.execute('SELECT * FROM audio_jobs WHERE job_id = ?', (job_id,)).fetchone()
        if row is None:
            return None
        job = dict(row)
        for field in ('created_at', 'updated_at'):
            job[field] = datetime.fromisoformat(job[field])
        if job['result'] is not None:
            job['result'] = json.loads(job['result'])
        return job

    def delete_job(self, job_id: str):
        with self._connection() as db:
            db.execute('DELETE FROM audio_jobs WHERE job_id = ?', (job_id,))

    def cleanup_old_jobs(self, hours: int = 24):
        with self._connection() as db:
            deleted = db.execute('DELETE FROM audio_jobs WHERE created_at < ?', ((datetime.now() - timedelta(hours=hours)).isoformat(),))
            return deleted.rowcount


job_queue = JobQueue()
