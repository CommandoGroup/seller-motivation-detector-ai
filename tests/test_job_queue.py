import concurrent.futures
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
GLOBAL_DIR = tempfile.TemporaryDirectory()
os.environ['AUDIO_JOB_DB'] = str(pathlib.Path(GLOBAL_DIR.name) / 'global.sqlite3')
from job_queue import JobQueue


class JobQueueTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / 'jobs.sqlite3'
        self.queue = JobQueue(self.path)

    def test_jobs_survive_a_second_worker_process(self):
        job = self.queue.create_job('synthetic-test')
        code = '''import sys
from job_queue import JobQueue
queue = JobQueue(sys.argv[1])
job = queue.get_job(sys.argv[2])
assert job and job['status'] == 'queued', 'another worker cannot see the uploaded job'
assert queue.update_job(sys.argv[2], status='complete', progress=100, result={'analysis': {'score': 70}})
'''
        child = subprocess.run([sys.executable, '-c', code, str(self.path), job], cwd=ROOT,
                               capture_output=True, text=True, timeout=20)
        self.assertEqual(0, child.returncode, child.stderr)
        result = self.queue.get_job(job)
        self.assertEqual('complete', result['status'])
        self.assertEqual({'analysis': {'score': 70}}, result['result'])
        self.assertIsInstance(result['created_at'], datetime)

    def test_partial_updates_keep_the_other_workers_fields(self):
        job = self.queue.create_job()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(JobQueue(self.path).update_job, job, progress=70)
            b = pool.submit(JobQueue(self.path).update_job, job, message='Analyzing')
            self.assertTrue(a.result())
            self.assertTrue(b.result())
        result = self.queue.get_job(job)
        self.assertEqual(70, result['progress'])
        self.assertEqual('Analyzing', result['message'])
        self.assertFalse(self.queue.update_job('missing', status='complete'))
        self.assertIsNone(self.queue.get_job('missing'))

    def test_cleanup_and_delete_are_shared_and_keep_recent_jobs(self):
        old = self.queue.create_job()
        recent = self.queue.create_job()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE audio_jobs SET created_at = ? WHERE job_id = ?',
                       ((datetime.now() - timedelta(hours=25)).isoformat(), old))
        self.assertEqual(1, JobQueue(self.path).cleanup_old_jobs())
        self.assertIsNone(self.queue.get_job(old))
        self.assertIsNotNone(self.queue.get_job(recent))
        JobQueue(self.path).delete_job(recent)
        self.assertIsNone(self.queue.get_job(recent))


if __name__ == '__main__':
    unittest.main()
