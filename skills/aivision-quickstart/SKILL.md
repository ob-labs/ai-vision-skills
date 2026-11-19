---
name: aivision-quickstart
description: Use when a user wants to try AI Vision on a reachable platform, explore its examples, connect a first Agent or SDK, or run a live test workload to verify Traces, Sessions and diagnosis.
---

# AI Vision Quickstart

Start from the user's existing instance and selected Space. Help the user
find a Trace, inspect the evidence for one call, and continue to a Session or
diagnosis when the selected path supports it. If the user still needs a
platform, use the [deployment Skill](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-deploy).
Have the user open `/register` for a new account or `/login` for an existing
one. If registration is disabled, use an authorized account or a team invitation.

## Choose a first experience

| User goal | Follow this path |
|---|---|
| See the product without a model key | Open **Help → Getting started**. If **Try an example** is available, have the user pick and confirm a scenario. Use the chosen example or full walkthrough to inspect a Trace and, when relevant, its Session or built-in rule result. Keep its simulated activity, usage and cost labeled as demo data. |
| Connect an existing Agent or SDK | Open **Agent Access** at `/access` and follow the deployed version's integration guide. Use the guide's generated configuration and runnable example for the user's language/framework, or generate its Agent installation command. Run a recognizable task and verify its Trace in the same Space and Agent. |
| Run a live evaluation with help from the coding Agent | Follow [the live demo workflow](reference/workflow.md). The bundled Python example sends real requests from an isolated test Agent and preserves identifiers and request counts for readback. |

Use the installed UI for examples and setup instructions. When a guide or demo
is unavailable, explain the capability or access gap and use the relevant
[manual first-Agent tutorial](https://aivision.mintlify.site/en/web-quickstart)
or the user's authorized live-demo path.

## Run and verify the live demo

1. Confirm the reachable URL, actual version, Space, test Agent and a private
   source for model credentials. The demo needs an OpenAI-compatible endpoint.
   Have the user supply secrets locally. Use a matching Model Connection
   when model-backed diagnosis is requested.
2. Run the bundled [demo](scripts/run_demo.py) in an isolated environment. The
   default command is offline planning. An authorized live run uses
   `--execute --config <private.json> --out <new-run-directory>`. It sends up to
   four model requests in two two-turn Sessions with no provider retries.
   Honor a smaller budget using the deployed integration's example. Connection
   tests, validation and model-backed diagnosis make additional requests.
3. Verify the exact generated Trace and Session IDs in the recorded Space,
   Agent and window. Inspect inputs, outputs, usage and the handled tool error.
   If supported and in scope, run one Quick Diagnosis on those Traces. Use one
   persisted request ID, check task and record states, and explain failed,
   skipped or missing results.
4. Hand back verified links, the actual request count and usage, and one
   concrete observation. Preserve demo state for the user's own review and
   keep secrets and private receipts out of shared output.

Use [aivision-trace](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-trace)
or [aivision-metric](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-metric)
for follow-on analysis of existing telemetry.
