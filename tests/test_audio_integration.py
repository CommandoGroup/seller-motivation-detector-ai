import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class AudioIntegrationTest(unittest.TestCase):
    def test_real_audio_worker_result_is_read_by_fresh_http_workers(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(pathlib.Path(directory) / 'jobs.sqlite3')
            os.environ['AUDIO_JOB_DB'] = db_path
            from job_queue import JobQueue
            import async_worker
            previous = async_worker.job_queue
            self.addCleanup(setattr, async_worker, 'job_queue', previous)
            async_worker.job_queue = JobQueue(db_path)
            audio = pathlib.Path(directory) / 'synthetic.wav'
            audio.write_bytes(b'RIFF synthetic provider fixture')
            transcription = SimpleNamespace(text='Synthetic transcript', duration=6)
            analyzer = SimpleNamespace(
                client=SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=lambda **kwargs: transcription))),
                analyze_transcript=lambda transcript: {'score': 77})
            usage = SimpleNamespace(record_audio_usage=lambda *args: None,
                                    get_usage_stats=lambda *args: {'audio_minutes_used': 0.1})
            job = async_worker.start_async_job(str(audio), 'synthetic-test', analyzer, usage, {})
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                state = async_worker.job_queue.get_job(job)
                if state['status'] in ('complete', 'error'):
                    break
                time.sleep(0.01)
            self.assertEqual('complete', state['status'], state.get('error'))
            self.assertFalse(audio.exists())
            # Import the unmodified Flask receiver in independent processes. No provider request is made.
            code = '''import os, sys
sys.path.insert(0, sys.argv[1])
from app import app
with app.test_client() as client:
    answer = client.get('/api/job-status/' + sys.argv[2])
    assert answer.status_code == 200, answer.get_json()
    body = answer.get_json()
    assert body['status'] == 'complete'
    assert body['result']['analysis']['score'] == 77
    assert body['result']['transcript'] == 'Synthetic transcript'
    assert client.get('/api/job-status/missing').status_code == 404
'''
            for _ in range(2):
                env = {**os.environ, 'AUDIO_JOB_DB': db_path, 'OPENAI_API_KEY': 'synthetic-test-only'}
                child = subprocess.run([sys.executable, '-c', code, str(ROOT), job], cwd=directory,
                                       env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(0, child.returncode, child.stderr)


if __name__ == '__main__':
    unittest.main()
