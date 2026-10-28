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

Use the deployment's release repository and compatible published versioned tag;
replace `YOUR_RESOLVED_VERSIONED_TAG` below with that actual tag. Resolve Daily
through the versioned-assets link in the `daily` Release; the moving pointer
has no CLI archive. During the restricted trial use an authorized GitHub account
with read access to the delivery repository and an authenticated `gh`. Skill
repository access does not grant Release access. Do not use shared tokens.
The current delivery repository remains `ob-labs/ai-vision-ob`; this Skill
repository does not currently publish CLI binaries. An owner may supply a different
fixed delivery repository/tag; verify its archive/checksums and compatibility
before replacing the assignments below. If no compatible Release is available,
report the missing Release and stop; a product source checkout is not a fallback. Keep
all downloads and extraction out of the caller's working directory:

```bash
export PATH="$HOME/.local/bin:$PATH"
(
  set -eu
  AIV_REPOSITORY=ob-labs/ai-vision-ob
  AIV_TAG=YOUR_RESOLVED_VERSIONED_TAG
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
  AIV_PACKAGE="aiv-$AIV_PLATFORM-$AIV_ARCH.tar.gz"
  AIV_TEMP=$(mktemp -d)
  AIV_STAGED=''
  trap 'rm -rf "$AIV_TEMP"; if [ -n "$AIV_STAGED" ]; then rm -f "$AIV_STAGED"; fi' EXIT HUP INT TERM
  command -v gh >/dev/null 2>&1 || { echo 'GitHub CLI is required for restricted Release downloads.' >&2; exit 1; }
  gh auth status --hostname github.com >/dev/null 2>&1 ||
    { echo 'Authenticate gh with an authorized account before downloading.' >&2; exit 1; }
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
  "$AIV_TEMP/aiv" --version
  mkdir -p "$HOME/.local/bin"
  AIV_STAGED=$(mktemp "$HOME/.local/bin/.aiv-install.XXXXXX")
  cp "$AIV_TEMP/aiv" "$AIV_STAGED"
  chmod 755 "$AIV_STAGED"
  mv -f "$AIV_STAGED" "$HOME/.local/bin/aiv"
  AIV_STAGED=''
  command -v aiv
  aiv --version
)
```

A failed download, checksum or executable check stops installation and preserves
the existing binary. Do not continue with stale output from an earlier attempt.
Before reporting installation complete, finish [durable PATH setup](path-setup.md)
and verify the permanent binary in fresh interactive and login shells with a
clean inherited PATH. A task-local export alone is insufficient. Querying an
existing platform does not require Docker, registry login, deployment prerequisites
or a local Agent hook.
