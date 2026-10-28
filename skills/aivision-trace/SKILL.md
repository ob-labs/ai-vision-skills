---
name: aivision-trace
description: Use when inspecting AI Vision LLM traces or span trees, debugging a conversation, exporting production telemetry for replay, or curating evaluation records with session context and token usage.
---

# AI Vision Trace

Use the `aiv` CLI with its selected profile to read trace data. Preserve the
query scope and full source evidence through selection, export and curation.

## Prerequisites

Expose an existing default installation before downloading anything:

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v aiv
aiv --version
aiv query metadata --help
aiv query trace list --help
```

If the binary is missing, cannot run, or lacks the required command/flags, follow
[reference/install-cli.md](reference/install-cli.md). Check the selected path and
help again after installing a compatible release; a printed version is insufficient.

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

## Inspect and export

Set `PROFILE` to the confirmed profile and resolve the requested time range
**once** into absolute RFC3339 or epoch `SINCE` / `UNTIL` values. Reuse those
exact values for every list, export, session usage and log query. Put all flags
before positional IDs, especially when passing multiple session IDs. For an
instance-specific task, set `AGENT_UUID` and pass `--param agent_uuid="$AGENT_UUID"`
to each query; `--agent-product` selects a product, not an instance. Metrics alone
has a dedicated `--agent-uuid` flag. Carry a requested source via `--param
source_system=...` too, and check returned identities and effective bounds.

Create a new private directory outside the repository; `-o` overwrites existing
files, so keep unique filenames for pages, details and retries. The commands
below select one confirmed instance. For an explicitly product-wide request,
omit the UUID check and selector together.

```bash
: "${PROFILE:?Select a profile}" "${AGENT_PRODUCT:?Confirm the Agent product}" \
  "${AGENT_UUID:?Confirm the instance UUID}" "${SINCE:?Set the frozen start}" \
  "${UNTIL:?Set the frozen end}"
umask 077
OUT=$(mktemp -d "${TMPDIR:-/tmp}/aivision-trace.XXXXXX") || exit 1
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --format json -o "$OUT/trace-metadata.json" traces
aiv query trace list --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --since "$SINCE" --until "$UNTIL" \
  --param agent_uuid="$AGENT_UUID" --page 1 --limit 100 --format json -o "$OUT/candidates-page-1.json"
```

Read the list response before continuing. Set `TRACE_ID` to a returned ID and
`FROM_MS` / `TO_MS` to its verified `meta.from` / `meta.to` epoch-millisecond
bounds; then retrieve that detail:

```bash
: "${TRACE_ID:?Select a returned trace ID}" "${FROM_MS:?Set verified from bound}" \
  "${TO_MS:?Set verified to bound}"
aiv query trace get --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" \
  --param from="$FROM_MS" --param to="$TO_MS" --format json -o "$OUT/trace.json" "$TRACE_ID"
```

For native detail queries, `FROM_MS` / `TO_MS` are the frozen bounds in epoch
milliseconds, obtainable from the verified list response's `meta.from` / `meta.to`.
Omit the UUID selector only for an explicitly requested product-wide result.

Start with default fields. Choose projections and predicates from metadata and
the actual response schema, then verify that returned rows satisfy the filter.
A successful command alone does not prove filtering. If a filter is rejected
or ignored, fetch the complete paginated population through the CLI, apply the
declared predicate locally, and export the exact selected IDs. Record missing
pages or IDs as incomplete scope.

**For batch exports or evaluation datasets, read and follow
[reference/dataset-export.md](reference/dataset-export.md).** It covers pagination,
full exports, session context, usage and the record contract. In particular:

- Select the final user-facing business answer from full trace messages in
  chronological and parent/child context. Tool calls and tool results remain
  context; Relay-style message `parts` need decoding too.
- Preserve `observed_output` separately from an independently justified
  `reference_answer`. Empty, ambiguous or parser-gap recovery records remain
  ineligible pending review.
- `trace get`, `session get` and `session io` ignore `--since` / `--until`.
  Pass explicit `--param from` / `--param to` for the native API; otherwise
  backend defaults may limit context to a rolling window. Verify returned
  bounds and membership; use a separately recorded wider window for context.
- Preserve each usage field's presence and raw value: missing, null and explicit
  zero differ. Report known subtotals and coverage; keep derived totals separate.
  Correlate logs using their actual time field, full timestamp precision and
  scope; unresolved parsing stays an explicit gap.

Use JSON for processing. Keep raw exports private and outside version control;
redact payloads before sharing. This skill reads telemetry and produces local
artifacts; it does not manage platform datasets.
