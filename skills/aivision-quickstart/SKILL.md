---
name: aivision-quickstart
description: Use when a user wants to try AI Vision on an existing instance, open a built-in example, connect a first Agent or SDK, or verify Traces and Sessions from the bundled demo.
---

# AI Vision Quickstart

Confirm the user's instance and Space. Help them open a Trace and inspect one
model or tool call that belongs to it. Continue to a Session or diagnosis when
the chosen example supports it. If the user needs an instance, use the
[deployment Skill](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-deploy).
For a first sign-in, use `/register` if registration is enabled, or sign in at
`/login` with an authorized account. Follow the team invitation if needed.

## Choose a first experience

| User goal | Follow this path |
|---|---|
| Explore example traces without a model key | Open **Help → Try an example** when available. Let the user choose a scenario and confirm creation of sample data in the selected Space. Open an example Trace and keep simulated Token usage and cost labeled as demo data. |
| Connect an Agent or SDK | Open **Agent Access** at `/access` and follow the selected integration's guide. Use its generated configuration and example for the user's framework, or its Agent installation command. Run a recognizable task and open its Trace in the same Space and Agent. For an SDK example, use **Verify this Trace** when available. |
| Run the bundled demo with a real model | Follow [the live demo workflow](reference/workflow.md) for the isolated test Agent, request budget, and exact Trace and Session IDs. |

Use **Help → Getting started** to start the walkthrough, or resume it from the
same menu. If the deployed instance lacks the example or integration guide, use the
[first-Agent tutorial](https://aivision.mintlify.site/en/web-quickstart).

## Run and verify the live demo

1. Confirm the reachable URL, version, Space, test Agent, and OpenAI-compatible
   Chat Completions endpoint. Have the user supply credentials locally.
2. Run the bundled [demo](scripts/run_demo.py) in an isolated environment. The
   default command prints an offline plan. With authorization for model calls,
   use `--execute --config <private.json> --out <new-run-directory>`. A complete
   run sends four requests across two Sessions with zero provider retries.
   Use a smaller integration example when the user sets a smaller budget.
   Model connection tests, validation, and model-backed diagnosis use
   additional requests.
3. Open the exact Trace and Session links in the report. Verify the Space,
   Agent and time window, then inspect the calls and handled tool error that
   actually appear. If requested and supported, run one Quick Diagnosis as
   described in the workflow and check its task and records.
4. Report the actual request count, verified links, observed usage, and any
   missing evidence. Keep secrets and private reports out of shared output.

Use [aivision-trace](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-trace)
or [aivision-metric](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-metric)
for follow-on analysis of existing telemetry.
