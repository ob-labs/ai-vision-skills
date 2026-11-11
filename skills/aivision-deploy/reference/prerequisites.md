# Prerequisites

Shared prerequisites for the [`aivision-deploy`](../SKILL.md) skill. Select the
deployment target first, then check only the tools required for that target.
The CLI is also usable manually; installing or deploying with `aiv` does not
require this Skill.

For the restricted native CLI profile, use default Docker or
CLI-managed `--target compose` with matching native release variables. It rejects
standalone `--compose-file`. The existing-file instructions below require an
ordinary source CLI build; if upgrading such an installation, stop before
replacing its CLI or changing its configuration or services. No automatic
conversion is provided.

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

Use the verified manifest for the selected release's server architecture and
CLI availability. Native deployment sets `NATIVE_PYTHON_RUNTIME` and needs no
user-installed Python. The Quickstart SDK demo and maintainer source builds
have their own requirements.

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

The restricted trial CLI has a native-only compile-time profile.
A source-mode CLI with the same version text is not equivalent: install the
checksummed archive from the selected private Release. The earlier `.20261028`
CLI embeds Python deployment helpers and needs replacement for strict delivery.
Native builds reject explicit source runtime/installer choices and standalone
`--compose-file`; use CLI-managed `--target compose` with the native release vars.

## Native Agent client runtime

Verify that the backend serves the native installer for the Agent machine's
operating system and architecture. For Apple Silicon or Windows x64, use the
matching CLI and [compatible preview backend](#select-the-agent-client-backend-configuration).
Check OS and security-policy limitations against that preview's qualification.
On Linux x64, require glibc 2.35 or newer. Debian Bookworm is the recorded Linux
client baseline. Check the **Agent's own Linux machine** before `aiv connect`:

```bash
getconf GNU_LIBC_VERSION
```

If glibc is older than 2.35, use a compatible Agent machine. A missing glibc
symbol is an incompatible client runtime; installing host Python does not fix
the native bundle. The static Go CLI and Docker services have separate runtime
requirements: application runtime libraries are inside their images. Successful
deployment on an older Docker host does not qualify Agent installation there.

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

Use the [channel choice](../SKILL.md#choose-release-or-daily) and the operator's
own authenticated `gh` session. Record the Linux deployment platform separately
from the computer running `aiv` and the machines running the Agents. Read the
Docker daemon architecture with `docker version --format '{{.Server.Os}}/{{.Server.Arch}}'`.
For Kubernetes, check the nodes that can run the workloads in the selected context.

| Choice | Resolve before changing an installation |
| --- | --- |
| Release (default) | Start at the product repository's [latest stable Release](https://github.com/ob-labs/ai-vision-ob/releases/latest). Confirm the published version, selected platform and matching assets. |
| Daily | Use [published CLI discovery](install-cli.md#discover-a-published-cli) and the exact published base `delivery-v<product-version>` prerelease in `ob-labs/ai-vision-skills`. For deployment, use `base_tag` from the discovery result. Check the base manifest against the actual Linux deployment platform. |
| Explicit version or retry | Inspect that exact Release or reuse the recorded selection. An unsupported requested platform or missing asset stops the operation. |

For restricted Daily, use a Linux x86 deployment host (`linux/amd64`) and a
base manifest that lists `linux/amd64` in `image_platforms` and `linux-x64` in
`cli_platforms`. Linux ARM64, Intel Mac, and Windows ARM64 are paused for this
channel, including selection of older releases for those platforms. For an
unpinned Daily, consider published, non-draft base Releases from newest to oldest
by product version, snapshot date, and numeric revision. Require the matching CLI
and the selected datastore vars asset. Use the published manifest for stable
Release platform support. Repeat discovery for the next operation.

When Apple Silicon or Windows x64 Agent onboarding is in scope, also require the matching
published client artifacts and preview backend configuration below. For a new
unpinned deployment, choose the newest base that satisfies those client needs as
well as the server platform. For an existing deployment, verify the companion
against its selected base and preserve the deployment identity. A different base
requires the [ordinary upgrade workflow](upgrade.md#prepare-and-run-the-upgrade).
Pin the exact base and companion tags after selection. Registry `daily` and `dev`
tags do not select a product Release. On an authentication, download or checksum
error, resolve that error before using the candidate. A confirmed incompatible
candidate can be skipped for unpinned discovery within the requested channel.

Set `AIV_RELEASE_TAG` to the selected base tag and `AIV_DELIVERY_REPOSITORY` to its
repository. The CLI discovery result provides `base_tag`, `repository`, and
`product_version`. Use `AIV_IMAGE_VARS=release-images.vars.yaml` for OceanBase CE or
`AIV_IMAGE_VARS=release-seekdb.vars.yaml` for Docker/Compose with seekdb. For
Kubernetes, use the CE asset as explained in the [Kubernetes recipe](kubernetes.md).
Download into an empty temporary directory and verify the two selected files.

```bash
: "${AIV_RELEASE_TAG:?Set the selected versioned base tag}"
: "${AIV_DELIVERY_REPOSITORY:?Set the selected repository}"
: "${AIV_IMAGE_VARS:?Set the selected datastore vars filename}"
AIV_WORKDIR=$(mktemp -d)
gh release view "$AIV_RELEASE_TAG" --repo "$AIV_DELIVERY_REPOSITORY" \
  --json tagName,isDraft,isPrerelease,publishedAt,assets &&
gh release download "$AIV_RELEASE_TAG" --repo "$AIV_DELIVERY_REPOSITORY" \
  --pattern SHA256SUMS --pattern release-manifest.json --pattern "$AIV_IMAGE_VARS" \
  --dir "$AIV_WORKDIR" &&
(
  cd "$AIV_WORKDIR" &&
  awk -v vars="$AIV_IMAGE_VARS" '
    $2 == vars || $2 == "release-manifest.json" { print; seen[$2]++ }
    END { if (seen[vars] != 1 || seen["release-manifest.json"] != 1) exit 1 }
  ' SHA256SUMS > SHA256SUMS.selected &&
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c SHA256SUMS.selected
  else
    shasum -a 256 -c SHA256SUMS.selected
  fi
)
```

Inspect the `release view` result for the exact tag, a publication date and the
expected channel. Daily is a prerelease. Verify that the manifest's
`product_version` matches the tag's product version and that its `channel` is
`daily` or `stable` as selected. For restricted Daily, confirm
`delivery.repository`, `delivery.release_tag`, `delivery.catalog_sha` and
`source_repository` identify the exact Skills release, catalog commit and product
repository. Verify all five vars image pins against `images`, the chosen bundled
database against `databases`, and `AIVISION_RELEASE_MANIFEST_BASE64` against that
manifest. Base Daily image references use `ghcr.io/ob-labs/ai-vision-skills/` and
immutable digests. Its bundled databases use the official upstream digests and
must include the selected native deployment architecture. Keep
`NATIVE_PYTHON_RUNTIME` enabled when the selected native configuration sets it.
Keep the verified manifest and vars in the durable deployment directory.

### Select the Agent-client backend configuration

Apply preview configuration only for the requested client platforms on a
compatible base. Use the selected release's verified asset list and checksums.
A macOS CLI runs on the Agent machine. The preview backend still runs on Linux.

| Requested clients | Backend configuration for the published macOS preview |
| --- | --- |
| Apple Silicon Macs | `release-images.vars.yaml` for OceanBase CE or `release-seekdb.vars.yaml` for seekdb, from the macOS companion Release |
| Linux x64 clients only | The selected base Release's CE or seekdb vars |

For Apple Silicon, discover a published `macos-codex-preview-v*` companion for the exact
base. Download `macos-codex-preview.json`, `SHA256SUMS`, and the chosen vars from
that companion tag. Verify checksums and the vars identity in `assets`. Confirm
its `release_tag`, `profile`, and `client["darwin/arm64"]` entry. Check that
`base_release` equals the selected base tag, `backend.base_reference` equals
its `images["aivision-be"]` digest reference, and `backend.apple_silicon.platform`
is `linux/amd64`. Match `BE_IMAGE` or `BACKEND_IMAGE` to
`backend.apple_silicon.reference`. Decode the companion vars'
`AIVISION_RELEASE_MANIFEST_BASE64` and compare it with the base manifest. For this
preview only `images["aivision-be"]` changes, to the declared companion digest.
Keep the four other service pins and the chosen datastore's upstream digest.
Apple notarization is pending for this preview.

Use `release-windows-preview.vars.yaml` only when Windows x64 preview is explicitly
requested. The published Windows assets live alongside the Linux base in the
same Release. Use the authenticated GitHub Releases API's `assets[].digest` to
verify the downloaded `windows-preview.json` and `release-windows-preview.vars.yaml`.
Also compare the vars file's SHA-256 with its entry in `windows-preview.json`.
The base `SHA256SUMS` covers the base files. The Windows bundle's `.sha256`
file covers its ZIP. Confirm `release.repository`, `release.tag`, `product_version`,
`client_platform`, `server_platform`, and `windows_image.registry_ref` in the
verified preview metadata.
Merge the preview vars into one complete isolated Linux x86 test configuration,
keeping the four other service pins and the original database settings. The
published override intentionally clears `AIVISION_RELEASE_MANIFEST_BASE64`. Keep
the verified base manifest and preview metadata privately to record the actual
configuration. Windows native end-to-end acceptance is pending. The Mac and
Windows previews use different backend digests. Deploy a combination only when a
published backend explicitly covers both.

For managed Docker/Compose use the chosen datastore asset and preserve its
matching database selector and digest. For an external datastore, keep
`OB_MANAGED: "false"` and the existing connection settings and database image
policy. Apply a companion only to the target described by its Release. For
Kubernetes, use the target's verified base service images unless a companion
explicitly supports that target.

## Install or upgrade the CLI when needed

Keep an installed CLI that matches the selected build and required capabilities.
Otherwise use [CLI discovery and installation](install-cli.md#discover-a-published-cli)
with the recorded version and client platform, then verify `aiv --version` and
the required `--help` commands. Use the published server CLI for deployment and
the matching Apple Silicon or Windows x64 CLI for Agent onboarding. If you use the checked
`install-aiv.sh` asset, confirm its help and pass the exact repository and tag it
supports. Finish the durable PATH checks below before running a lifecycle command.

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
the effective five image pins and manifest against the selected base or verified
preview configuration before `cast`.
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
