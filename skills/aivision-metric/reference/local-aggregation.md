# Local aggregation of CLI trace details

Use `aiv query trace metrics` for native whole-window trace aggregates. Verify
`meta.complete: true` and inspect usage coverage. If the backend returns the
10,000-trace scan limit, record the error and the requested bounds.

Use this local path for a requested custom detail analysis or when the native
aggregate endpoint is unavailable and full trace list/detail retrieval can be
verified. This produces local trace-derived measurements; it does not prove
that a server metric/SQL endpoint works. A list page is never a full-window
total. Preserve any failed aggregate request as evidence before considering
this separate method.

## 1. Fix the scope and retrieve the full population

Resolve the requested endpoint, profile, space, agent product and Agent UUID
once. For instance-specific comparisons, native metrics uses `--agent-uuid`,
while metadata/list/get/export/session commands use `--param
agent_uuid="$AGENT_UUID"`. Apply the same selector throughout. For a product
with multiple instances, read each relevant Agent UUID and record the coverage.
For each scope, choose one absolute UTC `SINCE`/`UNTIL` pair and a bounded time window.
The CLI accepts RFC3339 or epoch seconds/milliseconds and sends milliseconds.
Do not pass epoch nanoseconds as CLI bounds. Relative values such as `1h` and
`now` are useful interactively but would move between pagination requests.

In these commands, `PROFILE` is the selected saved profile, `SINCE`/`UNTIL` are
the frozen bounds, `PAGE` starts at 1, and `TRACE_ID` comes from the returned
list. `OUT` is the private absolute directory created by the skill. Keep prior
failed-query evidence there and use new filenames for retries; outputs overwrite.
`FROM_MS` / `TO_MS` are the
same frozen bounds in epoch milliseconds, available from the verified list's
`meta.from` / `meta.to`. Set values from the current task; do not reuse identities
or windows from a previous run. The following example selects one Agent:

```bash
: "${OUT:?Use the skill private output directory}" "${AGENT_PRODUCT:?Confirm product}" \
  "${AGENT_UUID:?Confirm instance UUID}"
umask 077
OUT=$(mktemp -d "$OUT/local-aggregation.XXXXXX") || exit 1
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --param agent_uuid="$AGENT_UUID" \
  --format json -o "$OUT/metadata.json"
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --param agent_uuid="$AGENT_UUID" \
  --format json -o "$OUT/trace-schema.json" traces
aiv query trace list --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --since "$SINCE" --until "$UNTIL" \
  --param agent_uuid="$AGENT_UUID" --limit 100 --page "$PAGE" --format json -o "$OUT/list-$PAGE.json"
aiv query trace get --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --param agent_uuid="$AGENT_UUID" \
  --param from="$FROM_MS" --param to="$TO_MS" --format json \
  -o "$OUT/trace-$TRACE_ID.json" "$TRACE_ID"
```

This is one list page and one detail, not a complete export loop. Repeat list
with increasing `--page` and fetch each distinct returned trace ID. Keep the
same scope, bounds, page size and ordering. A typical list has `data` rows and
`meta.page`, `meta.limit`, `meta.totalItems`, `meta.totalPages`; inspect the actual
envelope. Follow all declared pages and reconcile the distinct ID count with
the declared total. Without pagination totals, continue until an empty page and
record that completion evidence. Repeated pages, changing totals or a request
budget reached before completion mean the result is partial. Narrow/split the
window when needed, deduplicating trace IDs across adjacent windows.

Begin with default fields and no speculative filter. Verify a requested filter
against returned records; an HTTP success is not proof that filtering worked.
If it cannot be verified, retrieve the bounded population and apply the exact
predicate locally, recording the predicate and selected/excluded counts. Keep
unmatched or undecidable records separate rather than silently discarding them.

The detail response commonly contains `traceId`, `sessionId` and `spans`.
Verify each detail's identity, compare its distinct span count to the list's
`span_count` when supplied, reject `meta.complete=false`, and record retrieval
failures. `trace get` ignores `--since` / `--until`; pass explicit `--param from`
and `--param to` for native reads. Without them, backend defaults may limit
retrieval or hide historical data. Verify returned scope/bounds and reconcile
details with the frozen list. If a source omits bound metadata, retain the
coverage gap and verify actual membership rather than calling it unwindowed.
State whether metrics include full retrieved trace spans or a local per-span
timestamp predicate; a boundary-crossing span can end outside the window.

An alternative is one export per list page:

```bash
aiv query trace export --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --since "$SINCE" --until "$UNTIL" \
  --param agent_uuid="$AGENT_UUID" --limit 100 --page "$PAGE" \
  --filename-pattern '{trace_id}.json' "$OUT/page-$PAGE"
```

Export does not paginate automatically. Detail reads preserve the list's Agent
UUID, source and frozen time bounds. Both JSONL and per-trace exports fail if a
detail is unavailable, reporting the failed trace, completed count and retained
output location. Native details must match the listed trace identity, contain
unique span IDs, and match the listed span count when supplied. Reconcile each
exported page's IDs with its list page and
inspect full span content. Keep page directories separate to avoid overwriting
files.

## 2. Define counts and latency

Normalize the response envelope, then keep one trace per `trace_id`/`traceId`
and one span per `(trace_id, span_id)`. Conflicting duplicate records require
investigation; do not arbitrarily add or select them. Retain original values
and their source field names alongside normalized measurements.

| Measurement | Definition |
|---|---|
| Trace count | Number of distinct selected trace IDs; disclose missing details separately. |
| Span count | Number of distinct span identities in verified details. |
| Span latency | `end - start` for that span, converted from nanoseconds to milliseconds by dividing by `1_000_000`. A confirmed `duration_nano` is another nanosecond source; cross-check when both exist. |
| Trace latency | Full trace envelope: maximum span end minus minimum span start. Do not sum child durations because spans can overlap. Label a root-span latency separately if requested. |
| Quantiles | State the method, unit and sample count. For nearest rank on sorted values, p50/p95 select index `ceil(p*n)-1`. An empty population has null latency statistics. |

Inspect wire values before parsing. Fields named `start_time_unix_nano` and
`end_time_unix_nano` may contain ISO8601 strings with up to nine fractional
digits, even when schema metadata says `bigint`. Parse numeric nanoseconds as
integers; parse ISO timestamps with the timezone and all fractional digits.
Preserve integer nanoseconds before subtracting. Avoid floating-point epoch
arithmetic, JavaScript `Date` millisecond truncation, or a parser that silently
truncates ISO fractions to microseconds. Convert only the final duration to the
reported unit. Missing or invalid/reversed times produce null latency and a
coverage gap, not zero or a silently omitted observation.

## 3. Reconcile generation usage and cost

Identify actual model-generation spans from the observed instrumentation, for
example `gen_ai.operation.name=chat`, `gen_ai.span.kind=LLM`,
`langfuse.observation.type=generation`, or a source's native LLM marker, model
fields and messages. Verify this selection against the span tree: a wrapper or
parent can repeat usage from its children. Count each generation once and
exclude parent/chain/tool aggregate copies. Do not require every SDK to emit the
same marker, or infer generation count from every span with any token field.

Build a per-generation ledger before summing. For every value record its span
identity, exact source field, numeric value, meaning and whether it was observed
or derived. Usage may live in `attributes`, native payloads or JSON-encoded
objects such as `langfuse.observation.usage_details`; decode these explicitly.
Parse numeric strings too. Choose one canonical source per measure; aliases and
nested copies of the same usage are not additional tokens.

| Measure | Aggregation rule |
|---|---|
| Input / output | Retain `gen_ai.usage.input_tokens`, `output_tokens` or equivalent native values with their source semantics. Missing fields stay null. |
| Cache reads / writes | Report explicit buckets separately, including native buckets such as `input_cache_read` / `input_cache_creation` when present. Missing buckets are unknown; an explicit zero is known zero. |
| Cache-inclusive input | If the source proves input excludes cache, add only disjoint cache buckets. If input already includes cache, leave input unchanged. If inclusion semantics are unknown, leave normalized inclusive input null and retain the observed values. |
| Total | Preserve an observed `total_tokens` / native total. Derive `input + output` only when the input is known to include all input/cache tokens, or after a proven disjoint-bucket reconciliation. Never add cache again to an inclusive total. |
| Cost | Use explicit generation cost fields such as `gen_ai.usage.total_cost` with currency/provenance. Use decimal arithmetic. Sum input/output components only when documented to be disjoint and complete. Missing cost or currency is unknown; never substitute zero or invent model prices. |

For example, input `120`, cache-read `80`, output `20` and total `220` are
consistent with exclusive input. If that source's contract confirms the
exclusion, inclusive input is `200`. Input `200`, cache-read `80`, output `20`
and total `220` instead need no extra cache addition. The arithmetic alone does
not establish a source's semantics. Output reasoning tokens may similarly be
included in output already.

Trace-list/session token totals are useful cross-checks, not values to add to
the generation ledger. API input can exclude cache even when API total includes
it. If session usage is checked, deduplicate session IDs and split requests into
batches of **1–100 IDs**; the CLI does not split them automatically. Pass the same
frozen bounds and put all flags before all IDs:

```bash
aiv query session usage --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --since "$SINCE" --until "$UNTIL" \
  --param agent_uuid="$AGENT_UUID" --format json "$SESSION_1" "$SESSION_2"
```

Keep disagreements visible. Platform/SDK usage is observed telemetry; only an
independent provider ledger can prove actual provider consumption. In particular,
repeated cumulative streaming usage must not be silently presented as verified
provider billing. Any correction needs a cited source and a separate derived value.

For each measure report `known_sum`, `present_count`, `missing_count`,
`expected_count` and `complete`. A complete total is null while required values
are missing. A known subtotal remains useful when clearly labelled; no present
values means null, not zero. Cost with no values is `unknown`, including when all
token counts are known. Do not combine unlike currencies or incompatible token
definitions into one total.

## 4. Report the result and limits

Include the method (`local aggregation of CLI trace details`), profile/scope,
absolute window and inclusion rule, retrieval time, CLI version, capability
decision, page/ID/detail coverage, trace/span counts, generation selection,
latency definition/unit/quantiles, token/cache semantics, cost currency and
per-field coverage. Link private command/output and ledger artifacts as
provenance; omit credentials and raw prompts from the user-facing aggregate.

If event counts are also requested, check event list or `fieldsJson` support and
paginate that signal separately with the same bounds. `fieldsJson` returns event
rows. Start with the default projection; aggregate only fields actually returned
and reconcile pagination separately. Do not count schema entries as events, or
deduplicate events by trace/span ID because one span can emit multiple records.
Unsupported event fields remain unavailable rather than being fabricated from
trace spans.
