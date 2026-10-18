"""Regression: Anna stdio must remain UTF-8 under Windows-style code pages."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1] / 'executas' / 'career-engine-python' / 'career_engine_plugin.py'

class TestUtf8Protocol(unittest.TestCase):
    def test_utf8_json_despite_legacy_stdio_encoding(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, PYTHONIOENCODING='cp1252', HOME=home, USERPROFILE=home)
            role = 'Ingénieur – Python'
            requests = [
                {'jsonrpc':'2.0','id':1,'method':'health'},
                {'jsonrpc':'2.0','id':2,'method':'invoke','params':{'tool':'career','arguments':{
                    'action':'analyze', 'role_title':role,
                    'resume_text':'Built Python services for weekly sales reports.',
                    'job_description':'Python SQL Docker'}}},
                {'jsonrpc':'2.0','id':3,'method':'invoke','params':{'tool':'career','arguments':{'action':'get_state'}}},
            ]
            raw = ('\n'.join(json.dumps(r, ensure_ascii=False) for r in requests)+'\n').encode('utf-8')
            result = subprocess.run([sys.executable, '-u', str(PLUGIN)], input=raw, capture_output=True, env=env, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
            responses = [json.loads(line) for line in result.stdout.decode('utf-8').splitlines()]
            self.assertEqual(len(responses), 3)
            self.assertEqual(responses[0]['result']['status'], 'ready')
            self.assertTrue(responses[1]['result']['success'])
            self.assertEqual(responses[1]['result']['data']['scan']['role_title'], role)
            self.assertEqual(responses[2]['result']['data']['active_scan']['role_title'], role)
