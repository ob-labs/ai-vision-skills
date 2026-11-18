# Prerequisites

Shared prerequisites for the [`aivision-deploy`](../SKILL.md) skill. Select the
deployment target first, then check only the tools required for that target.
The CLI is also usable manually; installing or deploying with `aiv` does not
require this Skill.

An existing restricted native installation retains its original profile until an
authorized upgrade. Follow the original release instructions for its lifecycle.

## Requirements by target

| Requirement | Needed when |
| --- | --- |
| `aiv` CLI | Default Docker, optional guarded Compose and fixed Kubernetes deployment; native Compose inspection can run without it. Check installed path, version and required commands before use. |
| Docker Compose 2.27+ | Optional Compose on Linux/macOS; Go aiv controls native Compose without host Python or an extra control script. Keep complete matching deployment assets. |
| Running Docker daemon | Docker deployment, or creating a local Kubernetes cluster with the Docker-backed kind recipe. An existing Kubernetes cluster does not require a local Docker daemon. |
| `kubectl` and a prepared cluster | Kubernetes deployment. Confirm the actual context, permissions, StorageClass, and target resources in the [Kubernetes guide](https://aivision.mintlify.site/en/deployment/kubernetes). |
| `curl` and `jq` | Discover and download a versioned public product Release. An already installed compatible CLI can be reused. |
| Image registry authentication | Only for images that require it. GitHub Release access and container image access are separate permissions. |
| CPU, memory, and storage | According to the selected target and datastore. Reusing OceanBase CE or seekdb removes the bundled datastore requirement, not the resources needed by the remaining services. |
| Network access | Whenever CLI assets, images, or dependencies must be downloaded or refreshed, including retries and upgrades. Do not assume only the first `cast` needs network access. |

Use the verified manifest and Release notes to check the selected combination's
image architectures and qualification. Check the deployment host and Agent
client separately.

A public image can remove the image-pull authentication step. It does not remove
database, Kubernetes, TLS, or other credentials required by the chosen environment.

Helm is planned but currently unavailable for the product. A Helm client is not a
prerequisite for this Skill's Kubernetes flow, and a source CLI build does not
provide a Chart. See the [Helm status and boundaries](kubernetes.md#helm-status).

For the Docker target only, check the daemon:

```bash
docker --version
docker info
```

For an existing Kubernetes cluster, check `kubectl` and the intended context
instead. Run the target-specific `aiv gauge` once the relevant tools and
configuration are available; a bare `aiv gauge` checks the Docker target.

### Product Compose and new source capabilities

Optional Compose requires matching aiv, Docker and Compose2.27+ on Linux/macOS.
It uses Go to call native Compose, without host Python or an extra control file.
Native delivery images provide their bootstrap executables with
`NATIVE_PYTHON_RUNTIME: "true"`; older Python-based images retain their matching
runtime mode. Default Docker stays the supported Go runtime and does not gain
a Compose prerequisite.

Use explicit --target compose on every CLI operation. With ordinary source CLI
builds only, existing files use
--compose-file absolute.yaml and --compose-env-file actual.env (default .env,
/dev/null for resolved exports), without namespace/workdir/vars/blueprint options.
Native config --quiet/ps/logs pin the original project name, absolute file and env.
Guarded mutations retain identity/ownership, locks, isolated seekdb init, init-job
reruns and exit/OOM-before-deletion checks; bare up/down is not an established
equivalent. See [the Compose reference](docker.md#product-compose-source-version).

Use matching images with backend/diagnosis SQL readiness, organization-file and
bootstrap support, gateway/data-backend native --ready and bounded shutdown.
Do not infer CLI target support or image compatibility from OB_BACKEND, dev tags
or source merges. The earlier controller matrix does not qualify the Go path;
record exact new combinations. If the selected Release lacks the required
capabilities, report the missing compatible Release. Image builds and publication
are product-maintainer work outside normal installation.

The gateway's default `healthcheck` checks local pprof within two seconds.
`healthcheck --ready` runs three checks, each with a two-second timeout, under
an eight-second CLI/Compose budget or ten-second Kubernetes readiness budget.
The local liveness command is not a substitute for readiness or authenticated
telemetry readback.
The data-backend `/api/v1/ready` must execute telemetry-store `SELECT 1` within
one second, returning HTTP 503 on database failure. Plain `/api/v1/health` and
native `healthcheck` without `--ready` remain liveness only. Reject an older
image returning HTTP 404 instead of falling back to its health endpoint.

Source CLI builds additionally require Python 3 for the asset freshness check.
After editing authoritative assets, run `make assets` in `aivision-cli/`, then
`make build`; normal builds check the committed generated files without changing them.

## Agent client runtime

Verify that the selected deployment serves an installer for the Agent machine's
OS and architecture. The standard source-compatible Agent path needs Python
3.11 or newer on that machine. Existing authorized native previews retain their
own host requirements. For a Linux x64 native preview, require glibc 2.35 or newer
and verify it on the Agent machine with `getconf GNU_LIBC_VERSION`.

The static `aiv` CLI, Docker services and hook installers have separate runtime
requirements. Consult `aiv connect --help` and the deployment's Agent catalog
before issuing an installation grant. Preserve existing Agent configurations.

## Find the CLI before installing

An installed CLI may be missing from the current shell's `PATH`. Check the
default installation directory before downloading again:

```bash
if ! command -v aiv >/dev/null 2>&1 && [ -x "$HOME/.local/bin/aiv" ]; then
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v aiv
```

If a custom install directory is known, add that directory to `PATH` instead.
For a runnable CLI, check the capabilities required by the selected target:

```bash
aiv --version
aiv cast --help
aiv status --help
aiv logs --help
```

Before treating this CLI as ready, complete [durable PATH setup](#finish-durable-path-setup)
and its fresh-shell checks. Check that the help includes the selectors used by the recipe, such as
`--namespace`, `--workdir` and `--vars-file`; Kubernetes also needs `cast`'s
`--target kubernetes` support. Help may print these flags with a single dash.
Before Agent onboarding, check `aiv connect --help` on the Agent machine as
described in [the Docker reference](docker.md#agent-machine-onboarding).
A printed version alone does not prove these capabilities. An unknown command
or missing required flag needs a compatible published Release via the
installation section below; preserve existing deployment state and profiles,
then repeat the path, version and help checks before continuing. A CLI that
cannot start needs its actual platform/runtime error resolved.

## Resolve the version and download matching assets

Use [published CLI discovery](install-cli.md#discover-a-published-cli) to resolve
Stable or an explicitly selected Daily from [product Releases](https://github.com/antgroup/ai-vision/releases).
Read the exact `tag` and `product_version`. Select `release-images.vars.yaml` for
bundled OceanBase CE or `release-seekdb.vars.yaml` for bundled seekdb. Kubernetes
uses the CE asset. With an external datastore, preserve its connection and
configuration when merging the selected product image pins.

On the deployment machine, check the daemon architecture independently:

```bash
docker version --format '{{.Server.Os}}/{{.Server.Arch}}'
```

Use a private working directory and set `AIV_TAG` to the verified versioned tag.
Use `AIV_IMAGE_VARS` to choose the matching CE or seekdb asset.

```bash
: "${AIV_TAG:?Set the exact resolved release tag}"
: "${AIV_IMAGE_VARS:?Choose release-images.vars.yaml or release-seekdb.vars.yaml}"
base="https://github.com/antgroup/ai-vision/releases/download/$AIV_TAG"
for asset in SHA256SUMS release-manifest.json "$AIV_IMAGE_VARS"; do
  curl -q --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    "$base/$asset" --output "$asset" || exit 1
done
awk -v vars="$AIV_IMAGE_VARS" '
  $2 == vars || $2 == "release-manifest.json" { print; seen[$2]++ }
  END { if (seen[vars] != 1 || seen["release-manifest.json"] != 1) exit 1 }
' SHA256SUMS > selected-assets.sha256 &&
  if command -v sha256sum >/dev/null 2>&1; then sha256sum -c selected-assets.sha256
  else shasum -a 256 -c selected-assets.sha256; fi
```

Confirm the release tag, product version, channel and the manifest's five GHCR
digests against discovery and the selected vars. Compare the service and database
indices with the actual deployment architecture and read the published notes for
runtime qualification. A CLI archive or an image index verifies availability for
a platform. Verify service health, authentication and Trace readback before
reporting deployment success.

### Verify an unpublished Actions candidate

Use this route only for an explicitly requested maintainer trial. The public
installer accepts published releases. For a candidate, use the GitHub CLI to
retrieve the exact successful Actions attempt and its frozen acceptance receipt
in an empty private directory. Set `AIV_RUN_ID` and `AIV_RUN_ATTEMPT` to the
selected run and attempt before starting.

```bash
set -eu
: "${AIV_RUN_ID:?Set the selected Actions run ID}"
: "${AIV_RUN_ATTEMPT:?Set the selected Actions attempt number}"
repo=antgroup/ai-vision
gh run view "$AIV_RUN_ID" --repo "$repo" --attempt "$AIV_RUN_ATTEMPT" \
  --json attempt,conclusion,headSha > run.json
jq -e --argjson attempt "$AIV_RUN_ATTEMPT" \
  '.attempt == $attempt and .conclusion == "success"' run.json >/dev/null
gh run download "$AIV_RUN_ID" --repo "$repo" \
  --name "release-assets-$AIV_RUN_ATTEMPT" --dir assets
gh run download "$AIV_RUN_ID" --repo "$repo" \
  --name "release-acceptance-$AIV_RUN_ATTEMPT" --dir acceptance
build_id="$AIV_RUN_ID.$AIV_RUN_ATTEMPT"
source_sha=$(jq -r .headSha run.json)
checksums_sha=$(shasum -a 256 assets/SHA256SUMS | awk '{print $1}')
manifest_sha=$(shasum -a 256 assets/release-manifest.json | awk '{print $1}')
jq -e --arg repo "$repo" --arg build "$build_id" --arg sha "$source_sha" \
  --arg checksums "$checksums_sha" --arg manifest "$manifest_sha" '
  .status == "qualified" and .source_repository == $repo
  and .build_id == $build and .source_sha == $sha
  and .assets.SHA256SUMS.sha256 == $checksums
  and .assets["release-manifest.json"].sha256 == $manifest
  and (.smokes | keys == ["oceanbase", "seekdb"] and all(.[];
    .status == "passed" and .source_sha == $sha and .build_id == $build
    and .manifest_sha256 == $manifest and .initial_pinned_content_verified
    and .recast_pinned_content_verified))
' acceptance/candidate-acceptance.json >/dev/null
(cd assets && shasum -a 256 -c SHA256SUMS)
```

Extract only the `aiv` executable from the verified archive for the CLI host.
Check that `aiv --version` matches `product_version` in `release-manifest.json`.
Choose the matching verified vars, merge host settings into one private file,
and run the [isolated Docker procedure](docker.md#verify-and-rerun). Record the
run ID, attempt, actual daemon architecture, database and image digests. The
frozen dual-database smoke covers the platform recorded in the receipt. Verify
other environments separately. If any receipt or selected asset is missing or
fails verification, stop this candidate trial.

## Install or upgrade the CLI when needed

Keep an installed CLI that matches the selected build and required capabilities.
Otherwise use [CLI discovery and installation](install-cli.md#discover-a-published-cli)
with the recorded version and client platform, then verify `aiv --version` and
the required `--help` commands. Use the published server CLI for deployment and
the matching Apple Silicon or Windows x64 CLI for Agent onboarding. The integrated
Mac profile uses `install-aiv-macos.sh`; the base and historical companion each
use their own `install-aiv.sh`. When using a supplied installer, verify it against
its profile checksum file and follow its exact repository and tag. Finish the
durable PATH checks below before running a lifecycle command.

### Finish durable PATH setup

The CLI must remain directly usable after this task ends. Keep it at
`$HOME/.local/bin/aiv` or the user's chosen permanent installation directory;
do not leave the sole binary in a download directory or task-local `tools/`.
Current source installers configure supported Bash/zsh startup files by default
and offer `--no-modify-path`; existing published installers may only print an
export command. Do not assume a published installer has the source feature or
pass a new option until its help confirms support. Manual archive/source installs
and older installers still need the fallback below.

For the default directory, use the actual selected shell. This adds the literal
PATH line only when missing and preserves other startup-file content:

```sh
AIV_PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
aiv_add_path_line() {
  [ -f "$1" ] || touch "$1"
  if ! grep -Fqx "$AIV_PATH_LINE" "$1"; then
    printf '\n%s\n' "$AIV_PATH_LINE" >> "$1"
  fi
}
case "${SHELL##*/}" in
  zsh)
    mkdir -p "${ZDOTDIR:-$HOME}"
    aiv_add_path_line "${ZDOTDIR:-$HOME}/.zshrc"
    ;;
  bash)
    aiv_add_path_line "$HOME/.bashrc"
    AIV_LOGIN_FILE="$HOME/.bash_profile"
    for AIV_CANDIDATE in "$HOME/.bash_profile" "$HOME/.bash_login" "$HOME/.profile"; do
      if [ -f "$AIV_CANDIDATE" ]; then
        AIV_LOGIN_FILE="$AIV_CANDIDATE"
        break
      fi
    done
    aiv_add_path_line "$AIV_LOGIN_FILE"
    ;;
  *) printf '%s\n' 'Configure PATH in the actual shell startup file before continuing.' >&2 ;;
esac
unset -f aiv_add_path_line
export PATH="$HOME/.local/bin:$PATH"
command -v aiv
aiv --version
```

For a custom directory, write its safely shell-quoted literal PATH entry instead;
do not copy unescaped path text into executable shell syntax. For another shell,
use its native PATH syntax and actual startup files. If the user explicitly
declines startup-file changes, preserve that choice and report manual setup as
pending rather than claiming fresh-terminal readiness.

Verify a new supported shell without the task's exported PATH. Use the confirmed
Bash/zsh executable in `$SHELL` (not an unrelated login-shell setting), and test
both interactive non-login and login startup:

```sh
env PATH=/usr/bin:/bin:/usr/sbin:/sbin "$SHELL" -ic 'command -v aiv && aiv --version'
env PATH=/usr/bin:/bin:/usr/sbin:/sbin "$SHELL" -lic 'command -v aiv && aiv --version'
```

Both must resolve the intended stable binary and selected version. Also repeat
`command -v aiv` and `aiv --version` in a newly opened terminal when available.
A successful current-shell export alone is insufficient. Fix conflicting PATH
resets or an older binary earlier in PATH before deployment completion.

For an existing Docker/Compose upgrade, first preserve the old configuration and
restore set using the [upgrade workflow](upgrade.md#prepare-and-run-the-upgrade).
For CLI-managed Docker or Compose, merge the verified vars entries into the
original private `aivision.vars.yaml`, updating existing keys rather than
appending duplicates. Reconcile legacy/canonical image aliases and higher-priority
`AIV_VAR_*` / `--var` image overrides as described in the upgrade workflow. Check
the effective five image pins and manifest against the selected release before `cast`.
Keep its password, history start, datastore choice, ports, addresses and custom
selectors. For an external database, retain `OB_MANAGED: "false"`, connection
settings and its existing database image policy. The downloaded database image
is for the bundled datastore. The CLI accepts **one** `--vars-file`; passing it
twice does not combine configurations. Keep the merged file outside source
control with mode `600`.

A failed download or verification is a blocker for using that asset. The
temporary directory is not the deployment directory; retain the verified
manifest and vars before removing it. Use the installation guide to keep
`~/.local/bin` in the shell's startup files and complete the fresh-shell checks
above before reporting a finished installation.

### Check published seekdb support

For seekdb, confirm the selected Release includes `OB_BACKEND` support. If it
does not, report the missing compatible Release; do not build from source as a
trial fallback. CLI platform support does not prove native datastore image
support: verify that the exact upstream seekdb index in the selected manifest
has a native child for the Docker daemon. Do not substitute an emulated image,
a mutable tag or a source build when the selected release lacks that child.

### Source build identity and verification

This optional maintainer path requires separately authorized product-source
access; it is not a prerequisite or fallback for recipient trial workflows.
Use it only for an explicitly requested source deployment or local validation. Build the CLI, deployment assets and owned images from the selected
checkout; do not replace that request with a published CLI or rolling image.
Keep local image references explicit and use `IMAGE_PULL=missing` when they are
not published. Record the actual source revision, dirty state and source-diff
hash alongside image IDs; an uncommitted merge is not a clean published version.

Root `VERSION` supplies `aiv --version` for `make build`. For each owned image
(`aivision-fe`, `aivision-be`, `antcollector-gw`, `agentlens`), generate build
metadata from that same checkout with
`python3 scripts/build/build_info.py --component COMPONENT --channel dev --format base64`
and pass it as `AIVISION_BUILD_INFO_BASE64` to its standard Dockerfile. Retain the
decoded metadata as non-secret build evidence. The generator records the actual
HEAD and dirty state; do not label a dirty local build as stable, RC or Daily.
Direct Docker builds without metadata report unknown identity.

After deployment, compare `/api/v1/version` and **Help → About** (`/about`) with
that evidence. Native backend images provide build info at
`/etc/aivision/build-info.json`; Python-based source images may use
`/app/aivision_backend/build-info.json`. Check gateway and diagnosis build info at
`/etc/aivision/build-info.json`, and the frontend's compiled identity shown in
About. Verify the four owned component names, source/build IDs, version, channel
and dirty state, plus the actual runtime image IDs. Record the external SigNoz
source/image provenance separately. These checks supplement health, telemetry,
retained-data and lifecycle verification; they do not replace them.

Without a verified installed release manifest, the product release remains
unknown even when component build details are present. Do not fabricate
`AIVISION_RELEASE_MANIFEST_BASE64` to make a local run appear published. Consult
the [bundled release identity guidance](operations.md#release-and-build-identity)
for reused-build identity and update-check behavior.

## Image access for Docker

For published builds, set `AIV_BE_IMAGE` to the backend digest in the verified
manifest, then check that exact image before asking for registry credentials:

```bash
docker pull "$AIV_BE_IMAGE"
```

For local source images, use `docker image inspect` on the recorded local image
instead of pulling an unpublished reference.

Only an authentication or authorization response such as `denied` or
`unauthorized` calls for checking image access and logging in. A timeout, DNS or
TLS error, missing manifest/tag, or lack of disk space needs its own fix; do not
append `|| docker login` to the pull command. A successful pull verifies access
to that image and tag, not every image used by the deployment.

If access is required, the operator replaces `YOUR_GITHUB_USERNAME` with their
GitHub username and runs:

```bash
docker login ghcr.io -u YOUR_GITHUB_USERNAME
```

Enter a GitHub personal access token (classic) with `read:packages` and access
to the requested package at the password prompt. A GitHub account password is
not a registry token. GitHub CLI login is not a substitute for this registry
login. Create the token in the operator's GitHub settings and grant only the
required package access, including organization authorization where required.
Do not assume repository read access also grants package access.

## Image access for Kubernetes

Image pulls happen inside the selected cluster. A Docker login on the local
machine alone does not configure cluster image access.

- If all requested images are anonymously accessible, add
  `--var IMAGE_AUTH=anonymous` to the Kubernetes command. This skips the pull
  credential flow; other deployment credentials still depend on the environment.
- For restricted images, use an existing `kubernetes.io/dockerconfigjson` Secret
  in the deployment namespace with `--var IMAGE_PULL_SECRET=YOUR_SECRET_NAME`,
  or follow the interactive GHCR username and PAT prompts. `YOUR_SECRET_NAME` is
  a placeholder for an actual Secret, not a token.
- Non-interactive credential provisioning uses the documented
  `AIV_GHCR_USERNAME` / `AIV_GHCR_TOKEN` environment variables or an existing pull
  Secret. Follow the operator's approved secret-management path; do not place a
  real token in a sample command, script, or chat.

See the [Kubernetes deployment guide](https://aivision.mintlify.site/en/deployment/kubernetes)
for complete commands and the supported configuration. An explicit
`IMAGE_AUTH=anonymous` clears the saved pull-secret reference; choose the mode
for the actual images rather than combining it with a restricted-image Secret.

## Secrets

Do not print, commit, or request credentials in chat. Let the operator enter
values at the appropriate CLI secret prompt or provision them through their
approved secret manager. Release download authentication, image-pull
credentials, database access, and AI Vision application sign-in serve different
purposes; verify each only when the selected task requires it.
