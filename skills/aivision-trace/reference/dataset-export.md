# Compose an evaluation dataset

This is the complete batch-export and curation recipe for
[`aivision-trace`](../SKILL.md). Use only `aiv` for remote reads; local processing
of its saved JSON is supported. Keep immutable raw responses separately from
curated records. Telemetry is evidence of observed behavior, not ground truth.

## 1. Freeze scope and inspect the schema

Complete the [prerequisites and private output setup](../SKILL.md) first. Reuse
that confirmed `PROFILE`, explicit `AGENT_PRODUCT` and private absolute `OUT`.
An expired account session does not block a valid SpaceKey query. Resolve the
user's requested window once into absolute RFC3339 or epoch
`SINCE` and `UNTIL`, and save them with the CLI version, profile, space, Agent
product and collection time in a manifest. Reuse the same scope and bounds in
every time-aware command, including retries and session usage. Include the
selected Agent UUID and source in the manifest. For an instance-specific task,
pass `--param agent_uuid="$AGENT_UUID"` on metadata, list, detail, export, session
and log commands below; this is distinct from `--agent-product`. Carry a requested
source via `--param source_system=...` and verify response identities. Omit these
selectors only when the requested population spans those instances or sources.
Relative values
such as `7d` or `now` are suitable for exploration, not a reproducible export.

The examples use a fresh subdirectory of `OUT`, preserving any exploratory
outputs. All flags precede positional IDs or paths. Read metadata before choosing fields
or predicates, then inspect default rows; storage fields and returned aliases
can differ. Metadata presence alone does not prove an endpoint accepts a field.

```bash
OUT=$(mktemp -d "$OUT/dataset.XXXXXX") || exit 1
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --format json -o "$OUT/trace-metadata.json" traces
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --format json -o "$OUT/event-metadata.json" events
aiv query trace list --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --since "$SINCE" --until "$UNTIL" \
  --page 1 --limit 100 --format json -o "$OUT/candidates-page-1.json"
```

When applying `--fields` or `--filter`, use the discovered field types and the
backend's supported predicate syntax. Verify the selected fields and check the
predicate against every returned row and a known nonmatching control when
available. Keep the unfiltered comparison and the predicate in the manifest.
An exit code of zero, or the same rows for opposing predicates, is not filtering
evidence. Preserve unknown/UNSET status separately from explicit success.

**If the filter or projection is rejected, ignored or unverifiable:** save that
limitation, omit the failing options, fetch all pages with default fields, then
filter the saved rows locally using an explicit field/type/value predicate.
Retrieve full details if a required predicate field is missing. Record the mode
as `local_filter` with counts before/after and the exact selected IDs. If the
required data cannot be retrieved, keep the result incomplete rather than
silently changing the requested population.

## 2. Account for every page and export the exact IDs

Repeat the list command with `--page 2`, `--page 3`, etc., preserving bounds,
limit and verified ordering. Follow returned pagination metadata (for example
`meta.totalPages` / `meta.totalItems`) and reconcile the count of distinct IDs.
Where totals are absent, require a verified terminal page and continued page
progress; repeated pages or an unexplained limit cap mean incomplete retrieval.
Save each page under a distinct filename. A single `--limit` is not a complete
population. Any intentionally sampled subset needs a stated sampling rule and
coverage count.

Save `selected-ids.txt` from the verified selection, one distinct trace ID per
line. Fetch each full detail without field projection, for example:

```bash
aiv query trace get --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --param from="$FROM_MS" --param to="$TO_MS" \
  --format json -o "$TRACE_RAW_FILE" "$TRACE_ID"
```

Here `TRACE_ID` is each selected ID and `TRACE_RAW_FILE` is its unique local
output path under `OUT`; retries use a new filename. `-o` and exports overwrite
existing files. For native detail reads, also pass `--param from="$FROM_MS" --param
to="$TO_MS"`, using epoch-millisecond bounds from the verified list's `meta.from`
and `meta.to`. The get command does not forward `--since` / `--until`. Match the
returned scope, trace ID, session ID and span tree to the selection; reject
`meta.complete=false`, missing/duplicate span IDs and a span-count mismatch
against the list. Preserve all spans, attributes, events and message payloads.
Reconcile selected IDs against successfully saved details: report missing and
unexpected IDs, duplicates, failures and counts. Deduplicate records by
`(scope, trace_id)` and spans by `(trace_id, span_id)`, preserving provenance.

`trace export` is a convenient list-and-detail operation for **one page**:

```bash
aiv query trace export --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --since "$SINCE" --until "$UNTIL" \
  --page 1 --limit 100 --filename-pattern '{trace_id}.json' "$OUT/page-1"
```

For a verified server filter, pass that same filter and page configuration to
each export. Reconcile exported IDs against the selection. For local filtering,
either fetch selected IDs with `trace get`, or export every unfiltered page to
separate directories and retain only the selected IDs in the curated set. This
also prevents repeated JSONL exports from overwriting earlier pages.

## 3. Attach session context and reconcile usage

For every selected session, save its detail, IO and windowed usage. Deduplicate
session IDs and split usage requests into batches of **1–100 IDs**; the CLI does
not split them automatically. All flags must precede **all** IDs in a batch:

```bash
aiv query session get --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --param from="$FROM_MS" --param to="$TO_MS" \
  --format json -o "$OUT/session-$SESSION_ID.json" "$SESSION_ID"
aiv query session io --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --param from="$FROM_MS" --param to="$TO_MS" \
  --format json -o "$OUT/session-io-$SESSION_ID.json" "$SESSION_ID"
aiv query session usage --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --since "$SINCE" --until "$UNTIL" \
  --format json -o "$OUT/session-usage-batch-1.json" "$SESSION_1" "$SESSION_2"
aiv query log list --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" \
  --param agent_uuid="$AGENT_UUID" --since "$SINCE" --until "$UNTIL" \
  --page 1 --limit 100 --format json -o "$OUT/logs-page-1.json"
```

Use unique filenames per session/batch. `trace get`, `session get` and `session
io` do not forward `--since` / `--until`; omitted bounds may trigger a backend
default such as a rolling 24-hour window. For native queries, pass `--param
from="$FROM_MS" --param to="$TO_MS"` explicitly on all three commands. Verify
returned `meta.from` / `meta.to` and trace membership against the selection.
Label this `windowed_context`, not full session history. If more conversation
context is needed, use a separately recorded wider absolute window and label
it `wider_window_context`; retain the original selection and usage bounds.
For a source without explicit bound support or metadata, record its actual
coverage and unresolved gaps. Preserve ordered turns and first/last business
IO, fetching referenced traces when needed. A session summary or default page
is not proof of full conversation coverage.

Usage describes all traces for those sessions **inside the frozen window**,
including traces excluded by the curation predicate. Check every requested
session ID is present, and reconcile against the full window population using
each contributing span once and the documented aggregation semantics. Preserve
input/output/total/cache fields and units as returned; parent aggregates and
child usage must not be counted twice. Determine contributing spans from their
operation and schema, retaining gaps even when a span lacks input tokens.

For **each** usage field, record its source pointer, `raw_present`, `raw_value`,
validated numeric `value` and state. Use key membership before reading a value:

| Raw field | Stored observation |
| --- | --- |
| Absent | `raw_present=false`, `raw_value=null`, `value=null`, `state=missing` |
| Present as null | `raw_present=true`, `raw_value=null`, `value=null`, `state=null` |
| Present as explicit zero | `raw_present=true`, `raw_value=0`, `value=0`, `state=observed` |

Retain original numeric strings as `raw_value` when normalizing them. Invalid or
unsupported fields carry that reason and `value=null`. Missing cache is unknown;
lack of cache evidence does not establish zero. `raw.get(field, 0)`, `value or 0`
and treating an empty sum as a known zero erase this distinction.

Aggregate each field into `known_subtotal`, `known_count`, `expected_count` and
missing/null/invalid/unsupported counts. With no observed values, the subtotal
is null. Partial coverage remains a known subtotal, not a complete total. A
matching subtotal alone cannot yield `reconciled_complete`. Record reconciliation
per field, including unresolved coverage. Report verified input/output/total
independently of unknown cache fields. An unknown optional field does not make
the record ineligible; only an unresolved check required by the evaluation task
affects eligibility. Keep a computed `derived_total`
separate from an absent raw total, with its formula, input pointers and justified
counter semantics; matching the API does not make it an observed span value.
Explain cache-inclusive versus exclusive counters or provider/SDK discrepancies
instead of relabeling them as exact provider totals. If coverage needs a wider
window, record a separate context query; keep the original bounds intact.

Paginate logs where supported and correlate by trace/session identity and time.
Choose the timestamp key from the actual raw schema (such as `time`, `timestamp`
or `period`), and save its field name, exact raw value and source row pointer.
Preserve all supplied fractional digits, including nine-digit nanoseconds; use
integer nanoseconds or an exact representation for comparisons, avoiding float
or microsecond-only truncation. Check the frozen window and the stated temporal
relation to the trace/session, together with the matching scoped trace/session
pair. Record identity, scope and time checks separately. A missing, null,
ambiguous or unparseable timestamp needs a specific gap and an unresolved time
check; a null normalized time cannot accompany a claim of complete correlation.
Apply the same metadata and verified-filter rules as traces. Report unavailable
logs or unsupported fields as limitations, not as evidence that no error exists.

## 4. Extract the final business answer

Process the **full raw trace**, retaining message roles, span IDs, parent IDs,
timestamps, tool-call IDs and finish reasons. Decode JSON-encoded message
attributes such as `gen_ai.input.messages` / `gen_ai.output.messages`, as well
as structured `content` and message `parts`. For Relay-style parts, text may be
in `{"type":"text","content":"..."}`; `tool_call` arguments and
`tool_call_response` payloads are context even when they contain valid JSON.

Identify the original user business request. Order model turns by timestamps
and message order, then follow the main agent's parent/child execution and tool
responses through completion. Choose the terminal **user-facing assistant
answer** to that request, after the relevant tool sequence. A subagent's final
answer may still be intermediate to the main agent. A root span may have empty
output, and the first nonempty assistant message may be a tool request or
progress text. Neither position nor valid JSON alone establishes finality.

Store the exact selected answer in `observed_output`, plus the source raw file,
span ID, attribute key, message/part index and extraction rationale. Keep tool
calls/results and earlier assistant messages in `context`. If parsing JSON or
removing a Markdown fence for evaluation, retain the original answer and record
the transformation separately. Cross-check against session IO and available
independent execution evidence.

When session IO or a parser misses output that is recovered from raw messages,
record `recovered_from_raw` and the parser gap explicitly. Retain the candidate
with `eval_eligible=false` pending review of that gap. Missing, truncated,
ambiguous, contradictory or unparseable output likewise needs a specific
ineligibility reason; an empty string is not an accepted final answer.

## 5. Deliver auditable records

Each curated JSONL record carries these fields or equivalent explicit fields:

| Content | Required evidence |
| --- | --- |
| Identity and scope | Profile/space/Agent product, selected Agent UUID/source, trace/session IDs, frozen since/until and effective context bounds, selection predicate and server/local mode |
| Provenance | Raw file paths and hashes, selected span/message/part pointers, collection time, CLI version, extraction transformations |
| Business pair | Original `input`, exact `observed_output`, ordered `context`, separate tool messages |
| Session and usage | Session trace membership and first/last IO, windowed usage, per-field presence/raw values, known subtotals/coverage, separate derived values and reconciliation states |
| Log correlation | Raw timestamp field/value and precision, source row, scoped trace/session pair, separate identity/scope/time checks and gaps |
| Reference answer | `reference_answer` and independent source/justification; `null` with reason when none exists |
| Eligibility | `eval_eligible`, reasons, status interpretation, completeness and parser-gap/recovery flags |

An observed answer, success status or a tool's JSON is not by itself a reference
answer. Populate `reference_answer` only from an independently justified source
such as reviewed ground truth, authoritative source data or a validated business
rule. Reference-based evaluation requires that reference; observation/replay
records can retain `null` with the evaluation purpose stated.

Before setting `eval_eligible=true`, verify scope, complete source retrieval,
semantic final output, session coverage and required usage checks. Deliver the
manifest, exact selected-ID inventory, raw directory, curated JSONL and a short
report of fetched/selected/eligible/excluded counts with unresolved limitations.
Keep raw telemetry private and outside version control; redact any shared sample.
