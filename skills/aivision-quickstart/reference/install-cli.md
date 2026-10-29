# Installing the `aiv` CLI

First expose the default install directory in **this terminal**, then check the
binary actually selected. This also reuses an installed CLI while offline:

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v aiv
aiv --version
```

If `aiv` is installed elsewhere, use that confirmed directory in the export.
A version alone does not prove support for this skill: inspect the relevant
`aiv query … --help` output. An unknown command/flag needs a compatible release,
not a new profile or a platform redeployment. Run the download block only when
installation or an upgrade is needed.

## From a release

Use the deployment's compatible published versioned Release. Restricted Daily
downloads use `ob-labs/ai-vision-skills` and a fixed
`delivery-v<product-version>` prerelease. The selected default below is
`delivery-v0.0.1-daily.20261029`, selecting Linux x64 or ARM64 CLI archives with
`uname` and declaring both `linux/amd64` and `linux/arm64` service images.
It is available only after its exact prerelease is published and all seven assets
are verified. Catalog changes do not establish release or runtime acceptance.
An absent or draft Release stops installation and preserves the installed binary.
Older trial Releases are retired after the replacement is verified; do not use
an older version as a download fallback. The `.20261028.2` branch below preserves
historical x64-only reader compatibility, not download availability.

The native CLI profile excludes legacy first-party Python resources at link time.
The retired `delivery-v0.0.1-daily.20261028` CLI contains source-mode helpers and
must not be used for strict native delivery.

Use the operator's authenticated `gh` account with authorized read access; do
not share tokens. Do not resolve this Daily through the old product `daily`
pointer or `releases/latest`. Stable product Releases retain their original
channel: for one of those, replace the repository with `ob-labs/ai-vision-ob`
and the tag with its actual published `v<product-version>`. Confirm compatibility
with the existing platform before replacing an installed CLI. A missing Release,
archive, or supported host platform stops installation; a product source
checkout is not a fallback. Keep downloads and extraction out of the caller's
working directory:

```bash
export PATH="$HOME/.local/bin:$PATH"
(
  set -eu
  AIV_REPOSITORY=${AIV_REPOSITORY:-ob-labs/ai-vision-skills}
  AIV_TAG=${AIV_TAG:-delivery-v0.0.1-daily.20261029}
  AIV_INSTALL_DIR=${AIV_INSTALL_DIR:-"$HOME/.local/bin"}
  export PATH="$AIV_INSTALL_DIR:$PATH"
  [ "$AIV_TAG" != delivery-v0.0.1-daily.20261028 ] ||
    { echo 'Select a supported native Daily; the earlier CLI contains legacy Python resources.' >&2; exit 1; }
  case "$AIV_TAG" in
    delivery-v*) AIV_PRODUCT_VERSION=${AIV_TAG#delivery-v}; AIV_PRERELEASE=true ;;
    v*) AIV_PRODUCT_VERSION=${AIV_TAG#v}; AIV_PRERELEASE=false ;;
    *) echo 'Select an exact published delivery-v or stable v tag.' >&2; exit 1 ;;
  esac
  case "$(uname -s)" in
    Linux) AIV_PLATFORM=linux ;;
    Darwin) AIV_PLATFORM=darwin ;;
    *) echo 'Supported platforms: Linux and macOS' >&2; exit 1 ;;
  esac
  case "$(uname -m)" in
    x86_64|amd64) AIV_ARCH=x64 ;;
    arm64|aarch64) AIV_ARCH=arm64 ;;
    *) echo 'Supported architectures: x64 and arm64' >&2; exit 1 ;;
  esac
  AIV_APPROVED_CLI_ASSETS=''
  case "$AIV_TAG" in
    delivery-v0.0.1-daily.20261028.2)
      [ "$AIV_PLATFORM-$AIV_ARCH" = linux-x64 ] ||
        { echo 'The explicit .20261028.2 delivery supports Linux x64 only.' >&2; exit 1; }
      AIV_APPROVED_CLI_ASSETS='aiv-linux-x64.tar.gz' ;;
    delivery-v0.0.1-daily.20261029)
      case "$AIV_PLATFORM-$AIV_ARCH" in
        linux-x64|linux-arm64) ;;
        *) echo 'This delivery selects Linux x64 and ARM64 only.' >&2; exit 1 ;;
      esac
      AIV_APPROVED_CLI_ASSETS='aiv-linux-x64.tar.gz aiv-linux-arm64.tar.gz' ;;
    delivery-v*)
      echo 'Resolve an explicitly supported native Daily and its platform contract first.' >&2; exit 1 ;;
  esac
  AIV_PACKAGE="aiv-$AIV_PLATFORM-$AIV_ARCH.tar.gz"
  AIV_TEMP=$(mktemp -d)
  AIV_STAGED=''
  trap 'rm -rf "$AIV_TEMP"; if [ -n "$AIV_STAGED" ]; then rm -f "$AIV_STAGED"; fi' EXIT HUP INT TERM
  command -v gh >/dev/null 2>&1 || { echo 'GitHub CLI is required for restricted Release downloads.' >&2; exit 1; }
  gh auth status --hostname github.com >/dev/null 2>&1 ||
    { echo 'Authenticate gh with an authorized account before downloading.' >&2; exit 1; }
  AIV_RESOLVED_TAG=$(gh release view "$AIV_TAG" -R "$AIV_REPOSITORY" \
    --json tagName,isDraft,isPrerelease,publishedAt \
    --jq "select(.isDraft == false and .isPrerelease == $AIV_PRERELEASE and .publishedAt != null) | .tagName")
  [ "$AIV_RESOLVED_TAG" = "$AIV_TAG" ] ||
    { echo 'The exact published Release is unavailable or has the wrong channel.' >&2; exit 1; }
  if [ -n "$AIV_APPROVED_CLI_ASSETS" ]; then
    [ "$AIV_REPOSITORY" = ob-labs/ai-vision-skills ] ||
      { echo 'Restricted Daily assets belong to ob-labs/ai-vision-skills.' >&2; exit 1; }
    AIV_ASSETS=$(gh release view "$AIV_TAG" -R "$AIV_REPOSITORY" \
      --json assets --jq '.assets[].name' | LC_ALL=C sort)
    AIV_EXPECTED_ASSETS=$(printf '%s\n' $AIV_APPROVED_CLI_ASSETS install-aiv.sh \
      release-manifest.json release-images.vars.yaml release-seekdb.vars.yaml SHA256SUMS | LC_ALL=C sort)
    [ "$AIV_ASSETS" = "$AIV_EXPECTED_ASSETS" ] ||
      { echo 'The Daily must contain exactly its approved asset set.' >&2; exit 1; }
  fi
  gh release download "$AIV_TAG" -R "$AIV_REPOSITORY" \
    -p "$AIV_PACKAGE" -p SHA256SUMS --dir "$AIV_TEMP"
  if command -v sha256sum >/dev/null 2>&1; then
    AIV_ACTUAL=$(sha256sum "$AIV_TEMP/$AIV_PACKAGE" | awk '{print $1}')
  else
    AIV_ACTUAL=$(shasum -a 256 "$AIV_TEMP/$AIV_PACKAGE" | awk '{print $1}')
  fi
  AIV_EXPECTED=$(awk -v f="$AIV_PACKAGE" '$2 == f {print $1; n++} END {if (n != 1) exit 1}' "$AIV_TEMP/SHA256SUMS")
  [ -n "$AIV_EXPECTED" ] && [ "$AIV_EXPECTED" = "$AIV_ACTUAL" ] ||
    { echo "checksum mismatch for $AIV_PACKAGE" >&2; exit 1; }
  tar -xzf "$AIV_TEMP/$AIV_PACKAGE" -C "$AIV_TEMP" aiv
  [ -f "$AIV_TEMP/aiv" ] && [ ! -L "$AIV_TEMP/aiv" ]
  chmod 755 "$AIV_TEMP/aiv"
  AIV_ACTUAL_VERSION=$("$AIV_TEMP/aiv" --version)
  [ "$AIV_ACTUAL_VERSION" = "aiv $AIV_PRODUCT_VERSION" ] ||
    { echo 'CLI product version differs from the selected Release.' >&2; exit 1; }
  mkdir -p "$AIV_INSTALL_DIR"
  AIV_STAGED=$(mktemp "$AIV_INSTALL_DIR/.aiv-install.XXXXXX")
  cp "$AIV_TEMP/aiv" "$AIV_STAGED"
  chmod 755 "$AIV_STAGED"
  mv -f "$AIV_STAGED" "$AIV_INSTALL_DIR/aiv"
  AIV_STAGED=''
  command -v aiv
  aiv --version
)
```

`AIV_TAG` selects an explicit compatible version; leaving it unset selects the
prepared Daily above. `AIV_INSTALL_DIR` can select another permanent directory.
The same recipe runs on Linux x64 and ARM64 without editing architecture values.
Docker selects a service child manifest from the release's multi-platform image
index on the deployment host; a CLI architecture does not choose the server's
architecture. Before deployment, verify the manifest and matching vars through
the deployment Skill.

A failed download, checksum or executable check stops installation and preserves
the existing binary. Do not continue with stale output from an earlier attempt.
The `delivery-v` tag prefix is distribution metadata; `aiv --version` prints the
product version (`0.0.1-daily.20261029` for the selected default). The checksummed
`install-aiv.sh` asset is an alternative only when it uses authenticated `gh`
for private downloads and the same fixed repository/tag. This CLI installation
does not require user-installed Python. The separate Quickstart Python SDK demo
has its own runtime requirements.
Before reporting installation complete, finish [durable PATH setup](path-setup.md)
and verify the permanent binary in fresh interactive and login shells with a
clean inherited PATH. A task-local export alone is insufficient. Querying an
existing platform does not require Docker, registry login, deployment prerequisites
or a local Agent hook.
