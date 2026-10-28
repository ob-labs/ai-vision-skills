# Prerequisites

Shared prerequisites for the [`aivision-deploy`](../SKILL.md) skill. Select the
deployment target first, then check only the tools required for that target.
The CLI is also usable manually; installing or deploying with `aiv` does not
require this Skill.

## Requirements by target

| Requirement | Needed when |
| --- | --- |
| `aiv` CLI | Default Docker, optional guarded Compose and fixed Kubernetes deployment; native Compose inspection can run without it. Check installed path, version and required commands before use. |
| Docker Compose 2.27+ | Optional Compose on Linux/macOS; Go aiv controls native Compose without host Python or an extra control script. Keep complete matching deployment assets. |
| Running Docker daemon | Docker deployment, or creating a local Kubernetes cluster with the Docker-backed kind recipe. An existing Kubernetes cluster does not require a local Docker daemon. |
| `kubectl` and a prepared cluster | Kubernetes deployment. Confirm the actual context, permissions, StorageClass, and target resources in the [Kubernetes guide](https://aivision.mintlify.site/en/deployment/kubernetes). |
| GitHub CLI (`gh`) and GitHub authentication | The bundled restricted-trial Release download procedure; the operator needs read access to the selected delivery repository. An already installed compatible CLI does not require downloading again. |
| Image registry authentication | Only for images that require it. GitHub Release access and container image access are separate permissions. |
| CPU, memory, and storage | According to the selected target and datastore. Reusing OceanBase CE or seekdb removes the bundled datastore requirement, not the resources needed by the remaining services. |
| Network access | Whenever CLI assets, images, or dependencies must be downloaded or refreshed, including retries and upgrades. Do not assume only the first `cast` needs network access. |

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
Container bootstrap Python remains in application images. Default Docker stays
the supported Go runtime and does not gain a Compose prerequisite.

Use explicit --target compose on every CLI operation. Existing files use
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
are product-maintainer work outside the normal restricted-trial workflow.

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

Follow the [channel choice](../SKILL.md#choose-release-or-daily), then inspect the
published GitHub Release. During the restricted trial, inspect metadata with
`gh release view --repo ob-labs/ai-vision-ob` or authenticated `gh api` using an
account authorized for the product delivery repository. Skill repository read
access does not grant Release access. Do not share tokens. The current CLI and
matching image manifests remain delivered by `ob-labs/ai-vision-ob`; this Skills
repository does not currently publish binaries. An owner may provide a fixed
delivery repository/tag later; verify its matching archive, checksums, manifest
and vars, without rewriting product build provenance or OCI image repositories.

| Choice | Resolve once, before downloading |
| --- | --- |
| Release (default) | Read the [latest stable Release](https://github.com/ob-labs/ai-vision-ob/releases/latest), or `GET https://api.github.com/repos/ob-labs/ai-vision-ob/releases/latest`. Use its published versioned `tag_name`; drafts and prereleases are excluded. |
| Daily | Read the [`daily` Release](https://github.com/ob-labs/ai-vision-ob/releases/tag/daily), or `GET https://api.github.com/repos/ob-labs/ai-vision-ob/releases/tags/daily`. Follow **Versioned assets and exact image manifest** in its notes and retain that versioned tag, such as `v0.0.1-daily.20261021` or `v0.0.1-daily.20261021.2`. |
| Explicit version | Read that versioned Release and confirm it is published and has the required assets. |

Published GitHub Releases define the installable versions. Do not enumerate Git
or registry tags to choose a build: `candidate-*`, `trial-*`, `sha-*`, and
architecture tags are build records, not Release or Daily choices. A `dev` image
tag does not establish that either channel has been published.

`daily` is a pointer Release with no CLI assets. Do not use
`/releases/download/daily/aiv-*.tar.gz` or `sh install-aiv.sh --version daily`.
Pin the resolved version for all downloads so a newer Daily cannot mix the CLI
and image combination halfway through installation. If a requested channel or
asset is absent, report it and resolve the missing publication; do not fall back
to another channel. When the user requests a particular day's build, compare
the snapshot date in the selected version and the published
`release-manifest.json` product version. A build finishing
after midnight or a retry does not change that date; `built_at` records the
actual build time. The first accepted Daily on that date has no revision
suffix; additional accepted versions use `.2`, `.3`, and later. Never derive a
Daily version from workflow run counters or attempts, and never overwrite an
accepted version with changed release content. Manual `dev` snapshots use a
separate version format and are not the Daily install choice.

Download the platform CLI, `SHA256SUMS`, `release-manifest.json`, and the selected
Docker datastore's vars asset from that same versioned Release. For Kubernetes,
download the CE vars asset but use its five service image entries and release metadata as
explained in the [Kubernetes recipe](kubernetes.md); its Docker database settings
do not apply. Complete the [bundled durable PATH setup](#finish-durable-path-setup)
below. The public [CLI installation guide](https://aivision.mintlify.site/en/guides/install-cli)
is supplemental reading.

Use the same terminal throughout. Save the current directory, then create an
empty temporary download directory:

```bash
AIV_RETURN_DIR="$PWD"
AIV_WORKDIR=$(mktemp -d)
cd "$AIV_WORKDIR"
```

Set `AIV_RELEASE_TAG` to the actual versioned tag just resolved, replacing the
placeholder before executing downloads. Choose one platform and one datastore:

```bash
AIV_RELEASE_TAG=YOUR_RESOLVED_VERSIONED_TAG
AIV_DELIVERY_REPOSITORY=ob-labs/ai-vision-ob
AIV_IMAGE_VARS=release-images.vars.yaml  # CE; use release-seekdb.vars.yaml for Docker seekdb
```

| Platform | Assignment |
| --- | --- |
| Linux x64 | `AIV_PACKAGE=aiv-linux-x64.tar.gz` |
| Linux ARM64 | `AIV_PACKAGE=aiv-linux-arm64.tar.gz` |
| macOS Intel | `AIV_PACKAGE=aiv-darwin-x64.tar.gz` |
| macOS Apple Silicon | `AIV_PACKAGE=aiv-darwin-arm64.tar.gz` |

For restricted Release downloads, use an authenticated `gh` with read access:

```bash
gh auth status --hostname github.com &&
gh release download "$AIV_RELEASE_TAG" -R "$AIV_DELIVERY_REPOSITORY" \
  -p "$AIV_PACKAGE" -p SHA256SUMS -p release-manifest.json -p "$AIV_IMAGE_VARS"
```

A 403/404 can mean a wrong tag, missing asset or unavailable access. Check the
actual Release with the authorized account. If no compatible Release exists,
report the missing artifact and stop. Do not silently compile a CLI, use a moving
tag or replace the requested channel. Preserve the existing installed binary.

Verify exactly one checksum record for each downloaded asset. The sums also
cover other platforms; verify only the files selected here:

```bash
awk -v archive="$AIV_PACKAGE" -v vars="$AIV_IMAGE_VARS" '
  $2 == archive || $2 == vars || $2 == "release-manifest.json" { print; seen[$2]++ }
  END { if (seen[archive] != 1 || seen[vars] != 1 || seen["release-manifest.json"] != 1) exit 1 }
' SHA256SUMS > SHA256SUMS.selected &&
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c SHA256SUMS.selected
else
  shasum -a 256 -c SHA256SUMS.selected
fi
```

Continue only after this succeeds. Read `release-manifest.json`: its
`product_version` must match the versioned tag without its leading `v`, its
channel must be `stable` for Release or `daily` for Daily, and the vars image
digests must match its `images` entries. The vars must also contain
`AIVISION_RELEASE_MANIFEST_BASE64` encoding that exact manifest. Keep this entry
when merging configuration; it supplies the installed product version to About.
All five bundled service repositories use the same product-version tag, but
component build identities may legitimately predate that release. Retain this
manifest and the verified vars asset in the
durable deployment directory. Do not print or replace an existing private
configuration to do so.

## Install or upgrade the CLI when needed

If the installed CLI already matches the manifest and required capabilities,
keep it. Otherwise install the verified archive from the previous step:

```bash
tar -xzf "$AIV_PACKAGE" aiv &&
mkdir -p "$HOME/.local/bin" &&
install -m 755 aiv "$HOME/.local/bin/aiv" &&
export PATH="$HOME/.local/bin:$PATH" &&
command -v aiv &&
aiv --version
```

Confirm the printed version equals the manifest's `product_version`, then repeat
the required help checks above. An installer is also available in the versioned
Release: its `--version` must be that versioned tag; omitting it selects the latest
stable CLI even when the installer came from a Daily Release.

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
`AIV_VAR_*` / `--var` image overrides as described in the upgrade workflow; verify
the effective five image pins and manifest before `cast`.
Keep its password, history start, datastore choice, ports, addresses and custom
selectors. For an external database, retain `OB_MANAGED: "false"`, connection
settings and its existing database image policy. The downloaded database image
is for the bundled datastore. The CLI accepts **one** `--vars-file`; passing it
twice does not combine configurations. Keep the merged file outside source
control with mode `600`.

Return to the saved directory before preparing or running a deployment:

```bash
cd "$AIV_RETURN_DIR"
```

A failed download or verification is a blocker for using that asset. The
temporary directory is not the deployment directory; retain the verified
manifest and vars before removing it. Use the installation guide to keep
`~/.local/bin` in the shell's startup files and complete the fresh-shell checks
above before reporting a finished installation.

### Check published seekdb support

For seekdb, confirm the selected Release includes `OB_BACKEND` support. If it
does not, report the missing compatible Release; do not build from source as a
trial fallback. CLI platform support does not prove native datastore image
support: the pinned seekdb image is Linux/amd64, so ARM needs Docker emulation
or a separately validated `OB_IMAGE`.

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
that evidence. Check backend build info at
`/app/aivision_backend/build-info.json`, gateway and diagnosis build info at
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
