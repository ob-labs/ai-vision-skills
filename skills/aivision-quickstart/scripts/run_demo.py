"""Four SDK-instrumented real requests in two sessions. Default: offline plan only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, DivisionByZero
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlencode, urlsplit
from uuid import UUID, uuid4

FIELDS = {"base_url", "space_id", "agent_uuid", "space_key", "provider_base_url", "provider_api_key", "model"}
PLAN = {"mode": "plan_only", "demo_requests": 4, "sessions": 2, "turns_per_session": 2,
        "provider_retries": 0, "request_timeout_seconds": 60, "max_tokens_per_request": 1024,
        "tool": "Actual local Decimal division: 137.1 / 3, then 137.1 / 0",
        "scope": "Synthetic tasks, real provider responses, SDK-generated observations; local orchestration chooses tools",
        "extra_calls": "Model connection test/validation and diagnosis are separate operations and costs",
        "completion": "Platform Trace and Session readback is required after this runner"}
SYSTEM = ("You are a concise AI Vision demo assistant. These are synthetic onboarding tasks with real model calls. "
          "Use at most four sentences. Use only the supplied facts and tool results. "
          "Do not claim that you inspected the environment. Explain actual tool failures honestly.")


class DemoError(Exception):
    """Fixed non-sensitive error identifiers only."""


def validate(config):
    if not isinstance(config, dict) or set(config) != FIELDS:
        raise DemoError("expected_seven_documented_config_fields")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 8192 for v in config.values()):
        raise DemoError("missing_or_invalid_config_value")
    for name in ("base_url", "provider_base_url"):
        parsed = urlsplit(config[name])
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise DemoError("invalid_base_url")
    if urlsplit(config["base_url"]).path not in ("", "/"):
        raise DemoError("platform_base_url_must_be_root_not_api_path")
    for name in ("space_id", "agent_uuid"):
        UUID(config[name])
    config["base_url"] = config["base_url"].rstrip("/")
    return config


def usage(raw):
    return {target: raw.get(source) if isinstance(raw, dict) and type(raw.get(source)) is int and raw[source] >= 0 else None
            for target, source in (("input", "prompt_tokens"), ("output", "completion_tokens"), ("total", "total_tokens"))}


def tool_step(client, denominator):
    inputs = {"numerator": "137.1", "denominator": denominator}
    with client.start_as_current_observation(name="decimal.divide", as_type="tool", input=inputs) as observation:
        try:
            result = {"ok": True, "value": str(Decimal("137.1") / Decimal(denominator))}
        except DivisionByZero:
            result = {"ok": False, "error": "division_by_zero", "error_type": "DivisionByZero"}
            observation.update(level="ERROR", status_message="DivisionByZero")
        observation.update(output=result)
    return result


def execute(config_path, output):
    config = validate(json.loads(config_path.read_text()))
    # Refuse an existing run even after interruption; inspect its ledger before any new paid attempt.
    if output.exists():
        raise DemoError("output_exists_inspect_attempt_ledger_before_new_run")
    versions = {name: importlib.metadata.version(name) for name in ("langfuse", "openai")}
    if versions != {"langfuse": "5.0.2", "openai": "2.54.0"}:
        raise DemoError("install_bundled_demo_requirements_in_isolated_venv")
    os.umask(0o077)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    secrets = (config["space_key"], config["provider_api_key"])

    def encoded(value):
        text = json.dumps(value, ensure_ascii=False, indent=2)
        if any(secret in text for secret in secrets):
            raise DemoError("secret_in_receipt_refused")
        return text + "\n"

    def checkpoint():
        # Persist a usable read window and links before every paid attempt, even if killed.
        report["to_ms"] = int(time.time() * 1000) + 120000
        scope = {"spaceId": config["space_id"], "agent": "langfuse", "agent_uuid": config["agent_uuid"],
                 "from": datetime.fromtimestamp(report["from_ms"] / 1000, timezone.utc).isoformat(),
                 "to": datetime.fromtimestamp(report["to_ms"] / 1000, timezone.utc).isoformat()}
        for request in report["requests"]:
            if request["trace_id"]:
                request["trace_url"] = config["base_url"] + "/trace?" + urlencode({**scope, "traceId": request["trace_id"]})
        report["sessions"] = [{"session_id": sid, "url": config["base_url"] + "/trace?" + urlencode(
            {**scope, "view": "session", "sessionId": sid})} for sid in dict.fromkeys(r["session_id"] for r in report["requests"])]
        report["diagnosis_url"] = config["base_url"] + "/badcase?" + urlencode(scope)
        data = encoded(report)
        temporary = output / ".run.json.tmp"
        with temporary.open("w") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        temporary.replace(output / "run.json")

    def event(value):
        value = {"at": datetime.now(timezone.utc).isoformat(), **value}
        with (output / "attempts.jsonl").open("a") as stream:
            stream.write(encoded(value).replace("\n", " ") + "\n")
            stream.flush(); os.fsync(stream.fileno())

    # Only this new demo process is changed; existing Agent and exporter settings remain untouched.
    for key in list(os.environ):
        if key.startswith(("LANGFUSE_", "OTEL_")):
            os.environ.pop(key)
    os.environ.update(LANGFUSE_BASE_URL=config["base_url"], LANGFUSE_PUBLIC_KEY=config["agent_uuid"],
                      LANGFUSE_SECRET_KEY=config["space_key"], LANGFUSE_MEDIA_UPLOAD_ENABLED="false")
    logging.disable(logging.CRITICAL)  # Avoid upstream error bodies leaking into terminal logs.
    started_ms = int(time.time() * 1000)
    run_id = "quickstart-" + uuid4().hex[:12]
    report = {"status": "running", "run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
              "base_url": config["base_url"], "space_id": config["space_id"], "agent_uuid": config["agent_uuid"],
              "model": config["model"], "sdk_versions": versions, "requests": [], "errors": [],
              "platform_readback_verified": False, "cost": None, "from_ms": started_ms - 60000}
    checkpoint()
    client = provider = None
    try:
        from langfuse import Langfuse, propagate_attributes
        from langfuse.openai import openai
        client = Langfuse(public_key=config["agent_uuid"], secret_key=config["space_key"],
                          base_url=config["base_url"], timeout=20, sample_rate=1)
        provider = openai.OpenAI(api_key=config["provider_api_key"], base_url=config["provider_base_url"],
                                timeout=60, max_retries=0)
        scenarios = {
            "welcome": ["Explain the difference between a Trace and a Session in two sentences.",
                        "Using our previous turn, suggest one thing I can inspect in each view. Do not claim you inspected them."],
            "calculator": ["Explain 137.1 divided by 3 using the actual tool result supplied below.",
                           "Now explain 137.1 divided by zero using the actual tool result. Ask how to correct the input."],
        }
        for kind, prompts in scenarios.items():
            session_id = run_id + "-" + kind
            messages = [{"role": "system", "content": SYSTEM}]
            for turn, prompt in enumerate(prompts, 1):
                request = {"session_id": session_id, "kind": kind, "turn": turn,
                           "status": "preparing", "trace_id": None, "tool": None}
                report["requests"].append(request)
                # Propagate outside the root so root, generation and tool share the Session.
                with propagate_attributes(session_id=session_id, tags=["aivision-quickstart", "synthetic-task"]):
                    with client.start_as_current_observation(name=f"quickstart.{kind}.{turn}", as_type="agent",
                                                             input=prompt) as root:
                        request["trace_id"] = client.get_current_trace_id()
                        if not request["trace_id"]:
                            raise DemoError("sdk_trace_not_created")
                        if kind == "calculator":
                            request["tool"] = tool_step(client, "3" if turn == 1 else "0")
                            prompt += "\nActual local tool result: " + json.dumps(request["tool"])
                            if not request["tool"]["ok"]:
                                root.update(level="WARNING", status_message="Handled demo tool failure")
                        messages.append({"role": "user", "content": prompt})
                        request.update(status="provider_attempted", input=prompt)
                        checkpoint()
                        event({"event": "provider_attempt_started", **request})
                        began = time.monotonic()
                        try:
                            response = provider.chat.completions.create(model=config["model"], messages=messages,
                                stream=False, max_tokens=1024, name=f"quickstart-{kind}-{turn}")
                        except Exception as error:
                            request.update(status="provider_failed", error_type=type(error).__name__,
                                           http_status=getattr(error, "status_code", None))
                            event({"event": "provider_attempt_failed", **request})
                            raise DemoError("provider_failed_no_retry") from None
                        text = response.choices[0].message.content if response.choices else None
                        raw_usage = response.usage.model_dump(mode="json") if response.usage else None
                        request.update(status="completed" if isinstance(text, str) and text.strip() else "empty_output",
                                       output=text, response_model=response.model, usage=usage(raw_usage), usage_raw=raw_usage,
                                       elapsed_seconds=round(time.monotonic() - began, 3))
                        event({"event": "provider_attempt_completed", **request})
                        root.update(output=text)
                        checkpoint()
                        if request["status"] != "completed":
                            raise DemoError("empty_provider_output_no_retry")
                        messages.append({"role": "assistant", "content": text})
        report["status"] = "completed_pending_readback"
    except Exception as error:
        report["status"] = "failed"
        report["errors"].append(str(error) if isinstance(error, DemoError) else type(error).__name__)
    finally:
        if client is not None:
            for action in (client.flush, client.shutdown):
                try:
                    if action() is False:
                        raise DemoError("sdk_flush_failed")
                except Exception as error:
                    report["status"] = "failed"
                    report["errors"].append(type(error).__name__)
        if provider is not None:
            provider.close()
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        checkpoint()
    print(json.dumps({"status": report["status"], "demo_attempts": sum(r["status"] != "preparing" for r in report["requests"]),
                      "run_file": str(output / "run.json"), "platform_readback_verified": False}))
    return 0 if report["status"] == "completed_pending_readback" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(PLAN, indent=2)); return 0
    if args.config is None or args.out is None:
        parser.error("--execute requires --config and a new --out directory")
    try:
        return execute(args.config, args.out)
    except Exception as error:
        print(json.dumps({"status": "failed", "error": str(error) if isinstance(error, DemoError) else type(error).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
