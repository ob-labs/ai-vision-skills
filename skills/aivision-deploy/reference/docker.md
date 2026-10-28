# Docker target

Depth for the Docker path of the [`aivision-deploy`](../SKILL.md) skill: the one
command, the datastore variants, and a second stack on the same host. Read this
after settling that the target is Docker (the default answer).

For a new deployment, offer **OceanBase CE (default)** and **OceanBase seekdb
(lightweight option)**, plus reuse of an existing database, following the
[datastore selection flow](../SKILL.md#choose-the-docker-datastore--oceanbase-ce-by-default).
An explicit request for the default selects CE; an existing choice or saved
deployment configuration is reused without another selection question. Save the
chosen `OB_BACKEND` in the private vars file and keep it on retries and upgrades.

Host requirements — the Docker daemon, the selected datastore resources and the
network access — are in [prerequisites](prerequisites.md), together with the
required CLI installation and conditional registry login.

## The one command — bundled OceanBase

First [prepare the fixed history start](../SKILL.md#fix-the-history-start-before-the-first-docker-cast)
in `./aivision.vars.yaml`. Generate it once only for confirmed empty storage;
reuse the saved timestamp for retained data and all subsequent casts. Merge the
selected published Release or Daily's [verified image variables](prerequisites.md#resolve-the-version-and-download-matching-assets)
into that same private file, preserving its other settings. For explicitly
requested source images, follow [source build identity and verification](prerequisites.md#source-build-identity-and-verification)
and use `IMAGE_PULL=missing` in the command below for unpublished local images.

```bash
aiv cast --vars-file ./aivision.vars.yaml --var IMAGE_PULL=always
aiv status
```

Run this after the host and CLI checks in [prerequisites](prerequisites.md).
Image access requires registry login only for restricted images; skip that step
when the images are public or the host already has valid access.

## What that one command does

`aiv cast` pulls each component's released image, starts the six containers in
dependency order, waits for every health check to pass, runs the datastore
bootstrap, bootstraps the backend's data-backend integration, and discovers the org id
the downstream components need. Nothing is cloned or compiled on the host.
The host needs both Docker and the `aiv` CLI, plus the resources and network
access listed in the prerequisites.

It is idempotent and safe to re-run: containers are replaced, **data is
preserved** (the selected datastore volumes and the data-backend metastore survive). Only
`aiv destroy --purge` deletes data.

| Component | Role | Default host port |
|---|---|---|
| `database` | Bundled OceanBase CE or seekdb (skipped when `OB_MANAGED=false`) | 2881 |
| `data-backend` | Telemetry storage and query | 18091 |
| `ingest-gateway` | Authenticated OTLP ingestion | 4318 (gRPC 4317, health 13133) |
| `backend` | Platform API | 8001 |
| `diagnosis` | Diagnosis engine | 8081 |
| `frontend` | Web entry point | 5174 |

Read the deployed values back from `aiv status` rather than assuming them.
These are role names in the current source CLI. Existing `be`, `fe`,
`agentlens`, `antcollector-gw`, `signoz` / `signoz-ob` and `oceanbase` selectors
remain compatibility aliases; physical names and persisted identities are retained.
CLI role configuration aliases follow [the bundled mapping](operations.md#component-names-and-configuration);
within one config layer the role key wins, while later layers and repeated CLI
flags retain their existing precedence.

## Variants — only these change the command

| Situation | Change |
|---|---|
| Bundled OceanBase CE (default) | `OB_BACKEND=oceanbase` — use the command above |
| Bundled OceanBase seekdb (lightweight option) | merge the verified `release-seekdb.vars.yaml`, including its backend and database image |
| An OceanBase CE or seekdb you already run | keep `OB_MANAGED: "false"` and existing connection settings in that vars file; use `OB_BACKEND=seekdb` for seekdb |
| Install a Release or Daily | Resolve a versioned Release and merge its verified vars, including `AIVISION_RELEASE_MANIFEST_BASE64`, into the same private vars file |
| Kubernetes | `--target kubernetes --context <context>` — see [kubernetes](kubernetes.md) |
| A second, isolated stack on the same host | `--namespace <name>` plus the port overrides below |

### Bundled OceanBase seekdb

Managed seekdb requires the Docker `aiv cast` lifecycle or the new
[product Compose lifecycle](#product-compose-source-version). Older generic
Compose exports omitted initialization and are not installation recipes.
Generic Kubernetes/systemd generation still does not support managed seekdb.

Use the matching CLI from a published build containing `OB_BACKEND` support, or
the explicitly requested matching source build. For published builds, merge
`release-seekdb.vars.yaml` from that build into the same private vars file.
Keep the same history-start preparation; the verified vars asset sets both the
seekdb selector and its corresponding database image. For a source build, save
`OB_BACKEND: "seekdb"` and the validated `OB_IMAGE` explicitly; preserve the
selected local service images and use `IMAGE_PULL=missing` instead of `always`
below when they are unpublished:

```bash
aiv cast --vars-file ./aivision.vars.yaml --var IMAGE_PULL=always
aiv status
```

The vars file retains `OB_BACKEND: "seekdb"`. Set `OB_TENANT_PASSWORD`
privately before the first cast, using letters, digits, `_`, and `-`. seekdb uses
`root` without a tenant. A new empty managed volume is initialized in a dedicated
internal network without published ports, using that password before normal
startup; existing volumes retain their
password. Changing the variable does not rotate a database password.

The default pinned seekdb image is Linux/amd64. ARM hosts need Docker emulation
or an independently validated image supplied through `OB_IMAGE`; do not claim
native ARM verification. Resource defaults are 2 CPU, 2G memory, a 2G datafile,
and 2G log disk, configurable through `SEEKDB_CPU_COUNT`, `SEEKDB_MEMORY_LIMIT`,
`SEEKDB_DATAFILE_SIZE`, and `SEEKDB_LOG_DISK_SIZE`. These cover the database only.

Data lives in `aivforge-seekdb-data-${NAMESPACE}`, mounted at `/var/lib/seekdb`.
OceanBase CE volumes cannot be reused for seekdb. The CLI rejects backend changes
within an existing namespace: use a new deployment and migrate data explicitly.
Kubernetes uses OB Operator and does not support this selector.

### Reusing an existing OceanBase

For a new config file, generate the override template and fill in the real
values. If a vars file already exists, edit it instead of regenerating it:

```bash
aiv gen --vars -o ./aivision.vars.yaml   # comment-only; uncomment what you change
```

```yaml
OB_MANAGED: "false" # Keep false to reuse the existing database.
OB_HOST: "YOUR_OB_HOST"
OB_HOST_PORT: "2881"
OB_TENANT: "aivision"
OB_TENANT_PASSWORD: "REPLACE_WITH_TENANT_PASSWORD"
AIVISION_NATIVE_TRACE_HISTORY_START: "REPLACE_WITH_EARLIEST_RETAINED_TRACE_UTC"
```

Replace the history placeholder with a confirmed ISO UTC timestamp at or before
the earliest retained trace. If the start is unknown, inspect the retained data
or ask the operator; do not use today's date for an existing datastore. For an
existing but verified-empty datastore, generate the UTC day's start once with
`date -u +%Y-%m-%dT00:00:00Z` and put that literal value into the existing template;
do not run the file-creation command over it.

```bash
chmod 600 ./aivision.vars.yaml
aiv cast --vars-file ./aivision.vars.yaml --var IMAGE_PULL=always
aiv status
```

The same thing as flags, for a one-off:

```bash
export OB_PW='…'
aiv cast --vars-file ./aivision.vars.yaml \
  --ob-host 10.0.0.5 --ob-tenant aivision --ob-password-env OB_PW
```

- `OB_MANAGED: "false"` is what selects the existing-datastore mode; `--vars-file`
  only loads values.
- The tenant must be in MySQL mode and its `root@<tenant>` account must be able
  to create and migrate the `aivision`, `signoz` and `agentlens` databases.
- `127.0.0.1` inside a container is that container, so `OB_HOST` must be an
  address containers can reach (the host's real IP or the Docker bridge gateway).
- Passwords are interpolated into connection strings without escaping — use
  letters, digits, `_` or `-` only.
- Prefer `AIV_VAR_OB_TENANT_PASSWORD=…` in the environment, or
  `--ob-password-env` / `--ob-password-file`; a vars file containing credentials
  must remain private with mode `600` and outside version control.
- `aivision.vars.yaml` is git-ignored. Keep it that way and never commit it.
- Overrides persist after a successful cast, so later `status`, `logs`,
  `destroy` and `redeploy` reuse them when given the same namespace, state root
  (`--workdir`, if customized), and blueprint (`--file`, if customized).
  Precedence, lowest to
  highest: blueprint < persisted overrides < `--vars-file` < `AIV_VAR_<KEY>`
  environment < `--var` / `--ob-*` flags.

### Reusing an existing seekdb

In the same private vars file, replace the database settings with:

```yaml
OB_BACKEND: "seekdb"
OB_MANAGED: "false"
OB_HOST: "YOUR_SEEKDB_HOST"
OB_HOST_PORT: "2881"
OB_TENANT_PASSWORD: "REPLACE_WITH_SEEKDB_PASSWORD"
# OB_USER: "aivision" # Optional existing account; root is the default.
```

Keep the confirmed history start and other settings. `OB_TENANT` is not needed.
The selected account must be able to create and migrate all three application
databases. Run the same `cast --vars-file` command above; alternatively add
`--var OB_BACKEND=seekdb` to the `--ob-host` example and omit `--ob-tenant`.
The CLI probes seekdb with the selected account, without a tenant suffix. The
same password restrictions and container network requirements apply.

### A second, isolated stack on one host

Prepare a separate vars file in a separate deployment directory using the
history-start rules above. Confirm the new namespace's volumes are absent or
empty before generating a new timestamp; reused volumes keep their original
history start.

```bash
aiv cast --namespace aivtest --vars-file ./aivision.vars.yaml \
  --var DATABASE_CONTAINER=aivtest-database \
  --var DATA_BACKEND_CONTAINER=aivtest-data-backend \
  --var INGEST_GATEWAY_CONTAINER=aivtest-ingest-gateway \
  --var BACKEND_CONTAINER=aivtest-backend --var FRONTEND_CONTAINER=aivtest-frontend \
  --var DIAGNOSIS_CONTAINER=aivtest-diagnosis \
  --var OB_PORT=2891 --var SIGNOZ_PORT=18092 \
  --var GATEWAY_GRPC_PORT=4327 --var GATEWAY_HTTP_PORT=4328 --var GATEWAY_HEALTH_PORT=13143 \
  --var BE_PORT=8011 --var AGENTLENS_PORT=8091 --var FE_PORT=5184
```

Each namespace bootstraps its own org, so no tenant id is shared. Change the whole
port set together — a partial override is how a second stack collides with the
first one.

Each bundled datastore needs its own resource allocation: OceanBase CE needs
roughly 6 GB of RAM; seekdb defaults to 2 CPU and 2G memory plus its data/log
disks. Other services need additional resources. Several stacks on one host each
run their own datastore unless pointed at an existing shared database.

## Verify and rerun

For an existing-version upgrade, follow the [upgrade workflow](upgrade.md).
Its known legacy data-backend stop recovery is separate from a failed database
stop; do not apply it to the database or to Compose stop records.

If a managed database failed to stop, repeating `cast` must still block its
replacement and seekdb offline initialization. The source CLI records the exact
container ID in private `state/lifecycle-stops/database-id`. Inspect the failed
container, then restart and stop it successfully or explicitly remove only that
container after diagnosis, preserving its volumes. Do not delete the stop record
to bypass the check; an unrelated startup failure remains retryable.

Use the skill's [verification steps](../SKILL.md#verify-docker--never-report-success-without-this),
including authenticated Langfuse v1 reads. The initial Docker cast persists the
history start after a successful cast; retain the vars file as well, including
after a partially failed first deployment. **Retry a failed cast with its full
original command**, including container names, ports, registry, tag and other
overrides that may not yet have been saved. Alternatively, keep all overrides
in the private vars file from the start. For an upgrade, first merge the selected
version's verified vars into the original private file, including all five
service image digests and `AIVISION_RELEASE_MANIFEST_BASE64`. Then reuse the same
namespace and deployment directory with that updated file:

```bash
aiv cast --namespace aivtest --vars-file ./aivision.vars.yaml \
  --var IMAGE_PULL=always
aiv status --namespace aivtest
```

Replace `aivtest` with the original namespace. If the original cast used a
custom state root, include it on every command; for example, for a deployment
whose state root is `$HOME/aiv-state`:

```bash
aiv status --namespace aivtest --workdir "$HOME/aiv-state"
aiv logs --namespace aivtest --workdir "$HOME/aiv-state" -n 80 backend
```

Retain `--file` as well when using a custom blueprint. Changing the current
directory can change the auto-selected blueprint (`./blueprint.yaml` or
`./blueprints/aivision.yaml`), so return to the original directory or pass its
absolute `--file` path. Neither a new directory nor a new state root proves
that the database volumes are empty.

Do not rerun the date-generation step. If using `--reset-vars`, explicitly
reapply this file and any other original deployment overrides.

After verification, introduce the optional
[trace and metric query skills](../SKILL.md#after-deployment-help-the-user-use-their-data).
If the deployment has no application telemetry, guide the user through Agent
onboarding and a real task first. If data already exists, preserve this
endpoint, space and Agent context when handing off to a query skill; query
access requires the matching profile and its space-scoped SpaceKey. Installing
only `aivision-deploy` does not install the query skills automatically.

## Serving users beyond the local host

`BIND_ADDR` defaults to `127.0.0.1`, a local-only deployment. Override the
built-in `*_SECRET` / `*_PASSWORD` values (`OB_TENANT_PASSWORD`,
`OB_SYS_PASSWORD`, `SIGNOZ_USER_ROOT_PASSWORD`, `AIVISION_INGEST_SECRET`, …)
**before** exposing it:

```bash
aiv cast --vars-file ./aivision.vars.yaml \
  --var BIND_ADDR=0.0.0.0 --var PUBLIC_HOST=YOUR_REACHABLE_HOST
```

Replace `YOUR_REACHABLE_HOST` with the deployment host's reachable IP or DNS name,
without a URL scheme or port. Keep the original namespace, state root, blueprint
and other deployment overrides on this cast, including the saved history start.
`PUBLIC_HOST` is what the backend hands to browsers and the Agent market, so both
the Web port (`FE_PORT`, default `5174`) and OTLP HTTP port
(`GATEWAY_HTTP_PORT`, default `4318`) must be reachable from the Agent machine.
Use `http://YOUR_REACHABLE_HOST:FE_PORT` (with the actual values) for onboarding;
install and connect the collection plugin on the machine running that Agent.

## Product Compose (source version)

Compose is optional. Default Docker remains supported through the Go runtime;
current source adds explicit --target compose, also controlled in Go. Use a
confirmed matching CLI and Compose2.27+ with Docker and matching images. There
is no host Python or extra controller file. Native delivery images provide
their bootstrap executables with `NATIVE_PYTHON_RUNTIME: "true"`; older
Python-based images retain their matching mode. A dev tag or OB_BACKEND does not prove
the installed CLI supports the target.

For a new CLI Compose installation, prepare original private vars/history/images
as above, then use the permanent `aiv` installation:

```sh
aiv cast --target compose --namespace aivision --vars-file ./aivision.vars.yaml
aiv status --target compose --namespace aivision
aiv logs --target compose --namespace aivision -n 100 backend
```

Keep the target and original namespace/workdir/blueprint selectors on every
operation; without it the CLI selects default Docker. Read the actual immutable
private bundle path from cast/status. Change configuration through original
vars/flags and cast, not generated-file edits. Status/logs/destroy use the saved
exact bundle rather than new defaults or ambient variables.

For optional low-level read-only native inspection, replace the path and project
name with the actual bundle and original namespace:

```bash
AIV_COMPOSE_BUNDLE=/absolute/path/reported/by/aiv
AIV_COMPOSE_PROJECT=aivision
docker compose --project-name "$AIV_COMPOSE_PROJECT" --file "$AIV_COMPOSE_BUNDLE/compose.yaml" \
  --env-file /dev/null config --quiet
docker compose --project-name "$AIV_COMPOSE_PROJECT" --file "$AIV_COMPOSE_BUNDLE/compose.yaml" \
  --env-file /dev/null ps --all
docker compose --project-name "$AIV_COMPOSE_PROJECT" --file "$AIV_COMPOSE_BUNDLE/compose.yaml" \
  --env-file /dev/null logs --tail 100 frontend
```

Config --quiet avoids printing resolved secrets. Standalone parameterized files
use their original actual env, not /dev/null. Mutations use the same Go guard:

```bash
aiv cast --target compose --compose-file /absolute/path/compose.yaml \
  --compose-env-file /absolute/private/compose.env
aiv status --target compose --compose-file /absolute/path/compose.yaml \
  --compose-env-file /absolute/private/compose.env
aiv logs --target compose --compose-file /absolute/path/compose.yaml \
  --compose-env-file /absolute/private/compose.env -n 100 backend
```

Use the original actual file/env; --compose-env-file defaults to .env. Resolved
exports use /dev/null. This mode derives state/identity from YAML and cannot mix
namespace/workdir/vars-file/var/blueprint options. It does not automatically import
standalone values into CLI vars. For parameterized templates edit original env;
for resolved exports regenerate from original private vars.

Go invokes native Compose while retaining identity/ownership, shared locks,
isolated seekdb initialization, initialization-task reruns and exit/OOM checks
before deletion. Native inspection does not prove bare up/down equivalent.
Existing Docker ownership is not automatically converted. Preserve original
credentials, fixed UTC history bound, metastore, organization and volume/network
identity. Backend integration shares only the organization ID with diagnosis.
Required SQL readiness does not prove authenticated telemetry acceptance.

For an authorized rebuild or data-preserving stop, retain the exact selectors:

```sh
aiv redeploy --target compose --compose-file /absolute/path/compose.yaml \
  --compose-env-file /absolute/private/compose.env
aiv destroy --target compose --compose-file /absolute/path/compose.yaml \
  --compose-env-file /absolute/private/compose.env
```

CLI-managed projects instead retain their original target, namespace, workdir
and blueprint selectors. Compose purge
removes named volumes but retains bind-mounted metastore, identity and config;
default Docker purge retains its original managed-volume plus namespace-state
removal. Neither clears external databases. Compose rejects redeploy --purge and
--purge-repos before changes. Failed stops block purge and keep exact container
IDs; do not delete records or data to bypass the guard.

The four supported combinations are bundled/external OceanBase CE and
bundled/external seekdb. Use the matching CLI's embedded assets; standalone
files must already exist and match that version. Installing this Skill does
not supply Compose templates or authorize downloading private product source.
Record actual new Go controller/native-inspection runtime evidence separately
from the earlier source-candidate matrix; static checks and same-image recast
are not cross-release upgrades. Follow the shared authenticated verification
for new and retained traces, organization identity, canaries, mounts and image IDs.

## Agent machine onboarding

Check the [native Agent client runtime](prerequisites.md#native-agent-client-runtime)
on the Agent machine first. This Daily's installer requires Linux x64 with glibc
2.35 or newer; Debian Bookworm is the qualified client runtime. The Docker host
and Agent client can be different machines with different runtime libraries.

Use the machine and user account that run the target coding Agent:

1. Complete the [CLI check or installation](prerequisites.md#find-the-cli-before-installing)
   there first, and verify `command -v aiv` and `aiv --version` in the same
   terminal. Run `aiv connect --help` and confirm it supports `--base-url`,
   `--space-id`, `--agent-uuid` and `--installation-token` for the Web command.
   Check any optional flags the user needs, such as `--config-dir` or
   `--collection-mode`. If a required command or flag is missing, follow the
   [CLI installation or upgrade steps](prerequisites.md#install-or-upgrade-the-cli-when-needed)
   and repeat the help check before generating an authorization.
   Use the selected Daily's native Agent installer; it does not require
   user-installed Python. Confirm the deployed platform actually serves that
   native installer before continuing. An older Python-based hook is a separate
   compatibility path, not a reason to add a Python prerequisite to this native
   flow. The host Agent must be installed and configured.
2. Open the deployed Web URL, register/sign in, and choose the target Agent's
   onboarding guide. Generate the installation command **after** the client
   prerequisites are ready. Run that complete command unchanged in the Agent
   machine's terminal. This Web-issued command contains an explicit one-use
   installation authorization and does not require `aiv auth login`. It expires
   after 15 minutes; if rejected as expired or already used, generate a new
   command in the Web guide. Keep the command and its token out of chat/logs.
3. Restart the host Agent and start a new session. For Codex, inspect and trust
   the new hooks through `/hooks`, then perform a real task. In the deployed Web
   UI, find that Agent's new trace and check its task/time against the task just
   run. Installation completion alone does not prove reporting.

For this Web-token path, use the actual platform trace as the reporting check;
it does not automatically create an account CLI profile. If the user prefers
account-based CLI onboarding instead, follow the separate
[bundled CLI account flow](operations.md#account-based-agent-onboarding)
with this deployment's reachable endpoint. Choose one onboarding path; querying
later has its own profile and SpaceKey requirements.

## Native query maintenance and emergency recovery

On matching candidate builds, the backend supervises Gunicorn and continuous projection maintenance together; historical enrollment needs no per-Space process. Deployment keys `BACKEND_QUERY_MODE=auto` and `DATA_BACKEND_PROJECTION_MAINTENANCE_ENABLED=true` are normal defaults. Legacy application names `AIVISION_QUERY_MODE` and `SIGNOZ_AIVISION_PROJECTION_MAINTENANCE_ENABLED` remain aliases, not additional switches.

For an authorized recovery, preserve the existing private vars file or Compose `.env`, namespace and datastore. `raw` bypasses derived reads; `false` persists shared maintenance suspension. Reapply through the original CLI target (`aiv cast --target compose ...` for Compose). Restoring `true` cannot clear suspension: use the [explicit operator sequence](operations.md#native-query-recovery), injecting the existing internal ingest key only into that command. Do not export it to normal backend services. Check fixed queries, full counts and known-zero versus missing usage afterward; a healthy API alone does not prove complete projections. Candidate tests and released-image capabilities remain separate evidence.
