import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from content_planner.models import CodexModel, ModelError


class CodexAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.executable = Path(self.tmp.name) / "fake-codex"
        self.executable.write_text('''#!/usr/bin/env python3
import json,os,pathlib,sys
if '--version' in sys.argv:
    print('test-double-cli');sys.exit(0)
assert '--ignore-user-config' in sys.argv
assert 'CODEX_THREAD_ID' not in os.environ
assert 'CODEX_APP_TOOLS_PIPE_PATH' not in os.environ
request=json.loads(sys.stdin.read().split('当前请求和全部实际观察：\\n')[1])
assert 'faults_remaining' not in request
action={'tool':'search_assets','arguments_json':json.dumps({'query':'剪辑'}),'reason':'仅测试结构化动作适配'}
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(action))
print(json.dumps({'type':'item.completed','item':{'type':os.environ.get('ADAPTER_TEST_ITEM','agent_message')}}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}))
''', encoding="utf-8")
        self.executable.chmod(0o755)
        self.state = {"request": {"topic": "剪辑"}, "calls": [], "faults_remaining": {"save_plan": 10}}

    def tearDown(self):
        self.tmp.cleanup()

    def test_app_context_removed_and_structured_action_parsed(self):
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "must-not-inherit", "CODEX_APP_TOOLS_PIPE_PATH": "must-not-inherit"}):
            model = CodexModel(executable=str(self.executable))
            action, info = model.decide(self.state)
        self.assertEqual(action["tool"], "search_assets")
        self.assertEqual(action["arguments"], {"query": "剪辑"})
        self.assertEqual(info["version"], "test-double-cli")
        self.assertEqual(info["usage"]["input_tokens"], 1)

    def test_cli_side_tool_execution_is_rejected(self):
        with patch.dict(os.environ, {"ADAPTER_TEST_ITEM": "command_execution"}):
            model = CodexModel(executable=str(self.executable))
            with self.assertRaises(ModelError):
                model.decide(self.state)

    def test_explicit_model_and_auth_location_kept_without_printing_credentials(self):
        with patch.dict(os.environ, {"CODEX_HOME": "/test-only-location", "CODEX_MODEL": "configured-test-model", "CODEX_SESSION_ID": "private-app-context"}):
            model = CodexModel(executable=str(self.executable))
        self.assertEqual(model.model, "configured-test-model")
        self.assertEqual(model.env["CODEX_HOME"], "/test-only-location")
        self.assertNotIn("CODEX_SESSION_ID", model.env)
        self.assertNotIn("/test-only-location", json.dumps(model.info))

    def test_invalid_timeout_fails_before_launch(self):
        with self.assertRaises(ModelError):
            CodexModel(timeout=0)


if __name__ == "__main__":
    unittest.main()
