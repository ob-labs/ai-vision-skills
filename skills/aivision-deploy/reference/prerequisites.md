# Prerequisites

Shared prerequisites for the [`aivision-deploy`](../SKILL.md) skill. Select the
deployment target first, then check only the tools required for that target.
The CLI is also usable manually; installing or deploying with `aiv` does not
require this Skill.

The standard product CLI retains source-compatible modes. For an explicitly
selected historical restricted native CLI profile only, use default Docker or
CLI-managed `--target compose` with matching native release variables. It rejects
standalone `--compose-file`. The existing-file instructions below require an
standard source-compatible CLI build; if upgrading such an installation, stop before
replacing its CLI or changing its configuration or services. No automatic
conversion is provided.

## Requirements by target

| Requirement | Needed when |
| --- | --- |
| `aiv` CLI | Default Docker, optional guarded Compose and fixed Kubernetes deployment; native Compose inspection can run without it. Check installed path, version and required commands before use. |
| Docker Compose 2.27+ | Optional Compose on Linux/macOS; Go aiv controls native Compose without host Python or an extra control script. Keep complete matching deployment assets. |
| Running Docker daemon | Docker deployment, or creating a local Kubernetes cluster with the Docker-backed kind recipe. An existing Kubernetes cluster does not require a local Docker daemon. |
| `kubectl` and a prepared cluster | Kubernetes deployment. Confirm the actual context, permissions, StorageClass, and target resources in the [Kubernetes guide](https://aivision.mintlify.site/en/deployment/kubernetes). |
| Bash, `curl`, `jq`, `tar`, SHA256 tool | The bundled product Release download and validation recipe; public downloads use anonymous access. |
| GitHub CLI (`gh`) and GitHub authentication | Fallback for a private product Release, or an explicitly selected historical Skills delivery. An already installed compatible CLI does not need authentication merely to run. |
| Image registry authentication | Only for images that require it. GitHub Release access and container image access are separate permissions. |
| CPU, memory, and storage | According to the selected target and datastore. Reusing OceanBase CE or seekdb removes the bundled datastore requirement, not the resources needed by the remaining services. |
| Network access | Whenever CLI assets, images, or dependencies must be downloaded or refreshed, including retries and upgrades. Do not assume only the first `cast` needs network access. |

Use only archives and image platforms present in the selected published Release.
The CLI host and deployment daemon may have different architectures. Check the
actual manifest and matching vars for runtime/profile requirements; do not
force `NATIVE_PYTHON_RUNTIME` into a standard source-compatible release. The
historical `.20261028.2` reader is x64-only and does not guarantee a download.
The separate Quickstart Python SDK demo and maintainer source-build checks
retain their own Python requirements.

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

Use explicit --target compose on every CLI operation. With standard source-compatible CLI
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

An explicitly selected historical restricted trial CLI has a native-only compile-time profile.
A source-mode CLI with the same version text is not equivalent: install the
checksummed archive from the selected private Release. The earlier `.20261028`
CLI embeds Python deployment helpers and needs replacement for strict delivery.
Native builds reject explicit source runtime/installer choices and standalone
`--compose-file`; use CLI-managed `--target compose` with the native release vars.

## Native Agent client runtime

Read the selected backend Release's actual native installer and ABI requirements.
The historical restricted Daily bundles required their own Linux x64 or ARM64
installer and glibc 2.35 or newer; Debian Bookworm was the qualified client runtime.
Do not carry that qualification forward to another build. Check the
**Agent's own machine** before `aiv connect`:

```bash
getconf GNU_LIBC_VERSION
```

For a selected bundle requiring glibc 2.35, use a compatible Agent machine if
the installed glibc is older. A missing glibc
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

Follow the [channel choice](../SKILL.md#choose-release-or-daily) and resolve one
published immutable Release in `ob-labs/ai-vision-ob` before downloading:

| Choice | Resolve once |
| --- | --- |
| Release (default) | Read the [latest stable Release](https://github.com/ob-labs/ai-vision-ob/releases/latest) or its GitHub `releases/latest` API response; use its exact published `v<version>` tag. Drafts and prereleases are excluded. If none exists, report that fact. |
| Daily/preview | Select an actually published versioned `v<version>-daily.<YYYYMMDD>[.<N>]` prerelease. Read its metadata, manifest and actual platform evidence; no future `0.1.0` tag/date is presumed published. |
| Explicit version | Inspect the exact product Release requested by the user. Only an explicit historical restricted-delivery request selects `ob-labs/ai-vision-skills` with an approved retained `delivery-v` tag. |

Keep the resolved tag for the whole operation, including retries and upgrades.
This workflow does not follow mutable `daily` or `latest` download selectors,
Dev tags, registry tags, workflow attempts or an automatic previous-version
fallback. A missing compatible publication or platform stops installation.
The selected snapshot date stays fixed across midnight/retries; new accepted
revisions need a new immutable version. Read the Release notes for actual native,
emulated or mixed-platform coverage. An archive or multi-platform image index
alone does not qualify runtime, Agent or Kubernetes behavior.

Use the independently bundled [CLI recipe](install-cli.md). It requires Bash,
`curl`, `jq`, `tar` and a SHA256 tool. Public metadata and assets are anonymous;
an authorized `gh` session is fallback for the currently private product
repository. A 403/404 can mean missing publication, missing assets or unavailable
access; authentication does not establish which without inspection.
Repository Git access, binary downloads and image pulls are separate operations.

Export the actual selected tag as `AIV_TAG` in the same terminal. The example below
selects a standard product Release. For an explicitly requested historical
restricted delivery, retain the approved `AIV_REPOSITORY=ob-labs/ai-vision-skills`
override and its matching `delivery-v` tag instead. For deployment,
also set `AIV_RELEASE_DIR` to a **new version-specific directory** under the
existing durable deployment directory before running that recipe. Its parent
must exist. Do not overwrite an existing restore set. For example, after
`AIV_TAG` has been resolved and exported:

```bash
: "${AIV_TAG:?Export the actual published immutable product Release tag first}"
export AIV_REPOSITORY=ob-labs/ai-vision-ob
export AIV_RELEASE_DIR="$PWD/release-$AIV_TAG"
```

Then run the [complete download/install block](install-cli.md#from-a-release).
It checks the exact published repository/tag/channel, the archive, manifest and
both vars checksums, the manifest's source repository/product version/Release
tag, and the extracted CLI version before replacing the permanent CLI. It saves
`release-manifest.json`, `release-images.vars.yaml`, `release-seekdb.vars.yaml`
and `SHA256SUMS` in the new directory. An existing destination stops the recipe;
reuse already verified files for a retry rather than creating another restore
set or silently changing the selected version.

Inspect those files before merging configuration:

- `product_version`, `channel`, `source_repository` and `release_tag` identify
  the exact product Release. Historical deliveries instead identify the exact
  Skills Release in `delivery.repository`/`delivery.release_tag`, retaining
  `delivery.catalog_sha` and original product provenance.
- Every application image in the chosen vars asset must match the manifest's
  `images` digest. The product owns four application image publications; SigNoz
  remains upstream-owned and is pinned by digest. Do not guess namespaces,
  component tags, or architecture-specific replacements.
- `AIVISION_RELEASE_MANIFEST_BASE64` must encode that exact manifest. Preserve
  it when merging so About shows the selected product version without changing
  component build identities.
- Use `release-images.vars.yaml` for Docker OceanBase CE or
  `release-seekdb.vars.yaml` for Docker seekdb. Retain the selected manifest's
  fixed official upstream database digest, and confirm each service/database
  index contains the actual Docker daemon platform. Replace saved retired
  private database-mirror references with the matching upstream refs.
- Keep runtime/profile settings as supplied by the selected Release. The
  standard source-compatible CLI is the default; only an explicit native
  variant uses its matching native settings. Do not force historical
  `NATIVE_PYTHON_RUNTIME: "true"` or infer it from the Daily channel.

Merge the chosen vars into the existing private configuration while retaining
credentials, datastore, history, namespace and data identity. Do not print that
configuration. For Kubernetes, use only its supported image/manifest settings
from the CE vars; follow the [Kubernetes recipe](kubernetes.md) rather than
copying Docker database or runtime settings blindly.

Historical assets/tags remain immutable and retained. The three approved
restricted-delivery guards live only in the explicit historical path; their
old six/seven-asset formats do not constrain product-owned Release assets or
promise historical downloads. This cutover publishes or retires no artifacts.

## Install or upgrade the CLI when needed

The [bundled recipe](install-cli.md) installs in the permanent directory and
preserves an installed binary when Release, checksum, manifest or executable
validation fails. If the installed CLI already matches the selected verified
manifest and needed capabilities, keep it; fetching matching deployment assets
through the recipe may reinstall that same version without changing services.
Confirm `aiv --version` equals the manifest's `product_version`, then repeat the
required help checks above. CLI installation does not upgrade running services.

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

Run deployment commands from the original durable deployment directory, with
the verified manifest/vars retained in `AIV_RELEASE_DIR`. The download recipe
uses and removes its own temporary directory without changing the caller's
working directory. A failed download or verification blocks use of that asset.
Complete durable PATH and fresh-shell verification above before reporting a
finished CLI installation.

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
