# SQL and event query capabilities

Reuse the confirmed `PROFILE` and explicit `AGENT_PRODUCT` from the skill. Read capabilities
and schema metadata with that scope:

```bash
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --format json
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --format json traces
aiv query metadata --profile "$PROFILE" --agent-product "$AGENT_PRODUCT" --format json events
```

For an instance-specific analysis, add `--param agent_uuid="$AGENT_UUID"` before
positional kinds on each metadata query. Native metrics uses `--agent-uuid`;
metadata/list/detail/session commands use `--param agent_uuid=...`.

On success, the command without a kind returns `capabilities`; `traces` and
`events` return field metadata. Preserve failed metadata requests and report
the affected capability as unknown. A failed event metadata request does not
invalidate independently verified trace queries. Schema discovery alone does
not establish SQL support.

| Observed capability | Action |
|---|---|
| `capabilities.events.query=true` and `capabilities.events.modes.rawSql=true` | SQL may use the backend's documented views, fields and required scoping macros. Validate its actual numeric response. |
| `rawSql=false` or absent | Skip `metric query` and `log query --mode rawSql`; use `trace metrics` for native trace aggregates. |
| Native trace metrics unavailable | Report the limitation. A separately requested detail analysis follows [local-aggregation.md](local-aggregation.md). |

`aiv query metric query` sends raw SQL through the Grafana endpoint; it is not
an independent SQL service. When SQL is unavailable, changing table names or
adding SQL macros cannot enable it. A rejected query remains a failed query.

`log query --mode fieldsJson` queries event rows, not a field dictionary.
Start with its default projection when that mode is supported. Metadata can
describe stored fields that a query endpoint does not expose; confirm returned
fields before choosing projections or aggregating them. Paginate event counts
separately and preserve their own coverage.
