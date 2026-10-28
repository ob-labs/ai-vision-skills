# Upgrade and recover an existing installation

Use the existing CLI lifecycle; do not introduce another upgrade controller.
This reference covers default Docker and optional Compose. Kubernetes keeps its
[target-specific workflow](kubernetes.md).

The restricted `0.0.1-daily.20261028.2` native CLI supports default Docker and
CLI-managed Compose. It rejects existing-file / standalone `--compose-file`
deployments. If the existing installation uses that mode, stop before replacing
the CLI, changing configuration or mutating services. Keep its compatible CLI
and resolve a supported upgrade path; this delivery provides no automatic
conversion. The standalone instructions below apply only to ordinary source
CLI builds with that capability.

## Continue within the requested scope

An explicit upgrade request selects the existing installation, not a fresh
installation. Honor the requested version/channel and established maintenance
window. Report that services may briefly stop; do not ask the user to repeat
known target, datastore or credential choices. Continue routine preparation,
CLI execution, verification and the eligible recovery below within the user's
upgrade authorization and the environment's execution permissions. Ask only for
missing information that prevents safe progress or a new action outside scope.
An inspection-only request does not authorize upgrade or container removal.

## Prepare and run the upgrade

1. Locate the original deployment directory and CLI command. Record enabled
   components and lifecycle status with `aiv status`, retaining every original
   selector. Establish the installed version/manifest separately from About/build
   responses and the actual container image identities; saved overrides alone
   are not runtime proof. Default Docker uses `--namespace`, `--workdir` and any
   `--file`; CLI-managed Compose also uses `--target compose`. For ordinary
   source CLI builds only, existing-file
   Compose uses its exact `--compose-file` and `--compose-env-file`, without
   mixing namespace/workdir/vars flags. Never convert an existing Docker target
   to Compose as part of an ordinary version upgrade.
   Keep `aiv` in its permanent installation directory and complete
   [durable PATH and fresh-shell verification](prerequisites.md#finish-durable-path-setup)
   for the selected CLI. Reuse existing startup setup when it works; a wrapper
   or binary under a task's `tools/` is not the user's normal lifecycle entry.
2. Privately preserve the original vars/env, state, image identities, persistent
   mounts, organization and fixed `AIVISION_NATIVE_TRACE_HISTORY_START`. Record
   a retained SQL/Trace/Session sample before changing the deployment. Prepare
   a consistent backup/restore set for the business and telemetry databases,
   SigNoz metastore, configuration and old images. Use the datastore's supported
   backup procedure and the required application/worker quiescence. An inspect
   report, vars-file copy or copy of live SQLite files is not a database backup.
   If the backup procedure or destination is unknown, resolve that specific gap
   before mutation. Keep backup credentials and private state out of chat/logs.
3. [Resolve and verify](prerequisites.md#resolve-the-version-and-download-matching-assets)
   one versioned Release and its matching CLI, manifest and backend-specific
   vars. Restricted Daily uses the exact published
   `delivery-v<product-version>` prerelease in `ob-labs/ai-vision-skills`; do not
   follow the old product `daily` pointer. The current target is
   `delivery-v0.0.1-daily.20261028.2`, Linux x64 / `linux/amd64` only; confirm the
   Release and platform exist before changing an installed CLI. A retry keeps
   that resolved version. CLI installation alone does
   not upgrade running services. Preserve the old restore set before installing
   the target CLI or changing deployment configuration.
4. Merge the five released application digests and exact embedded release
   manifest into the original configuration. Treat legacy/canonical image aliases
   as one setting: an old `DATA_BACKEND_IMAGE` can override a new `SIGNOZ_IMAGE`.
   Update or remove stale image aliases in saved/merged variables and reconcile
   image overrides from `AIV_VAR_*` and original `--var` flags; do not carry old
   pins forward merely because they were in the original command. Preserve
   unrelated overrides and selectors. Privately resolve the effective five image
   settings and embedded manifest before `cast`; all must match the selected
   release. For restricted Daily, use the manifest's exact digest references
   under `ghcr.io/ob-labs/ai-vision-skills/` and retain
   `NATIVE_PYTHON_RUNTIME: "true"` from its native vars. Never guess tags or
   print resolved secrets to do this.
   Retain passwords, tokens, datastore/backend, managed/external choice, ports,
   addresses, namespace/state and fixed history start. Do not replace the file
   with the downloaded vars or pass two `--vars-file` flags. External databases
   retain their existing connection/image policy. With ordinary source CLI
   builds only, existing parameterized Compose
   files keep their original env and matching maintained assets; do not rewrite
   generated CLI bundles or infer a different lifecycle from registry tags.
5. Run the matching CLI's ordinary `cast` with the original selectors and one
   merged private configuration. For example, an existing default Docker stack:

   ```sh
   aiv cast --namespace demo --workdir /srv/demo/work \
     --vars-file /srv/demo/aivision.vars.yaml --var IMAGE_PULL=always
   aiv status --namespace demo --workdir /srv/demo/work
   ```

   Substitute the discovered selectors, including any original `--file`.
   CLI-managed Compose keeps `--target compose` on both commands. With ordinary
   source CLI builds only, existing-file Compose follows the
   [exact file/env command](docker.md#product-compose-source-version).
   Cached local images use the previously selected pull policy. Do not start
   overlapping lifecycle commands or blindly retry a failed stop.

## Known stopped legacy SigNoz recovery

This is a shutdown ownership bug, not a data-format migration. The affected old
SigNoz can close a borrowed SQL pool during shutdown, log `sql: database is
closed` and exit 1. The new CLI deliberately stops replacement and retains that
container. Retrying the same command alone cannot make its old exit code clean.
Do not alter business rows, truncate telemetry, delete SQLite/WAL files or reset
credentials to address this failure.

The verified case is default Docker from `0.0.1-daily.20261022` to
`0.0.1-daily.20261025` on native Linux with OceanBase CE or OceanBase seekdb.
It was operator-assisted container recovery, not a clean automatic upgrade.
The affected SigNoz revision is
`d560a6ad5459220af64c851899aae8f696d5b9fe`; the verified target contains the
borrowed-pool shutdown fix at `d6d5d94cdbfc70885f7218254464d9043ea6f326`.
For another target, establish that it includes this fix from release/source
identity; a newer tag alone is insufficient.

When the user already requested this data-preserving upgrade, continue this
known recovery without another routine confirmation **only after all checks**:

- This is the original default Docker installation. Its private
  `<namespace-state>/lifecycle-stops/data-backend.json` binds `component` equal
  to `data-backend` and `container_id` equal to the inspected full immutable ID.
  Match namespace ownership and component labels to the original deployment;
  legacy `signoz` / `signoz-ob` map to `data-backend`. Do not rely on a name alone.
- The exact old image/revision and same shutdown attempt are identified. The
  retained logs contain `failed to stop signoz` with `sql: database is closed`;
  container state is `exited`, exit code 1, not running/restarting/dead and not
  OOM-killed. Other failures or a failed database stop are outside this recipe.
- `/var/lib/signoz` is in the original persistent bind/volume, with the original
  metastore present and a verified consistent backup. Preserve all related
  SQLite/WAL files together. Reject writable-layer-only storage or ambiguous
  mounts. The database and its volumes remain intact; the private configuration,
  organization, credentials and history bound are available for retry.
- No other lifecycle operation is running. Default Docker has no shared mutation
  lock for this helper action: use the maintenance window and recheck exact ID,
  ownership, state, mounts and pending record immediately before removal.
  Save only necessary state/log evidence privately, avoiding `Config.Env` dumps.

After those checks, the sole recovery mutation is plain removal of the exact
**already stopped** container. Set `AIV_FAILED_ID` from the verified full ID:

```sh
docker rm "$AIV_FAILED_ID"
```

Do not use `-f`, `-v`, `compose down`, purge, prune, a database-container removal,
SQL edits or stop-record deletion. A Docker inspection error does not prove
absence: require a successful daemon/listing check confirming that exact ID is
absent. Verify configuration and storage are unchanged, then rerun the same
ordinary target CLI `cast`. The CLI acknowledges the absent failed ID and clears
its own gate. Do not restart the old SigNoz or loop recovery attempts; stop if
this one retry fails and preserve the evidence.

Compose uses a different `.compose-stop-pending.json` map and ownership/lock
contract. Keep its original target/file/env and inspect through its CLI; do not
apply the default-Docker stop-file procedure or automatically generalize this
published recovery proof to Compose. Unknown image/state/signature, OOM, failed
SQL readiness, missing backup or unclear ownership requires diagnosis before
further mutation. A broad confirmation cannot replace the missing evidence.

## Verify before declaring the upgrade complete

Use the Skill's [verification](../SKILL.md#verify-docker--never-report-success-without-this)
with the original selectors. Require every enabled service healthy and inspect
restarts/OOM, actual image identities and organization/mount bindings. Compare
About's installed release and observed frontend/backend builds with their
expected manifest entries; reused component builds may have older source SHAs.
Verify retained SQL data and old Trace/Session samples plus newly ingested and
authenticated read-back telemetry. Preserve the original credentials and history
bound. Readiness or a version label alone does not establish retained-data safety.
Record any real-model, platform or artifact checks that were not performed.

Report the selected version, actual recovery action, retained-data verification
and remaining limitations. The agent can handle the known operator steps; this
does not change the CLI's stop gates or guarantee zero downtime. If schema
migration has run, selecting old images is not rollback: restore the matching
database/metastore/configuration/image set. Do not perform automatic rollback.

Hand back the permanent CLI path and the actual deployment directory, plus the
selector-rich `aiv status`, `aiv logs`, upgrade `cast`, supported `redeploy`, and
data-preserving `destroy` commands for this target. Keep any original namespace,
workdir, blueprint or Compose file/env selectors in those commands so a new
terminal operates the same installation.
