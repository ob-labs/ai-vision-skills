---
name: aivision-deploy
description: Use when a user wants to install, verify, or upgrade AI Vision with Docker, Compose, Kubernetes, or All-in-One, or needs help registering and getting started on a deployment they just set up.
---

# AI Vision Deployment

Use the selected target and its maintained lifecycle entry point. Deployment
assets and the CLI are distributed through
[AI Vision Releases](https://github.com/antgroup/ai-vision/releases).

## Choose a deployment mode

| Situation | Start here |
|---|---|
| First try or personal use on a Linux x86-64 or ARM64 Docker host | Recommend [All-in-One Preview](reference/all-in-one.md) when a verified bundle matches the host. One container includes the platform and embedded seekdb, with data in one named Docker volume. After startup, follow [the first-use handoff](#help-the-user-sign-in-and-get-started). |
| New shared deployment, an external database, or an explicit distributed Docker, Compose or Kubernetes target | Follow the distributed deployment below, including its supported platforms and datastore choices. |
| Existing instance | Keep its mode, datastore and identity. Use the [All-in-One operations guide](reference/all-in-one.md#stop-restart-or-recreate) for an existing preview or the [distributed upgrade workflow](reference/upgrade.md) for an existing distributed installation. |

Check the Docker host separately from the browser or Agent machine. If no
verified preview bundle matches the Linux host, check the distributed target's
platform support or use an eligible Linux VM for the trial. Honor an explicit
deployment or version choice. The steps below apply to distributed deployments.

## Upgrade an existing installation

For an upgrade request, use the [existing-installation workflow](reference/upgrade.md)
before the new-install steps below. Let the matching `aiv` CLI perform the
lifecycle. Preserve the original target, namespace, state, datastore, credentials
and history bound; resolve one published product version for all five images.
Continue routine preparation, upgrade and verification under the user's existing
authorization, without repeating choices they already made. The reference also
covers the narrowly verified stopped legacy data-backend recovery and the
conditions that require stopping for specific missing information. It does not
make upgrades zero-downtime or replace a database backup.

## Choose Release or Daily

For an explicitly requested source deployment or local validation, use that
checkout and matching images instead of selecting a published channel. Follow
[source build identity and verification](reference/prerequisites.md#source-build-identity-and-verification);
local evidence does not establish a published Release or Daily.

For a new deployment with no version preference, offer **Release** (the default,
latest published stable version) or **Daily** (latest successfully published
preview build). Honor an explicit version or channel without asking again.
If the user delegates the choice, use Release. For an existing deployment,
inspect its saved configuration and actual version first; retries keep that
combination, and upgrades use the channel or version the user requested.

Resolve a **published versioned Release** in `antgroup/ai-vision` before
installing. For Release, use the latest compatible stable `vX.Y.Z` Release.
For Daily, use a compatible versioned `vX.Y.Z-daily.YYYYMMDD[.N]` prerelease.
A rolling pointer can help discovery; install using the exact versioned tag.
Verify the matching CLI, datastore vars file and manifest. The deployment host
and Agent clients can use different platforms. Follow
[version resolution and asset verification](reference/prerequisites.md#resolve-the-version-and-download-matching-assets).

If a channel has no compatible publication, name the missing tag, asset, or
platform. For an unpinned trial, check the official distributed Release if
All-in-One is absent. Offer an existing platform or the explicitly requested
[source deployment path](reference/prerequisites.md#source-build-identity-and-verification)
when available. Keep a requested version fixed across retries.

## Decide the environment first

Use the target the user already requested or the existing deployment uses.
For a new deployment with no target specified, offer the choices below; the
entry points differ and Kubernetes needs a cluster that already exists:

| Target | What it requires | Command shape | Depth |
|---|---|---|---|
| **Docker** (default, the usual answer) | a running Docker daemon | `aiv cast --var …` | [reference/docker.md](reference/docker.md) |
| **Docker Compose** (optional, current source) | Matching aiv, Docker, Compose 2.27+, matching deployment assets/images; no host Python/controller | `aiv cast --target compose …` | [product Compose](reference/docker.md#product-compose-source-version) |
| **Kubernetes** | `kubectl` plus an existing cluster: Kubernetes 1.33–1.36, admin rights, a default StorageClass, ≥4 CPU / 16Gi and ~140Gi disk | `aiv cast --target kubernetes --context <ctx> --vars-file ./aivision.k8s.vars.yaml` | [reference/kubernetes.md](reference/kubernetes.md) |

For Compose, retain `--target compose` on every CLI operation. The Go CLI calls
native Compose with lifecycle guards. Follow the
[Compose recipe](reference/docker.md#product-compose-source-version) or the
[Kubernetes recipe](reference/kubernetes.md) for your target, then return to the
[first-use handoff](#help-the-user-sign-in-and-get-started). The remaining
deployment commands on this page apply to Docker. Kubernetes supports bundled
OceanBase CE through OB Operator. Check its limits on datastore selection and
Langfuse v1 reads in the Kubernetes recipe.

Helm deployment is a committed follow-up and is currently unavailable. This
delivery provides no product Chart or supported Helm commands; use the fixed
Kubernetes CLI path. Future Helm work does not provide a runnable installation
or automatic adoption of existing resources.

Use `frontend`, `backend`, `diagnosis`, `ingest-gateway`, `data-backend` and
`database` as product component names. The bundled [component compatibility](reference/operations.md#component-names-and-configuration)
records aliases and implementation names.
Existing resource names, service DNS, state and volume bindings remain stable.
The data-backend image must provide `/api/v1/ready` and native
`/app/signoz healthcheck --ready`, backed by a bounded telemetry-store `SELECT 1`.
Database failure affects readiness, while plain `/api/v1/health` remains local
liveness. Reject incompatible images instead of weakening these probes.
An older released CLI may still display old aliases; check its actual capabilities
before using new role selectors or new generation commands. Do not automatically
adopt an existing CLI installation into Compose.

## Prepare the CLI and deployment location

Before any `aiv` command, follow [prerequisites](reference/prerequisites.md):
keep the CLI in a stable installation directory, complete durable shell PATH
setup, and verify `aiv` in a fresh supported terminal. An export in the current
task or a binary left only under `tools/` does not finish installation. Reuse an
installed CLI when compatible, verify its version against the selected manifest
(or the recorded source build), and check
the runtime for the selected target. Install or upgrade when required to match the selected build.
Deployment does not require an AI Vision account login.

For Docker, run the deployment commands on the host that will run the stack.
If the coding Agent runs on another machine, use the deployment host for `cast`
and its local checks; follow [Agent machine onboarding](reference/docker.md#agent-machine-onboarding)
on the Agent's own machine afterward. Configure [remote access](reference/docker.md#serving-users-beyond-the-local-host)
before that Agent connects; its `127.0.0.1` is a different machine.

Keep configuration in a durable deployment directory, outside source control;
for a new deployment, for example:

```bash
mkdir -p "$HOME/aivision-deploy"
cd "$HOME/aivision-deploy"
```

For an existing deployment, return to its original directory and reuse its
configuration. The Docker examples below use the built-in blueprint, namespace
`aivision`, and state root `~/.aivision/forge`. If the deployment uses
`--namespace`, `--workdir`, or `--file`, repeat those selectors on **every**
deployment command, including `status` and `logs`; they are not saved in the vars
file. See the [custom-deployment example](reference/docker.md#verify-and-rerun).

A failed managed-database stop blocks replacement and seekdb offline
initialization on subsequent retries. Follow the [stop recovery instructions](reference/docker.md#verify-and-rerun)
and preserve its volumes and ID-bound stop record until the failure is resolved.

## Choose the Docker datastore — OceanBase CE by default

For a **new Docker deployment**, make both bundled options visible:

| Datastore | Configuration |
|---|---|
| **Bundled OceanBase CE (default)** | `OB_BACKEND=oceanbase`; about 6 GB RAM and 10 GB disk for the database. |
| **Bundled OceanBase seekdb (lightweight option)** | `OB_BACKEND=seekdb`; defaults to 2 CPU, 2G memory, 2G datafile, and 2G log disk for the database. |
| Existing OceanBase CE or seekdb | Supply a container-reachable host, port and password; OceanBase needs a MySQL tenant, seekdb uses `root` or an explicit `OB_USER`. |

When no preference has been given, offer a short choice in the user's language:
“Which database would you like: OceanBase CE (default), OceanBase seekdb
(lightweight), or an existing database?” Explain the database resource defaults
above so the user can choose. OceanBase CE stays the default; do not silently
select seekdb because the machine has fewer resources.

- If the user asks for the default or delegates the choice, use OceanBase CE.
- If the user already chose CE, seekdb, the lightweight option, or an existing
  database, honor that choice without asking again.
- For retries, upgrades or an existing deployment, read its original vars file
  and saved deployment state first and preserve the backend. Do not present a
  fresh choice or switch an existing namespace; changing backend requires a
  new deployment and explicit data migration.

Record a new deployment's choice as `OB_BACKEND: "oceanbase"` or
`OB_BACKEND: "seekdb"` in its private vars file prepared below. Retain that
selection across subsequent casts, together with the fixed history start.

Other platform services need additional resources. Use the selected manifest's
fixed upstream seekdb digest and confirm its platform index includes the actual
Docker daemon architecture. A CLI archive alone does not establish native
seekdb support; a missing child must be resolved before deployment.
Use the matching CLI from the selected Release and confirm `OB_BACKEND` support
when choosing seekdb; see [prerequisites](reference/prerequisites.md).

## Fix the history start before the first Docker cast

Native Langfuse v1 reads require `AIVISION_NATIVE_TRACE_HISTORY_START`, a fixed
UTC timestamp covering **all retained traces**. Set it before accepting telemetry.

| Datastore state | History start |
|---|---|
| Confirmed empty, with no reused volumes or restored telemetry | Generate the current UTC day's start once, using the preparation below. |
| Existing deployment | Reuse its original vars file or the saved value shown by `aiv status --namespace <name>`. |
| Retained data, but no configured start | Inspect the earliest retained trace timestamp or ask the operator for a confirmed bound; use that timestamp or an earlier bound. Do not substitute today's date. |

For **confirmed empty storage only**, run this once in a new deployment directory:

```bash
(umask 077; set -C
  printf 'AIVISION_NATIVE_TRACE_HISTORY_START: "%s"\n' \
    "$(date -u +%Y-%m-%dT00:00:00Z)" > ./aivision.vars.yaml
)
```

This creates a private config file and refuses to overwrite an existing one.
If the file already exists, inspect and reuse it; add a missing history value
according to the table. A new namespace alone does not prove the datastore is
empty. Keep the literal timestamp across retries, upgrades, restarts and
`--reset-vars`; do not regenerate it or replace it with a sliding time window.
For retained history whose start is unknown, resolve the bound before claiming
Langfuse v1 readiness. See the [bundled history limits](reference/operations.md#native-v1-history-limits). The current Kubernetes path has a separate
[configuration limitation](reference/kubernetes.md#native-langfuse-v1-limitation).

## The one command — Docker, bundled OceanBase CE or seekdb

For a published build, merge the selected Release's verified image variables into this **one private
vars file**, preserving the datastore, password, fixed history start, addresses
and ports. Use the CE or seekdb asset for that selected backend; see
[matching assets](reference/prerequisites.md#resolve-the-version-and-download-matching-assets).
Use the selected base's five exact service digests, including SigNoz, and its
`AIVISION_RELEASE_MANIFEST_BASE64`. Match the runtime configuration to the CLI
and images. The standard release uses source-compatible images and CLI. For
explicitly requested local images, keep their recorded references and use
`IMAGE_PULL=missing` instead of `always` below when
those images exist only on this host.

```bash
aiv cast --vars-file ./aivision.vars.yaml --var IMAGE_PULL=always
aiv status
```

For seekdb, use the verified seekdb vars asset, which sets `OB_BACKEND: "seekdb"`
and the matching database image. Configure its `OB_TENANT_PASSWORD` before
the first cast; no tenant is needed. Managed seekdb initializes the password only
on a new empty volume and keeps existing credentials on retries and upgrades.
See [the Docker reference](reference/docker.md#bundled-oceanbase-seekdb) for storage
and backend-switching boundaries.

Check image access as described in [prerequisites](reference/prerequisites.md).
Registry login is needed only for restricted images; database credentials still
depend on the selected datastore.

`aiv cast` pulls each component's released image, starts the six containers in
dependency order, waits for every health check to pass, runs the datastore
bootstrap, bootstraps the backend's data-backend integration, and discovers the org id
the downstream components need. Nothing is cloned or compiled on the host.
After installing the `aiv` CLI, Docker is the required runtime. The cast is
idempotent and safe to re-run:
containers are replaced, **data is preserved** — only `aiv destroy --purge`
deletes data.

The component list, their default host ports and the datastore variants
(seekdb, existing databases, a second isolated stack on one host) are in
[reference/docker.md](reference/docker.md). Read the deployed values back from
`aiv status` rather than assuming them.

## Verify Docker — never report success without this

Use the same namespace, state root and blueprint as the cast. After a failed
first cast, also pass the original vars file and overrides to diagnostics;
they may not have been persisted yet. The commands below show the defaults:

```bash
aiv status                 # every component must be running and ok
aiv logs -n 80 backend          # backend startup errors surface here
AIV_WEB_URL=http://127.0.0.1:5174 # replace with the deployed Web URL
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' "$AIV_WEB_URL"
```

For live troubleshooting, optionally run `aiv logs backend -f` and stop following
with Ctrl+C before continuing verification. Use `-f` in examples for compatibility
with older clients; check the installed CLI help for other aliases.

Success means all enabled components (six with either bundled datastore, five with
`OB_MANAGED=false`) report `running` with `ok` health, the web port answers,
and the user can open the deployed Web URL. Verify signed-in access and
telemetry with the steps below. A component that is `running` but not `ok`, or a
container that restarted, is not a finished deployment — read `aiv logs
<component>` and report the real state.

Use the [account setup](reference/operations.md#register-or-sign-in) at the deployed
Web URL. Once signed in, open **Help → About** or `/about`. For a published
build, compare the current version with `release-manifest.json` and expand
Diagnostics to compare the actual frontend and backend builds with their own
expected manifest entries. Reused components may have different older SHAs and
build-time versions; that is valid when the release record expects them. Missing
release metadata means an unknown product release. Record a mismatch instead of
inferring success from an image tag. A Daily
build shows its full derived version; **Check for updates** compares against the
latest stable Release, not the next Daily. No stable release or a failed network
check does not mean the deployment is up to date. The page does not upgrade it.
For source validation, apply the [source identity checks](reference/prerequisites.md#source-build-identity-and-verification)
instead of expecting a published release record.

Read the frontend port and effective `PUBLIC_HOST` from the deployment settings
and `aiv status`; `5174` is only the default. For another machine, also check the
public Web URL from the browser/Agent host and use that reachable endpoint for
onboarding. A local HTTP 200 does not establish remote reachability.

For native Langfuse v1 readiness, also confirm that `aiv status` shows the saved
history start matching the vars file. After connecting a Langfuse SDK Agent and
obtaining its SpaceKey through onboarding, use Basic authentication
(`AgentUUID:SpaceKey`)
to call `GET /api/public/traces?limit=1` at the deployed web endpoint: expect
HTTP 200, including for an empty agent. Then send a non-sensitive SDK trace and
verify `GET /api/public/traces/<trace-id>` returns that trace, allowing bounded
polling for asynchronous ingestion. On upgrades or retries, also query a trace
retained before the current upgrade or retry, including data ingested during a
failed attempt. Keep credentials in private configuration and do not print
them. Without credentials, report the API check
as pending; container health and Web HTTP 200 alone do not verify v1 reads.

## Help the user sign in and get started

Open the verified Web URL from the user's browser and guide them through
[registration or sign-in](reference/operations.md#register-or-sign-in). Confirm
the intended Space opens. The user enters their password in the browser or the
CLI's hidden prompt.

Choose the first action based on what the user wants to try:

| Goal | First action and verification |
|---|---|
| Explore the platform without a model key | Open **Help → Getting started**. When **Try an example** is available, let the user choose and confirm a scenario, then inspect one demo Trace. |
| See their own Agent's telemetry | Open **Agent Access** at `/access`, choose the Agent or SDK and use its setup guide. For a coding Agent, follow [Agent machine onboarding](reference/docker.md#agent-machine-onboarding). In the same Space, find the first Trace from a recognizable new task and inspect a call. |

For a live standalone evaluation, continue with
[aivision-quickstart](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-quickstart)
using the verified URL and selected Space.

If the installed build lacks the example, use its Agent integration guide or
share the [first-Agent tutorial](https://aivision.mintlify.site/en/web-quickstart).
For builds that include the All-in-One sample helper, the
[synthetic sample Trace](reference/all-in-one.md#view-a-sample-trace) is another
way to explore the UI. Report deployment health, account access and the actual
first-use result, marking any step the user still needs to complete.

After real telemetry is present, introduce
[aivision-trace](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-trace)
for Trace and Session inspection and
[aivision-metric](https://github.com/ob-labs/ai-vision-skills/tree/main/skills/aivision-metric)
for usage, rate, latency and supported cost metrics. Querying uses an authorized
query SpaceKey for the selected Space.

## Native query defaults and recovery

Matching builds enable managed native Trace/Session query acceleration by default. Maintain the two recovery controls through the canonical deployment assets: `BACKEND_QUERY_MODE` (`auto`/`raw`) and `DATA_BACKEND_PROJECTION_MAINTENANCE_ENABLED` (`true`/`false`). Their legacy environment names remain aliases. Do not add independent strategy switches, hand-edit generated copies or start per-Space projector processes for normal installation.

The backend supervisor runs Gunicorn and the maintenance worker; explicit bootstrap commands bypass both. Shared maintenance OFF cannot be cleared by a normal restart. For an authorized recovery, follow the target-specific [Docker](reference/docker.md#native-query-maintenance-and-emergency-recovery) or [Kubernetes](reference/kubernetes.md#native-query-recovery-configuration) instructions, preserve private configuration/data identity, and inject the existing deployment key only into the explicit recovery command. Health alone does not prove projection completeness; record authenticated query results and the actual released/source build boundary.

## Operate Docker

These examples use the default Docker deployment. For every operation retain
the original `--target`, `--namespace`, `--workdir` and `--file` selectors and
the private vars file/overrides needed by `cast` or an incomplete first cast.
Compose uses its [target-specific commands](reference/docker.md#product-compose-source-version);
Kubernetes has no `destroy` or `redeploy` command. Do not create a `manage`
wrapper for normal product operations.

| Task | Command |
|---|---|
| Per-component state and endpoints | `aiv status` |
| Component logs | `aiv logs -n 80 backend`, `aiv logs backend -f` (`-f` = follow) |
| Upgrade to a selected Release or Daily | Resolve its versioned assets, merge its verified vars into the original private vars file, then `aiv cast --vars-file ./aivision.vars.yaml --var IMAGE_PULL=always` |
| Refresh a floating tag | `aiv cast --var IMAGE_PULL=always` |
| Rebuild a running stack | `aiv redeploy` |
| Stop everything, keep data | `aiv destroy` |
| Stop everything, wipe data + state | `aiv destroy --purge` |
| Second stack | use a new namespace on every command and override all fixed container names and ports; see [Docker variants](reference/docker.md) |

Hand the user the stable CLI path, selected version, deployment directory and
the actual selector-rich `aiv status` and `aiv logs` commands used to verify this
installation. Include its matching `cast`, `redeploy` and data-preserving
`destroy` commands where the selected target supports them; identify purge as
destructive. They must work from a fresh supported terminal without this Skill
or a task-local helper.

Upgrades preserve data: the selected datastore volumes and the data-backend metastore are kept,
and the backend and AgentLens run their migrations on boot. For backups and
rollback after schema changes see [backup and rollback](reference/operations.md#backup-and-rollback). To serve users
on other machines, override `BIND_ADDR` and `PUBLIC_HOST` as described in
[reference/docker.md](reference/docker.md).

## Rules

- **Never invent, print or commit credentials, tokens or SpaceKeys.** Passwords
  belong in a `chmod 600` `aivision.vars.yaml` outside version control, or in an
  environment variable; ask the user to supply them.
- **Never run `aiv destroy` or `aiv destroy --purge` without explicit user
  confirmation** — `--purge` deletes the current managed datastore volumes and namespace state (including the default data-backend metastore); it does not clear external OceanBase or seekdb.
- Do not bring the stack up manually with `docker run`, and do not edit generated
  manifests to work around a failed component; fix the authoritative source or
  configuration. For optional Compose use Go aiv --target compose to retain the lifecycle guards;
  native config/ps/logs may inspect the same original project. Bare up/down is
  not an established equivalent.
- Do not claim the deployment works without target-specific status, a reachable
  web port and the authenticated telemetry checks in the verification recipe.
- Keep the authentication gate detection-based rather than baking "private" or
  "public" into commands, so the skill survives the visibility change.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Release download returns 403/404 | Check the versioned tag and asset under `antgroup/ai-vision`, then network and any required GitHub authentication. Report missing official assets before attempting installation. |
| `docker pull ghcr.io/antgroup/ai-vision/…` denied / `unauthorized` | Check image access. If authentication is needed, use `docker login ghcr.io -u <user>` with an authorized PAT with `read:packages` (<https://github.com/settings/tokens/new>). Handle network and disk errors separately. |
| `Can't connect to MySQL server on 127.0.0.1:2881` when reusing OB | `127.0.0.1` is the container itself; point `OB_HOST` at the host IP or the Docker bridge gateway. |
| `bind: address already in use`, or a clash with another stack | Change the whole port set together with `--var` (see the isolated-stack variant). |
| `--context requires --target kubernetes`, or a docker-only flag is rejected | Kubernetes accepts only the flags listed in its variant. |
| A component is `running` but health is not `ok` | `aiv logs <component>`; usually a datastore that is not ready or a wrong `OB_*` value. Re-run `aiv cast` after fixing — it is idempotent. |
| Docker native Langfuse v1 reads return HTTP 503 mentioning `AIVISION_NATIVE_TRACE_HISTORY_START` | Set the fixed history start covering retained data in the original vars file and re-run `aiv cast --vars-file ...` with the same namespace. Verify v1 reads again; do not narrow the query window to hide the missing configuration. |

## Reference

Skill detail:

- [reference/all-in-one.md](reference/all-in-one.md) — quick trial and personal
  deployment, online or offline install, Agent onboarding and volume retention
- [reference/docker.md](reference/docker.md) — Docker target: the one command, the
  component/port table, selecting seekdb, reusing an existing database, a second isolated stack,
  serving users beyond the local host
- [reference/kubernetes.md](reference/kubernetes.md) — Kubernetes target: cluster
  requirements, bootstrapping a kind cluster, and the flags it rejects
- [reference/prerequisites.md](reference/prerequisites.md) — shared: what is
  really required, installing the CLI, verifying releases and checking image access

Manual user steps: [Docker deployment](https://aivision.mintlify.site/en/deployment/docker)
and [Kubernetes deployment](https://aivision.mintlify.site/en/deployment/kubernetes).

Bundled operator details: [component compatibility, history limits, backup and recovery](reference/operations.md).
The matching released CLI embeds product deployment assets. This repository does
not build images, publish a Chart or grant access to product Releases or packages.
