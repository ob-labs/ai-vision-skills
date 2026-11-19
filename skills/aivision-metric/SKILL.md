---
name: aivision-metric
description: Use the aiv CLI to measure AI Vision request volume, errors, latency, token use, and cost over a time window and check coverage before comparing results.
---

# AI Vision Metric

Compute aggregate signals from the capabilities exposed to the current `aiv`
profile. The server enforces SpaceKey visibility; use the CLI for every platform
read. Keep the endpoint, space, agent product and time window fixed per result.

## Prerequisites

Check the active CLI and the commands you need:

```bash
command -v aiv
aiv --version
aiv query metadata --help
aiv query trace metrics --help
```

If `aiv` is missing or lacks a required command, use
[reference/install-cli.md](reference/install-cli.md) to locate or install a
compatible CLI. Use `Get-Command aiv` to check the path in PowerShell.

Reuse the confirmed `PROFILE`, endpoint and space. Set `AGENT_PRODUCT` and,
for an instance request, `AGENT_UUID` from the existing platform Agent details
or the user's known instance. Product and UUID are different selectors; pass
the explicit product in every recipe. The endpoint must be reachable from this
machine (`localhost` refers to this machine). Existing telemetry needs neither
redeployment nor a local Agent hook.

Inspect `aiv auth status --profile "$PROFILE"`, then verify a scoped query.
SpaceKey-only profiles need no account login; an expired account session does
not block a working query key. For missing profiles, key setup, changed spaces,
401/403/404, failed metadata or empty results, follow
[reference/query-setup.md](reference/query-setup.md). Preserve failures and verify
scope before widening a window or inferring that collection is broken.

## Query a complete trace window

Freeze the requested scope and time window into absolute UTC `SINCE` / `UNTIL`
bounds. Reuse those values for every comparison. The commands below select one
confirmed instance and create a private directory outside the repository. For
a product with multiple instances, query each relevant Agent UUID and record
the coverage. A product name alone can select a default route. Use unique output
names for each query and retry because `-o` overwrites files.

```bash
: "${PROFILE:?Select a profile}" "${AGENT_PRODUCT:?Confirm the Agent product}" \
  "${AGENT_UUID:?Confirm the instance UUID}" "${SINCE:?Set the frozen start}" \
  "${UNTIL:?Set the frozen end}"
umask 077
OUT=$(mktemp -d "${TMPDIR:-/tmp}/aivision-metric.XXXXXX") || exit 1
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --format json -o "$OUT/metadata.json"
aiv query trace metrics --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --agent-uuid "$AGENT_UUID" --since "$SINCE" --until "$UNTIL" \
  --bucket hour --group-by model -o "$OUT/metrics.json"
```

This queries the entire window through the native trace metrics API, which is
independent of raw SQL support. `--bucket` accepts `minute`, `hour` or `day`.
`--group-by` accepts `model` or `provider` and defaults to `model`.
For comparisons using metadata, list/get/export or session commands, use
`--param agent_uuid="$AGENT_UUID"`; their flags differ from metrics. Verify the
returned scope and preserve it through every page and detail request.
Filters use a JSON array, for example
`--filter '[{"field":"status_code","op":"IN","value":[1,2]}]'`.

The result is JSON: counts, error rate, canonical token/cost `usage`, `coverage`,
`latencyMs.mean` / `p95`, `timeseries`, `groups`, and `meta` with the exact bounds
and filters. Read it before reporting a measurement:

- The CLI requires `meta.complete` to be `true` before it writes aggregate output.
- If the backend returns the **10,000-trace scan limit**, narrow the window and
  report the effective bounds. The command has no pagination. Report p95 for
  each measured scope or compute it from the full set of trace latencies.
- Retrieval completeness differs from usage coverage. If a billable call lacks
  usage, `usage.total` can be null. Report `coverage.knownTokens` as a known
  subtotal alongside `knownUsageCalls` / `billableCalls`, never as a full total.
  Missing latency/cost also stays null; preserve cost provenance and currency.
- Preserve failures as failures, not empty arrays or zeros. An old CLI's unknown
  command or a datasource's unsupported endpoint is not verified support.

Include method (`native trace metrics`), scope, UTC bounds, filters, CLI version,
retrieval time, units and coverage in the report. Retain command/output evidence
privately; omit credentials and raw telemetry from commits and chat.

## Other analyses

For SQL or event queries, first read
[reference/query-capabilities.md](reference/query-capabilities.md). Missing SQL
support does not disable native trace metrics.

For custom detail analysis or an unavailable aggregate endpoint, read
[reference/local-aggregation.md](reference/local-aggregation.md). Retrieve all
pages/details, deduplicate identities, preserve missing values and label the
method `local aggregation of CLI trace details`. Preserve any original failure;
this separate analysis does not establish server aggregate support.
