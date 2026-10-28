"""Exercise the real SDK against local fixture HTTP servers; no paid model calls."""
import base64
from datetime import datetime
from contextlib import contextmanager
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from urllib.parse import parse_qs, urlsplit
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_demo.py"
AGENT = "10000000-0000-4000-8000-000000000001"
SPACE = "20000000-0000-4000-8000-000000000002"


@contextmanager
def fixture(provider_error=False, pause_provider=False):
    state = {"calls": [], "exports": [], "auth": [], "entered": threading.Event(), "release": threading.Event()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            if self.path == "/model/v1/chat/completions":
                body = json.loads(raw)
                state["calls"].append(body)
                if pause_provider:
                    state["entered"].set()
                    state["release"].wait(10)
                status = 500 if provider_error else 200
                result = {"error": {"message": "private fixture error"}} if provider_error else {
                    "id": "fixture-response", "object": "chat.completion", "created": 1,
                    "model": "fixture-model", "choices": [{"index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "A real fixture HTTP response."}}],
                    "usage": {"prompt_tokens": 17, "completion_tokens": 9, "total_tokens": 26},
                }
                data = json.dumps(result).encode()
            elif self.path == "/api/public/otel/v1/traces":
                state["auth"].append(self.headers.get("Authorization"))
                state["exports"].append(gzip.decompress(raw) if self.headers.get("Content-Encoding") == "gzip" else raw)
                status, data = 200, b""
            else:
                status, data = 404, b"{}"
            self.send_response(status)
            self.send_header("Content-Type", "application/json" if self.path.startswith("/model") else "application/x-protobuf")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except BrokenPipeError:
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", state
    finally:
        state["release"].set()
        server.shutdown()
        server.server_close()
        thread.join()


def invoke(*args):
    env = os.environ.copy()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(key, None)
    # The standalone demo must not inherit a disabled or unrelated exporter.
    env.update(OTEL_SDK_DISABLED="true", LANGFUSE_BASE_URL="https://invalid.example")
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], env=env,
                          text=True, capture_output=True, timeout=40)


class DemoTests(unittest.TestCase):
    def config(self, root, origin):
        path = root / "private.json"
        path.write_text(json.dumps({"base_url": origin, "space_id": SPACE, "agent_uuid": AGENT,
                                  "space_key": "fixture-space-secret", "provider_base_url": origin + "/model/v1",
                                  "provider_api_key": "fixture-provider-secret", "model": "fixture-model"}))
        path.chmod(0o600)
        return path

    def test_default_plan_does_not_read_config_or_create_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = invoke("--config", root / "missing.json", "--out", root / "run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["mode"], "plan_only")
            self.assertFalse((root / "run").exists())

    def test_sdk_exports_four_requests_two_sessions_and_real_tool_error(self):
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
        with tempfile.TemporaryDirectory() as tmp, fixture() as (origin, state):
            root = Path(tmp); output = root / "run"
            result = invoke("--execute", "--config", self.config(root, origin), "--out", output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / "run.json").read_text())
            self.assertEqual(report["status"], "completed_pending_readback")
            self.assertFalse(report["platform_readback_verified"])
            self.assertEqual(len(state["calls"]), 4)
            self.assertEqual(len(report["requests"]), 4)
            browser_query = parse_qs(urlsplit(report["requests"][0]["trace_url"]).query)
            self.assertEqual(int(datetime.fromisoformat(browser_query["from"][0]).timestamp() * 1000), report["from_ms"])
            sessions = {r["session_id"] for r in report["requests"]}
            self.assertEqual(len(sessions), 2)
            self.assertTrue(all(sum(r["session_id"] == sid for r in report["requests"]) == 2 for sid in sessions))
            self.assertTrue(all(r["usage"]["total"] == 26 for r in report["requests"]))
            self.assertEqual(report["requests"][-1]["tool"]["error_type"], "DivisionByZero")
            self.assertIn("division_by_zero", state["calls"][-1]["messages"][-1]["content"])
            self.assertEqual(len(state["calls"][1]["messages"]), 4)
            self.assertTrue(all(c["stream"] is False and c["max_tokens"] == 1024 for c in state["calls"]))
            spans = []
            for raw in state["exports"]:
                exported = ExportTraceServiceRequest.FromString(raw)
                spans.extend(span for resource in exported.resource_spans for scope in resource.scope_spans for span in scope.spans)
            self.assertEqual(len(spans), 10)
            for request in report["requests"]:
                own = [s for s in spans if s.trace_id.hex() == request["trace_id"]]
                roots = [s for s in own if not s.parent_span_id]
                self.assertEqual(len(roots), 1)
                self.assertTrue(all(not s.parent_span_id or s.parent_span_id == roots[0].span_id for s in own))
                for span in own:
                    attrs = {a.key: a.value.string_value for a in span.attributes}
                    self.assertEqual(attrs["session.id"], request["session_id"])
            expected_auth = "Basic " + base64.b64encode((AGENT + ":fixture-space-secret").encode()).decode()
            self.assertTrue(state["auth"] and all(a == expected_auth for a in state["auth"]))
            private_report = (output / "run.json").read_text() + (output / "attempts.jsonl").read_text()
            self.assertNotIn("fixture-space-secret", private_report)
            self.assertNotIn("fixture-provider-secret", private_report)
            self.assertEqual((output / "run.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)

    def test_provider_failure_is_not_retried_and_run_cannot_be_replayed(self):
        with tempfile.TemporaryDirectory() as tmp, fixture(provider_error=True) as (origin, state):
            root = Path(tmp); output = root / "run"; config = self.config(root, origin)
            result = invoke("--execute", "--config", config, "--out", output)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(len(state["calls"]), 1)
            report = json.loads((output / "run.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["requests"][0]["status"], "provider_failed")
            self.assertNotIn("private fixture error", result.stdout + result.stderr)
            second = invoke("--execute", "--config", config, "--out", output)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(len(state["calls"]), 1)

    def test_hard_interruption_retains_readback_bounds_and_attempt_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp, fixture(pause_provider=True) as (origin, state):
            root = Path(tmp); output = root / "run"; config = self.config(root, origin)
            env = os.environ.copy()
            for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
                env.pop(key, None)
            process = subprocess.Popen([sys.executable, str(SCRIPT), "--execute", "--config", str(config),
                                        "--out", str(output)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                self.assertTrue(state["entered"].wait(10), "provider request never started")
                process.kill()
                process.communicate(timeout=5)
                report = json.loads((output / "run.json").read_text())
                ledger = [json.loads(line) for line in (output / "attempts.jsonl").read_text().splitlines()]
                self.assertEqual(report["requests"][0]["status"], "provider_attempted")
                self.assertIsInstance(report["from_ms"], int)
                self.assertGreater(report["to_ms"], report["from_ms"])
                self.assertTrue(report["requests"][0]["trace_url"])
                self.assertTrue(datetime.fromisoformat(ledger[0]["at"]))
                self.assertEqual(len(state["calls"]), 1)
            finally:
                if process.poll() is None:
                    process.kill(); process.communicate(timeout=5)
                state["release"].set()

    def test_missing_secret_does_not_issue_requests(self):
        with tempfile.TemporaryDirectory() as tmp, fixture() as (origin, state):
            root = Path(tmp); config = self.config(root, origin)
            data = json.loads(config.read_text()); data["provider_api_key"] = ""; config.write_text(json.dumps(data))
            result = invoke("--execute", "--config", config, "--out", root / "run")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(state["calls"])
            self.assertFalse((root / "run").exists())


if __name__ == "__main__":
    unittest.main()
