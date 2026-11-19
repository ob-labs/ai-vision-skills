# Bundled deployment operations

These recipient details accompany the released CLI's embedded product assets.
They do not require a product source checkout. Use the selected Release's actual
capabilities; a source merge or static validation does not qualify released images.

## Component names and configuration

| Product role | Compatible CLI aliases | Retained implementation / physical name |
|---|---|---|
| `frontend` | `fe`, `aivision-fe` | React / Nginx; `aivision-fe` |
| `backend` | `be`, `aivision-be` | Django; `aivision-be` |
| `diagnosis` | `agentlens` | AgentLens; `agentlens` |
| `ingest-gateway` | `gateway`, `antcollector-gw` | AntCollector; `antcollector-gw` |
| `data-backend` | `signoz`, `signoz-ob` | External SigNoz OceanBase distribution; `signoz-ob` |
| `database` | `oceanbase`, `seekdb` | OceanBase CE / seekdb; Kubernetes uses OB Operator |

Canonical configuration aliases map to existing keys as follows:

| Canonical prefix/key | Existing key(s), in matching suffix order |
|---|---|
| `FRONTEND_{IMAGE,CONTAINER,PORT}` | `FE_{IMAGE,CONTAINER,PORT}` |
| `BACKEND_{IMAGE,CONTAINER,PORT}` | `BE_{IMAGE,CONTAINER,PORT}` |
| `BACKEND_QUERY_MODE` | `AIVISION_QUERY_MODE` |
| `DIAGNOSIS_{IMAGE,CONTAINER,PORT}` | `AGENTLENS_{IMAGE,CONTAINER,PORT}` |
| `INGEST_GATEWAY_{IMAGE,CONTAINER,HTTP_PORT,GRPC_PORT,HEALTH_PORT}` | `GATEWAY_{IMAGE,CONTAINER,HTTP_PORT,GRPC_PORT,HEALTH_PORT}` |
| `DATA_BACKEND_{IMAGE,CONTAINER,PORT,METASTORE_DIR}` | `SIGNOZ_{IMAGE,CONTAINER,PORT,METASTORE_DIR}` |
| `DATA_BACKEND_PROJECTION_MAINTENANCE_ENABLED` | `SIGNOZ_AIVISION_PROJECTION_MAINTENANCE_ENABLED` |
| `DATABASE_{IMAGE,CONTAINER,BACKEND,HOST,HOST_PORT,PORT,USER,MANAGED}` | `OB_{IMAGE,CONTAINER,BACKEND,HOST,HOST_PORT,PORT,USER,MANAGED}` |

Within one CLI configuration layer the canonical role alias wins. Precedence is
built-in defaults < saved configuration < vars file < environment < command line.
Repeated command-line values use the last occurrence regardless of alias spelling.
Compose `.env` uses the keys expected by the actual template, without inheriting
CLI vars precedence. Reconcile aliases before an upgrade; never rename resources,
DNS, state, selectors or persistent mounts to change their displayed role.

## Native v1 history limits

`AIVISION_NATIVE_TRACE_HISTORY_START` must cover all retained traces before
claiming native v1 read readiness. It is a query boundary, not retention or
deletion configuration. A later bound excludes older data. Docker can otherwise
run the platform without it, but native v1 reads return HTTP 503 / code 3038;
guarded Compose requires a nonempty fixed UTC bound. Never substitute today's
date for unknown retained history.

Compatible backend images split history into windows of at most 31 days, merge
and deduplicate results, and read to current time plus
`AIVISION_NATIVE_TRACE_FUTURE_SKEW_SECONDS` (default `300`).
`AIVISION_NATIVE_TRACE_MAX_WINDOWS` (default `120`) bounds work; exceeding it
fails explicitly instead of returning partial history. A recent 93-day window
does not establish all-history coverage. The fixed Kubernetes CLI does not
accept the history-start configuration; health checks cannot establish v1 reads.

## Release and build identity

A verified release manifest establishes the installed product version and the
expected build identity of each component. Reused components may have older
source SHAs and build-time versions; compare each component to its own manifest
entry. Preserve original image repositories/digests and build provenance when
changing delivery repositories. Component build metadata alone does not establish
a published product release. Update checks compare against the latest stable
Release; a failed network check or absent stable release is not an up-to-date
result and the About page does not perform upgrades.

## Backup and rollback

Before an upgrade, verify business-database migrations on a copy when applicable.
Quiesce application services and diagnosis workers, then use the datastore's
supported consistent backup procedure for business and telemetry databases,
SigNoz metastore and configuration. Record old image identities and retain
telemetry. A vars-file copy or a copy of live SQLite files is not a database
backup. Preserve the metastore's related SQLite/WAL files together.

Backend and diagnosis boot may migrate schemas. Selecting older images after a
schema change is not rollback. Stop services and restore a matching database,
metastore, configuration and image set before restarting. Reverse migrations
cannot recover deleted data. Resolve a missing backup method/destination before
mutation; do not automatically roll back or replace current tables with old DDL.

## Register or sign in

Use the Web URL reported by the deployment, reachable from the user's browser.
For a new local account, open `/register` or choose **Create an account**
from `/login`. Let the user enter their name, email and password. Successful
registration signs them in and provisions a personal Space. Existing users open
`/login`. For a team Space, have them accept its administrator's invitation
and then select it in the Space switcher. If public registration is disabled,
use an authorized account or the team's invitation flow.

For a terminal-based start with a compatible installed `aiv`, run the
registration command or the sign-in command as appropriate, then check access.
Set `ENDPOINT` to the actual platform URL, `EMAIL` to the user's email and
`PROFILE` to a profile for this instance and account.

```sh
# New account. The CLI prompts for a name and a hidden password.
aiv auth register --profile "$PROFILE" --endpoint "$ENDPOINT" --email "$EMAIL"
# Existing account. The CLI prompts for a hidden password.
aiv auth login --profile "$PROFILE" --endpoint "$ENDPOINT" --email "$EMAIL"
aiv auth status --profile "$PROFILE"
aiv space list --profile "$PROFILE"
```

CLI registration signs the user in and selects the personal Space. For a team
Space, use `aiv space use "$SPACE_ID" --profile "$PROFILE"` after joining.
Browser and terminal sessions are separate. Have the user complete prompts
directly and keep passwords, session cookies, installation tokens, SpaceKeys
and model keys out of chat and shared logs.

## Account-based Agent onboarding

This is an alternative to the Web one-use installation authorization, on the
machine/account running the Agent. Inspect installed command help first. Set
`PROFILE`, `ENDPOINT`, `EMAIL`, `SPACE_ID` and a supported `AGENT_PRODUCT` to the
confirmed values; preserve an existing profile/space instead of changing it.

```sh
aiv auth login --profile "$PROFILE" --endpoint "$ENDPOINT" --email "$EMAIL"
aiv auth status --profile "$PROFILE"
aiv space list --profile "$PROFILE"
aiv space use "$SPACE_ID" --profile "$PROFILE"
aiv connect "$AGENT_PRODUCT" --profile "$PROFILE" --dry-run
aiv connect "$AGENT_PRODUCT" --profile "$PROFILE"
```

For a new account use `aiv auth register` with the same endpoint/profile/email;
it prompts for name and hidden password. Honor disabled registration and account
permissions. `--dry-run` reads prerequisites without creating an Agent or
installation authorization, and does not prove reporting. Actual connect creates
or reuses the selected Space's same-type Agent and issues a one-use installation
authorization; keep secrets private. Restart the host Agent, trust hooks where
required, start a new session and confirm its identifiable real trace in the UI.
CLI and browser sessions are separate. Query access separately needs a saved
same-Space SpaceKey; `aiv key import` uses a hidden prompt or `--key-stdin`, while
an authorized administrator can use `aiv key create --name cli`. Neither account
login nor ingest credentials establish query access.

## Native query recovery

Perform this only for an authorized recovery with matching backend/data-backend
builds. Retain original target, namespace, state, datastore and private vars/env.
Set `BACKEND_QUERY_MODE=raw` and reapply the original deployment to bypass derived
reads. If derived writes/schema are faulty, also set
`DATA_BACKEND_PROJECTION_MAINTENANCE_ENABLED=false` on all writers and reapply.
The shared OFF latch survives ordinary restarts. Raw ingestion must continue
through the controlled path; direct SQL imports/restores bypass tracking and
need suspension before and explicit rebuild afterward.

After repairing the cause, set maintenance `true` on every writer and reapply.
Explicit resume needs configured SigNoz admin credentials plus the existing
deployment-internal ingest key. Obtain that key from the original private
configuration through the approved secret procedure. Disable shell tracing;
export it only in the authorized operator shell for the one-shot command below,
then unset it. Never add it to ordinary serving-worker configuration or print it.

For Docker/Compose, resolve the actual backend container name from the original
selector-rich `aiv status` command; default Docker commonly uses `aivision-be`,
while Compose may choose another name. Set `AIV_BACKEND_CONTAINER` accordingly.
Use `/app/manage` in a compatible native backend image:

```sh
test -n "${SIGNOZ_INGEST_INTERNAL_KEY:-}" &&
docker exec --workdir /app --env SIGNOZ_INGEST_INTERNAL_KEY "$AIV_BACKEND_CONTAINER" \
  /app/manage maintain_trace_read_model --resume-maintenance --once
unset SIGNOZ_INGEST_INTERNAL_KEY
```

For a source-compatible Python image, use its confirmed Python management
launcher. Do not add a host Python prerequisite or assume
that the native image includes `/app/.venv/bin/python`.

Resume clears rebuildable derived records and increments shared generation;
raw Spans remain. The worker reenrolls and catches up afterward. Verify the same
fixed-window queries, complete counts, retained data, and known zero versus
missing Token usage before restoring `BACKEND_QUERY_MODE=auto` through the
original lifecycle command. Health and enrollment completion alone do not prove
complete coverage. A failed/interrupted recovery remains unresolved; preserve
its evidence and correct the cause before another authorized attempt.

### Kubernetes recovery

Retain context, namespace, PVCs and original private vars; reapply `true` on all
writers with the fixed CLI. Export the existing single-line internal key only
in the operator shell with tracing off. Replace context and namespace below;
the physical Deployment/container names remain `aivision-be` / `be`:

```sh
test -n "${SIGNOZ_INGEST_INTERNAL_KEY:-}" &&
printf '%s\n' "$SIGNOZ_INGEST_INTERNAL_KEY" |
  kubectl --context YOUR_CONTEXT --namespace YOUR_NAMESPACE \
    exec -i deployment/aivision-be -c be -- /bin/sh -c \
    'IFS= read -r SIGNOZ_INGEST_INTERNAL_KEY || exit 1; export SIGNOZ_INGEST_INTERNAL_KEY; cd /app && exec /app/manage maintain_trace_read_model --resume-maintenance --once'
unset SIGNOZ_INGEST_INTERNAL_KEY
```

The key enters only this process by stdin; no serving Pod environment or
bootstrap Job changes. Verify fixed queries and complete coverage before
reapplying `BACKEND_QUERY_MODE=auto`. This procedure does not add database
combinations, replicas or native v1 history support, or establish live-cluster
acceptance.
