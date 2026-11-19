#!/usr/bin/env python3
"""Send a synthetic trace to a loopback All-in-One preview."""

import argparse
import getpass
import http.cookiejar
import json
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import warnings


SPACE_NAME = "All-in-One Sample"
SPACE_DESCRIPTION = "Synthetic traces created by the AI Vision All-in-One sample installer."
AGENT_NAME = "All-in-One Sample Agent"
AGENT_PRODUCT = "Codex"
SPAN_NAMES = (
    "Sample: answer a shipping question",
    "Sample: look up an order",
    "Sample: draft a reply",
)
SAMPLE_PROMPT = "When will sample order DEMO-104 arrive?"
SAMPLE_REPLY = "Sample order DEMO-104 was shipped and is expected to arrive tomorrow."


class SampleError(RuntimeError):
    def __init__(self, message, *, http_status=None, api_code=None):
        super().__init__(message)
        self.http_status = http_status
        self.api_code = api_code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def open_loopback(*handlers):
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(), *handlers)


def request_json(opener, origin, path, *, headers=None, method=None, body=None):
    request = urllib.request.Request(
        origin + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Accept": "application/json", "Content-Type": "application/json", **(headers or {})},
        method=method,
    )
    label = f"{request.get_method()} {path.split('?')[0]}"
    try:
        with opener.open(request, timeout=10) as response:
            raw = response.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raise SampleError(f"{label} returned HTTP {error.code}.", http_status=error.code) from None
    except (OSError, ValueError):
        raise SampleError(f"{label} did not return usable JSON. Check the loopback ports.") from None


class Platform:
    def __init__(self, origin):
        self.origin = origin
        self.cookies = http.cookiejar.CookieJar()
        self.opener = open_loopback(urllib.request.HTTPCookieProcessor(self.cookies))

    def api(self, path, *, body=None, method=None):
        csrf = next((cookie.value for cookie in self.cookies if cookie.name == "csrftoken"), "")
        payload = request_json(
            self.opener, self.origin, "/api/v1" + path, method=method, body=body,
            headers={"Origin": self.origin, "Referer": self.origin + "/", "X-CSRFToken": csrf},
        )
        if payload.get("code") != 0:
            raise SampleError(f"AI Vision rejected {path.split('?')[0]}.", api_code=payload.get("code"))
        return payload.get("data")


def sample_payload(trace_id):
    start = time.time_ns() - 1_000_000_000
    root_id = secrets.token_hex(8)
    conversation = {
        "gen_ai.input.messages": json.dumps([{"role": "user", "content": SAMPLE_PROMPT}]),
        "gen_ai.output.messages": json.dumps([{"role": "assistant", "content": SAMPLE_REPLY}]),
    }
    tool = {
        "gen_ai.tool.name": "sample_order_lookup",
        "gen_ai.tool.call.arguments": json.dumps({"order_id": "DEMO-104"}),
        "gen_ai.tool.call.result": json.dumps({"status": "shipped", "estimated_delivery": "tomorrow"}),
    }
    spans = []
    steps = ((0, 180, "AGENT", conversation), (10, 40, "TOOL", tool), (70, 90, "CHAIN", {}))
    for index, (name, (offset, duration, kind, details)) in enumerate(zip(SPAN_NAMES, steps)):
        attributes = [{"key": key, "value": {"stringValue": value}}
                      for key, value in {"gen_ai.span.kind": kind, **details}.items()]
        attributes.append({"key": "aivision.sample", "value": {"boolValue": True}})
        span = {
            "name": name, "traceId": trace_id, "kind": 1,
            "spanId": secrets.token_hex(8) if index else root_id,
            "startTimeUnixNano": str(start + offset * 1_000_000),
            "endTimeUnixNano": str(start + (offset + duration) * 1_000_000),
            "status": {"code": 1},
            "attributes": attributes,
        }
        if index:
            span["parentSpanId"] = root_id
        spans.append(span)
    return {"resourceSpans": [{
        "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "aivision-aio-sample"}}]},
        "scopeSpans": [{"scope": {"name": "aivision-aio-sample"}, "spans": spans}],
    }]}


def wait_for_trace(platform, space_path, agent_id, trace_id):
    query = urllib.parse.urlencode({"agent_product": AGENT_PRODUCT, "agent_uuid": agent_id, "detail": "1"})
    path = f"{space_path}/signoz/trace/{trace_id}/detail?{query}"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            detail = platform.api(path)
        except SampleError as error:
            if error.http_status != 404 and error.api_code not in (3019, 3035):
                raise
        else:
            spans = detail.get("spans", []) if detail else []
            if detail and detail.get("traceId") == trace_id and {s.get("name") for s in spans} == set(SPAN_NAMES):
                return
        time.sleep(1)
    raise SampleError("AI Vision accepted the sample, but its Trace did not become readable within 60 seconds.")


def create_sample(web_port, otlp_port, email, password):
    origin = f"http://127.0.0.1:{web_port}"
    platform = Platform(origin)
    platform.api("/auth/csrf")
    try:
        platform.api("/auth/login", body={"email": email, "password": password})
    except SampleError as error:
        raise SampleError(
            f"Could not sign in. Use {origin}/register for a new account or {origin}/login to check sign-in."
        ) from error

    spaces = platform.api("/spaces")["items"]
    sample_space = next((space for space in spaces if (
        space.get("is_owner") is True and space.get("member_count") == 1
        and space.get("name") == SPACE_NAME and space.get("description") == SPACE_DESCRIPTION
    )), None)
    if sample_space is None:
        sample_space = platform.api("/spaces", body={"name": SPACE_NAME, "type": 2,
                                                    "description": SPACE_DESCRIPTION})
    space_id = sample_space["space_id"]
    space_path = "/spaces/" + urllib.parse.quote(space_id, safe="")
    agent = platform.api(space_path + "/agents/create", body={"agent_product": AGENT_PRODUCT, "name": AGENT_NAME})
    agent_id = agent["agent_uuid"]
    if agent.get("name") != AGENT_NAME and agent.get("custom_name") != AGENT_NAME:
        raise SampleError(f"The {SPACE_NAME} workspace already has a different Codex Agent.")

    key_id = platform.api(space_path + "/space-keys", body={"name": "All-in-One one-time sample"})["id"]
    key_path = f"{space_path}/space-keys/{key_id}"
    trace_id = secrets.token_hex(16)
    try:
        token = platform.api(key_path + "/ingest-token", body={"agent_uuid": agent_id, "ttl_seconds": 120})["token"]
        result = request_json(
            open_loopback(), f"http://127.0.0.1:{otlp_port}", "/v1/traces",
            headers={"Authorization": "Bearer " + token}, body=sample_payload(trace_id),
        )
        partial = result.get("partialSuccess") or result.get("partial_success") or {}
        if int(partial.get("rejectedSpans", partial.get("rejected_spans", 0))):
            raise SampleError("The local Collector rejected part of the sample Trace.")
    finally:
        try:
            platform.api(key_path, method="DELETE")
        except SampleError:
            print(f"Could not remove the one-time sample key. Remove key {key_id} in {SPACE_NAME} settings.",
                  file=sys.stderr)

    wait_for_trace(platform, space_path, agent_id, trace_id)
    query = urllib.parse.urlencode({
        "spaceId": space_id, "agent": AGENT_PRODUCT, "agent_uuid": agent_id,
        "traceId": trace_id, "source_system": "signoz",
    })
    return f"{origin}/trace?{query}"


def port(value):
    number = int(value)
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-port", type=port, default=5174)
    parser.add_argument("--otlp-port", type=port, default=4318)
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.error("Run the sample from an interactive terminal to enter your local account password safely.")
    print(f"Use your AI Vision account from http://127.0.0.1:{args.web_port}. The sample uses no model.")
    try:
        email = input("AI Vision email: ").strip()
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("AI Vision password: ")
        url = create_sample(args.web_port, args.otlp_port, email, password)
    except (EOFError, KeyboardInterrupt):
        parser.exit(1, "Sample Trace cancelled.\n")
    except getpass.GetPassWarning:
        parser.exit(1, "Sample Trace requires a terminal that can hide password input.\n")
    except SampleError as error:
        parser.exit(1, f"Sample Trace: {error}\n")
    except (AttributeError, KeyError, TypeError, ValueError):
        parser.exit(1, "Sample Trace: the local API returned an unsupported response.\n")
    print(f"Open the synthetic sample Trace in your browser:\n{url}")


if __name__ == "__main__":
    main()
