# Run a live standalone demo

Use this workflow when the user wants the coding Agent to run a live test.
The deployed product's walkthrough and onboarding examples are the entry
points for exploring sample data or integrating an existing application.

## 1. Establish the instance and model

Use the user's existing platform and confirm its installed version in
**Help → About**. Use a URL reachable from the demo host. For simultaneous
local platforms, use distinct allowed hostnames such as `127.0.0.1` and
`localhost` so browser cookies remain isolated. If an instance needs to be
installed first, use the
[deployment Skill](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-deploy).

Create an account at `/register` when self-registration is enabled, or sign
in at `/login`. Registration signs the user in and creates a personal Space.
To use a team Space, accept its invitation and select it in AI Vision.
Use the browser for setup and Trace readback. [CLI readback](#3-verify-trace-and-session-before-diagnosis)
is also available with a compatible `aiv` and a query SpaceKey.

For model-backed diagnosis, open **Model connections** at
`/model-connections?spaceId=<SPACE_UUID>`. Reuse a matching connection or
create a clearly named demo connection using the user's private API base URL,
model ID and key. For providers without a preset, select
**Custom · OpenAI compatible** and enter the provider's model ID. The standalone
runner reads the provider credentials from its own private config. Trace
collection and rule-only diagnosis can proceed without a saved model connection.

When setting up a model connection, run **Test connection** once within the
requested call budget and read back the result. It makes a real model request.
Optional **Validate model** uses up to two additional tests for structured
output and citation capability. Verify actual diagnosis separately and retain
errors from failed probes.

If API automation is available, the platform account Cookie + CSRF APIs are:

| Operation | Route under `/api/v1/spaces/<SPACE_UUID>/diagnose` |
|---|---|
| List/create | `GET/POST /model-connections` |
| Read/update | `GET/PATCH /model-connection/<UUID>` |
| Test | `POST /model-connection/<UUID>/test` with `{}` |

Create fields: `name`, `endpoint`, `model_name`, `api_key`. Model management needs
`model_connection.manage`; the saved API key is write-only. Use the public
platform, not internal SigNoz/AgentLens credentials. Use same-Space connection
UUIDs; listings and update responses must not reveal the write-only key. On
authorization or connection-test failure, preserve the error and correct that
access or endpoint instead of copying another workload's credentials.

## 2. Create a test Agent and private demo directory

For the bundled demo choose **Langfuse → Python → OpenAI** from
`/access` in the selected Space and create or select a dedicated test project
with product `langfuse`. Read the deployed version's configuration at
`/access/langfuse-onboarding`. For other languages and frameworks, use the
platform's example for the selected integration.
For API automation the create route is
`POST /api/v1/spaces/<SPACE_UUID>/agents/create` with
`{"agent_product":"langfuse","name":"AI Vision Quickstart"}`.
Obtain a same-Space SpaceKey through the onboarding wizard. Creating a key
requires `space.key.manage`; a list of masked keys cannot recover the original.
Reuse a privately available key or create one with authorization. Do not rotate
or revoke a key used by an existing application.

| Demo config | Meaning |
|---|---|
| `base_url` | AI Vision root URL, corresponding to `LANGFUSE_BASE_URL` |
| `space_id` | The selected Space UUID |
| `agent_uuid` | Test Agent UUID, corresponding to `LANGFUSE_PUBLIC_KEY` |
| `space_key` | Same-Space SpaceKey, corresponding to `LANGFUSE_SECRET_KEY` |
| `provider_base_url` | The user's API base for OpenAI-compatible Chat Completions |
| `provider_api_key` | The provider key, separate from the platform SpaceKey |
| `model` | The selected actual model ID |

Choose a private `DEMO_DIR` outside the repository and create it with mode
`0700`. Save the seven string fields as `private.json` with mode `0600`.
Fill keys from a private input supplied for this run and keep them out of
command arguments and output. Run the demo in a standalone process to keep
its SDK and exporter settings separate from the user's application.

Set `SKILL_ROOT` to the installed Skill directory. Use Python 3.11 or later
to create an isolated environment and view the offline plan:

```sh
: "${SKILL_ROOT:?Set the installed aivision-quickstart directory}" \
  "${DEMO_DIR:?Set the private demo directory}"
python3 -m venv "$DEMO_DIR/.venv"
"$DEMO_DIR/.venv/bin/python" -m pip install -r "$SKILL_ROOT/scripts/requirements.txt"
"$DEMO_DIR/.venv/bin/python" "$SKILL_ROOT/scripts/run_demo.py"
```

Once the user authorizes the real model calls, run the demo with a new output
directory:

```sh
"$DEMO_DIR/.venv/bin/python" "$SKILL_ROOT/scripts/run_demo.py" --execute \
  --config "$DEMO_DIR/private.json" --out "$DEMO_DIR/run-1"
```

The dependency pins apply to this standalone example. A complete run sends four
non-streaming requests with a 60-second timeout, a 1024-token output limit and
zero provider retries. The last two requests use local Decimal calculations,
including a handled division by zero. The script selects and runs the tool
locally. It records reported Token usage and leaves missing usage or cost
unknown.

`run.json` and `attempts.jsonl` preserve private inputs/outputs, SDK versions,
real IDs and the time window. Their existence does not prove ingestion.
An existing run directory is refused, including after interruption. Inspect
started/finished attempts and first confirm whether the old process is still
running. Every checkpoint preserves numeric read bounds, browser links and
timestamped events even if the process is killed. Freeze a later read-only end
bound if needed; do not rerun the provider to discover an uncertain outcome. A
timeout can still have incurred cost. Fix the
specific problem and obtain any needed expanded retry scope before a new run.

## 3. Verify Trace and Session before diagnosis

Read `run.json` privately and use its exact IDs, `from_ms` and `to_ms`. Allow a
bounded ingestion delay (for example, poll reads for up to 120 seconds) without
sending more model requests. In the UI use the selected Space and test Agent:

- Trace: `/trace?spaceId=<S>&agent=langfuse&agent_uuid=<A>&traceId=<T>&from=<ISO_UTC>&to=<ISO_UTC>`.
- Session: the same route with `view=session&sessionId=<ID>`.

The runner supplies browser links with ISO dates, plus a diagnosis link.
For a complete run, verify four Traces and two Sessions with two Traces each.
Inspect the model and tool calls, their parentage, inputs, outputs, the handled
tool error, and reported usage. For a partial run, inspect the attempted
requests and report any missing records. Treat native `null` usage and legacy
v1 integer placeholders as unknown.

For optional CLI readback, use a compatible `aiv`. Follow the
[installation guide](install-cli.md) if needed. Set `ENDPOINT` and `SPACE_ID` to
the instance and Space from the run, use `AGENT_PRODUCT=langfuse`, and follow the
[query profile setup](query-setup.md) to verify the profile and its SpaceKey.
Check the installed commands' help. Pass the recorded bounds in epoch
milliseconds as detail parameters:

```sh
: "${PROFILE:?Set the verified query profile}" \
  "${TRACE_ID:?Select an ID from run.json}" "${SESSION_ID:?Select an ID from run.json}" \
  "${AGENT_UUID:?Set the test Agent UUID}" "${FROM_MS:?Use run.json from_ms}" \
  "${TO_MS:?Use run.json to_ms}"
aiv query trace get "$TRACE_ID" --profile "$PROFILE" --agent-product langfuse \
  --param agent_uuid="$AGENT_UUID" --param from="$FROM_MS" --param to="$TO_MS" --format json
aiv query session get "$SESSION_ID" --profile "$PROFILE" --agent-product langfuse \
  --param agent_uuid="$AGENT_UUID" --param from="$FROM_MS" --param to="$TO_MS" --format json
```

Do not replace detail bounds with `--since/--until`; those shortcuts are not
forwarded by the current detail commands. SDK flush, HTTP acceptance and a
nonempty dashboard alone do not prove this run's persistence.

## 4. Run one diagnosis and hand over

When diagnosis is requested or part of the chosen evaluation, open
`/badcase?spaceId=<S>&agent=langfuse&agent_uuid=<A>` and use Quick Diagnosis
for the exact generated Trace IDs. This needs `diagnosis.execute`, an Agent bound
to the account, and an enabled native SigNoz datasource. Langfuse SDK ingestion
into native storage qualifies; an external Langfuse datasource is a different
capability. Use the live options, not assumed detector names:

`GET /api/v1/spaces/<S>/diagnose/quick-runs/options?agent_uuid=<A>`.

Choose `conversation_qa` / `task_completion` with the selected model connection
for an LLM quality example and available `tool_success` / `total_latency` Rules.
A Rule-only `quick_runtime` run is available when the user wants to avoid Judge
calls; it does not assess answer quality. Do not select grounding without real
source materials supplied to the model, or use a coding-delivery scene for this
small chat/tool demo. A live option that is unavailable must remain unavailable.

For a model-backed example, API automation posts to
`/api/v1/spaces/<S>/diagnose/quick-runs?agent_uuid=<A>`.

```json
{
  "request_id": "<new UUID persisted before submitting>",
  "trace_ids": ["<actual generated Trace IDs>"],
  "builtin_keys": ["task_completion", "tool_success", "total_latency"],
  "scene_key": "conversation_qa",
  "model_connection_uuid": "<the selected same-Space connection UUID>"
}
```

Use only keys returned by live options. Core Quick accepts at most 10 Traces and
one LLM Core; it can make additional Judge attempts within its server budget
(up to 30 per task, 3 per case). Connection probes/validation and this Judge work
are not included in the runner's four business requests. Preserve request ID and
body before POST. On `provisioning` honor `retry_after_seconds`; after an uncertain
response retry the **same** ID/body, not a new job. Persist accepted job/task IDs,
poll the task, then read its records and evidence. A timeout is unresolved,
not permission to submit a second paid diagnosis.

Tasks: `GET /api/v1/spaces/<S>/diagnose/tasks/<TASK>?agent_uuid=<A>`.
Records: `GET /api/v1/spaces/<S>/diagnose/records?job_uuid=<JOB>&task_uuid=<TASK>&agent_uuid=<A>`,
then each `/records/<RECORD_UUID>` in the same diagnosis prefix.
Check task terminal state, source completeness and per-record execution,
metrics/evidence and skips. `model_parse_error` is an execution failure;
`missing_required_evidence`, `privacy_redacted` and not-applicable skips are not
GOOD verdicts. Never force expected GOOD/BAD counts or hide failure records.
A completed task with failed records is a **partial diagnostic result**.

Leave authorized demo resources for manual review. Deliver the platform
version, model (and saved connection when used), test Agent, actual request,
Trace and Session counts, verified links and inspection window. Include the
successful call and handled tool error that were read back, and report diagnosis
task and record outcomes if diagnosis ran. Keep credentials, session cookies and
private reports out of shared output.
For long-term work connect the user's existing Agent using its own onboarding
path; do not replace it with the demo.
