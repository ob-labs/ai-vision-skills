---
name: aivision-quickstart
description: Use when a user wants a first hands-on AI Vision experience, an empty installation needs a test Agent, or real model requests are needed to explore Trace, Session and diagnosis before connecting an existing application.
---

# AI Vision Quickstart

Help a user experience their own AI Vision installation with a small test Agent.
Reuse an existing instance; if there is none, follow the
[deployment Skill](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-deploy)
to deploy and verify the requested Release/Daily first. Installing this Skill
alone does not install the platform, its CLI or the Python demo dependencies.

The default outcome is a configured model connection, a test Agent, **four real model
requests in two two-turn Sessions**, readable Traces and a persisted diagnosis
with honest per-record results. Use the user's chosen provider. Baidu Token Plan
is one example, not a bundled account or a required provider.

## Run the experience

Read [the workflow](reference/workflow.md) for the actual routes, credential
mapping, commands, readback and diagnosis contract, then:

1. Establish the reachable platform URL, actual installed version, authorized
   account/Space and a private source for model endpoint/model ID/API key.
   Keep known choices and existing services. Ask only for missing inputs;
   never request a key pasted into chat. Honor a smaller explicit call budget
   through an adapted onboarding example rather than forcing the four-call runner.
   No available key means stop before
   paid calls rather than substituting fixture data and calling it real.
2. Reuse or create the selected Space's model connection and run one connection
   test. Open the Langfuse onboarding page and create or reuse a **dedicated
   test Agent**. Obtain its Agent UUID and same-Space SpaceKey. A saved model
   connection does not reveal its API key to the local demo; the provider key
   and the SpaceKey are separate inputs.
3. Set up the bundled [Python demo](scripts/run_demo.py) in a private directory
   outside a source checkout, using [its package pins](scripts/requirements.txt).
   The default command is offline plan-only. An authorized real-request task
   uses `--execute --config <private.json> --out <new-run-directory>`; it does not
   need another routine confirmation. The runner makes at most four business
   calls, with zero provider retries, and records attempts before sending them.
   Connection tests, optional model validation and LLM diagnosis are **additional
   calls/costs**. Inspect an interrupted/failed run before any new paid run;
   never silently change provider/model or create another attempt directory.
4. Read back the exact generated Trace IDs and both Session IDs in the same
   Space/Agent and recorded time window. Verify actual inputs, outputs, usage
   and parent/child relationships, including the real local tool error.
   `completed_pending_readback` and SDK flush are not platform persistence proof.
5. Run one supported Quick Diagnosis on those exact Traces. Use live options,
   the selected model connection and one persisted request ID; retain the same
   body/ID on an uncertain submission. Check task **and record** outcomes.
   Failed, skipped and missing-evidence records remain visible; task success
   does not turn them into successful diagnoses or justify repeated paid runs.
6. Leave the demo, connection, credentials and results available for the user.
   Give working Trace, Session, model-connection and diagnosis links, a short
   click-through itinerary, actual request counts/usage and remaining limits.
   Do not revoke keys, delete data or change an existing Agent's configuration
   as routine cleanup. Do not claim zero cost, general model quality, or that
   a handled example tool failure proves every detector will flag it.

The demo uses the official Langfuse OpenAI wrapper and public SDK observations.
It runs actual local Decimal tools under deterministic orchestration; it does
not implement model-selected tool calling, hand-write OTLP or require a Langfuse
Server. Existing applications should keep their compatible SDK and use their
onboarding example; these package pins are for the isolated demo only.

For later analysis of existing telemetry, use
[aivision-trace](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-trace)
or [aivision-metric](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-metric).
