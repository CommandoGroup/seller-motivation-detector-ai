"""Run the audio-status regression and its deliberate process-isolation negative."""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
source = ROOT / 'job_queue.py'
original = source.read_bytes()
positive = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT)
if positive.returncode:
    sys.exit(positive.returncode)
text = original.decode('utf-8')
line = next(line for line in text.splitlines() if line.strip().startswith('self.path = os.fspath('))
changed = text.replace(line, line + '\n        self.path += "." + str(os.getpid())', 1)
try:
    source.write_text(changed, encoding='utf-8')
    negative = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_job_queue.py',
                               '-k', 'second_worker_process'], cwd=ROOT, capture_output=True, text=True)
finally:
    source.write_bytes(original)
restored = source.read_bytes() == original
result = {'positive_exit': positive.returncode, 'negative_exit': negative.returncode,
          'negative': 'isolate job storage by worker process', 'restored_byte_identical': restored,
          'source_sha256': hashlib.sha256(original).hexdigest()}
if len(sys.argv) > 1:
    pathlib.Path(sys.argv[1]).write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
sys.exit(0 if negative.returncode == 1 and restored else 1)
