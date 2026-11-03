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
`aiv cast --help` output. An unknown command/flag needs a compatible release,
not a new profile or a platform redeployment. Run the download block only when
installation, an upgrade, or verified deployment metadata is needed.

## From a release

The default download owner is `ob-labs/ai-vision-ob`. Select a compatible,
**published immutable tag** and export `AIV_TAG` before running the recipe:
`v<version>` for stable Release or `v<version>-daily.<YYYYMMDD>[.<N>]` for a
Daily/preview. Use the product's standard source-compatible CLI unless the user
explicitly selected a different published profile. No Daily date or future
`0.1.0` tag is assumed to exist by these instructions.

Resolve the version once from the published Release metadata and keep it for
CLI, manifest, vars, and upgrades. This recipe deliberately requires that exact
tag: `daily`, `latest`, Dev tags, and an unset tag stop before downloads. A
missing or draft Release stops installation and preserves an installed binary;
never substitute a different version or source checkout.

Requirements: Bash, `curl`, `jq`, `tar`, and `sha256sum` or `shasum`. Public
metadata and assets are downloaded anonymously. If anonymous access fails,
`gh` with the operator's authorized account can read the currently private
product repository. Check tag/asset existence as well as access on a 403/404;
authentication does not create a missing Release. Skill Git access, image pulls,
platform sessions and model credentials remain separate operations.

For an explicitly requested historical restricted native delivery only, set
`AIV_REPOSITORY=ob-labs/ai-vision-skills` and its exact retained `delivery-v` tag.
The three historical tag/platform/asset guards below remain in force, including
the x64-only `.20261028.2` format. Those readers do not promise available assets.
The withdrawn `.20261028` source-bearing CLI remains rejected. Historical
private downloads always use authenticated `gh`; they are never the default.

Run this in the same terminal after exporting the actual selected `AIV_TAG`.
`AIV_INSTALL_DIR` can choose another permanent installation directory. Deployment
operators can also export `AIV_RELEASE_DIR` as a **new version-specific directory**
to retain the checksummed manifest, both datastore vars and `SHA256SUMS` before
merging the selected vars into existing private configuration. Its parent must
exist; an existing destination stops installation rather than overwriting it.

```bash
export PATH="$HOME/.local/bin:$PATH"
(
  set -eu
  AIV_REPOSITORY=${AIV_REPOSITORY:-ob-labs/ai-vision-ob}
  AIV_TAG=${AIV_TAG:-}
  AIV_INSTALL_DIR=${AIV_INSTALL_DIR:-"$HOME/.local/bin"}
  export PATH="$AIV_INSTALL_DIR:$PATH"
  [ -n "$AIV_TAG" ] || { echo 'Set AIV_TAG to an exact published vVERSION or vVERSION-daily.YYYYMMDD[.N] tag.' >&2; exit 1; }
  command -v jq >/dev/null 2>&1 || { echo 'Install jq for Release JSON validation.' >&2; exit 1; }
  AIV_HISTORICAL=false
  AIV_APPROVED_CLI_ASSETS=''
  case "$AIV_REPOSITORY:$AIV_TAG" in
    ob-labs/ai-vision-ob:v*)
      jq -en --arg tag "$AIV_TAG" '$tag | test("^v[0-9]+\\.[0-9]+\\.[0-9]+(-daily\\.[0-9]{8}(\\.[1-9][0-9]*)?)?$")' >/dev/null ||
        { echo 'Select an immutable stable or Daily product tag; mutable selectors and Dev builds are unsupported.' >&2; exit 1; }
      AIV_PRODUCT_VERSION=${AIV_TAG#v} ;;
    ob-labs/ai-vision-skills:delivery-v0.0.1-daily.20261028.2)
      AIV_HISTORICAL=true
      AIV_PRODUCT_VERSION=${AIV_TAG#delivery-v}
      AIV_APPROVED_CLI_ASSETS='aiv-linux-x64.tar.gz' ;;
    ob-labs/ai-vision-skills:delivery-v0.0.1-daily.20261029|ob-labs/ai-vision-skills:delivery-v0.1.0-daily.20261101)
      AIV_HISTORICAL=true
      AIV_PRODUCT_VERSION=${AIV_TAG#delivery-v}
      AIV_APPROVED_CLI_ASSETS='aiv-linux-x64.tar.gz aiv-linux-arm64.tar.gz' ;;
    *) echo 'Unsupported repository/tag. Historical native deliveries require their explicit Skills repository and approved tag.' >&2; exit 1 ;;
  esac
  case "$AIV_PRODUCT_VERSION" in
    *-daily.*) AIV_CHANNEL=daily; AIV_PRERELEASE=true ;;
    *) AIV_CHANNEL=stable; AIV_PRERELEASE=false ;;
  esac
  case "$(uname -s)" in
    Linux) AIV_PLATFORM=linux ;;
    Darwin) AIV_PLATFORM=darwin ;;
    *) echo 'Supported CLI platforms: Linux and macOS.' >&2; exit 1 ;;
  esac
  case "$(uname -m)" in
    x86_64|amd64) AIV_ARCH=x64 ;;
    arm64|aarch64) AIV_ARCH=arm64 ;;
    *) echo 'Supported CLI architectures: x64 and arm64.' >&2; exit 1 ;;
  esac
  AIV_PACKAGE="aiv-$AIV_PLATFORM-$AIV_ARCH.tar.gz"
  if [ "$AIV_HISTORICAL" = true ]; then
    case " $AIV_APPROVED_CLI_ASSETS " in
      *" $AIV_PACKAGE "*) ;;
      *) echo 'The historical delivery does not support this CLI platform.' >&2; exit 1 ;;
    esac
  fi
  AIV_TEMP=$(mktemp -d)
  AIV_STAGED=''
  trap 'rm -rf "$AIV_TEMP"; if [ -n "$AIV_STAGED" ]; then rm -f "$AIV_STAGED"; fi' EXIT HUP INT TERM
  aiv_require_auth() {
    command -v gh >/dev/null 2>&1 && gh auth status --hostname github.com >/dev/null 2>&1 ||
      { echo 'Release access failed. For a private repository, authenticate gh with your authorized account; also check the exact tag and asset.' >&2; return 1; }
  }
  AIV_API="repos/$AIV_REPOSITORY/releases/tags/$AIV_TAG"
  AIV_RELEASE_URL="https://github.com/$AIV_REPOSITORY/releases"
  if [ "$AIV_HISTORICAL" = true ]; then
    aiv_require_auth
    gh api "$AIV_API" > "$AIV_TEMP/release.json"
  elif ! curl --fail --silent --show-error --location "https://api.github.com/$AIV_API" --output "$AIV_TEMP/release.json"; then
    aiv_require_auth
    gh api "$AIV_API" > "$AIV_TEMP/release.json"
  fi
  jq -e --arg tag "$AIV_TAG" --arg url "$AIV_RELEASE_URL/tag/$AIV_TAG" --argjson preview "$AIV_PRERELEASE" '
    .tag_name == $tag and .html_url == $url and .draft == false and
    .prerelease == $preview and (.published_at | type == "string" and length > 0) and
    (.assets | type == "array") and
    (([.assets[].name] | length) == ([.assets[].name] | unique | length))
  ' "$AIV_TEMP/release.json" >/dev/null ||
    { echo 'The exact published Release is unavailable or has the wrong repository/channel.' >&2; exit 1; }
  if [ "$AIV_HISTORICAL" = true ]; then
    AIV_ASSETS=$(jq -r '.assets[].name' "$AIV_TEMP/release.json" | LC_ALL=C sort)
    AIV_EXPECTED_ASSETS=$(printf '%s\n' $AIV_APPROVED_CLI_ASSETS install-aiv.sh \
      release-manifest.json release-images.vars.yaml release-seekdb.vars.yaml SHA256SUMS | LC_ALL=C sort)
    [ "$AIV_ASSETS" = "$AIV_EXPECTED_ASSETS" ] ||
      { echo 'The historical Daily must contain exactly its approved asset set.' >&2; exit 1; }
  fi
  for AIV_ASSET in "$AIV_PACKAGE" SHA256SUMS release-manifest.json release-images.vars.yaml release-seekdb.vars.yaml; do
    AIV_URL=$(jq -er --arg name "$AIV_ASSET" --arg url "$AIV_RELEASE_URL/download/$AIV_TAG/$AIV_ASSET" '
      [.assets[] | select(.name == $name and .browser_download_url == $url)] |
      if length == 1 then .[0].browser_download_url else error("missing exact Release asset") end
    ' "$AIV_TEMP/release.json")
    if [ "$AIV_HISTORICAL" = true ]; then
      gh release download "$AIV_TAG" -R "$AIV_REPOSITORY" -p "$AIV_ASSET" --dir "$AIV_TEMP"
    elif ! curl --fail --silent --show-error --location "$AIV_URL" --output "$AIV_TEMP/$AIV_ASSET"; then
      rm -f "$AIV_TEMP/$AIV_ASSET"
      aiv_require_auth
      gh release download "$AIV_TAG" -R "$AIV_REPOSITORY" -p "$AIV_ASSET" --dir "$AIV_TEMP"
    fi
  done
  for AIV_ASSET in "$AIV_PACKAGE" release-manifest.json release-images.vars.yaml release-seekdb.vars.yaml; do
    if command -v sha256sum >/dev/null 2>&1; then
      AIV_ACTUAL=$(sha256sum "$AIV_TEMP/$AIV_ASSET" | awk '{print $1}')
    else
      AIV_ACTUAL=$(shasum -a 256 "$AIV_TEMP/$AIV_ASSET" | awk '{print $1}')
    fi
    AIV_EXPECTED=$(awk -v f="$AIV_ASSET" '$2 == f {print $1; n++} END {if (n != 1) exit 1}' "$AIV_TEMP/SHA256SUMS")
    [ -n "$AIV_EXPECTED" ] && [ "$AIV_EXPECTED" = "$AIV_ACTUAL" ] ||
      { echo "Checksum mismatch for $AIV_ASSET." >&2; exit 1; }
  done
  jq -e --arg version "$AIV_PRODUCT_VERSION" --arg channel "$AIV_CHANNEL" --arg tag "$AIV_TAG" \
    --arg repository "$AIV_REPOSITORY" --argjson historical "$AIV_HISTORICAL" '
    .product_version == $version and .channel == $channel and .source_repository == "ob-labs/ai-vision-ob" and
    (if $historical then .delivery.repository == $repository and .delivery.release_tag == $tag
     else .release_tag == $tag end)
  ' "$AIV_TEMP/release-manifest.json" >/dev/null ||
    { echo 'Manifest repository, version, channel or Release tag differs from the selected Release.' >&2; exit 1; }
  tar -xzf "$AIV_TEMP/$AIV_PACKAGE" -C "$AIV_TEMP" aiv
  [ -f "$AIV_TEMP/aiv" ] && [ ! -L "$AIV_TEMP/aiv" ]
  chmod 755 "$AIV_TEMP/aiv"
  AIV_ACTUAL_VERSION=$("$AIV_TEMP/aiv" --version)
  [ "$AIV_ACTUAL_VERSION" = "aiv $AIV_PRODUCT_VERSION" ] ||
    { echo 'CLI product version differs from the selected Release.' >&2; exit 1; }
  if [ -n "${AIV_RELEASE_DIR:-}" ]; then
    mkdir "$AIV_RELEASE_DIR"  # Use a new version-specific directory; never overwrite saved metadata.
    for AIV_ASSET in SHA256SUMS release-manifest.json release-images.vars.yaml release-seekdb.vars.yaml; do
      cp "$AIV_TEMP/$AIV_ASSET" "$AIV_RELEASE_DIR/$AIV_ASSET"
    done
  fi
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

The recipe checks exact Release repository/tag/channel, checksums for the
archive, manifest and both vars, manifest source repository/product version/tag,
and the extracted CLI version before atomic binary replacement. It consumes the
Release's actual platform archive and metadata; it does not assume a native
profile, image namespace, or service architecture from the CLI host. Product
Releases may contain additional product-owned assets. Only explicit historical
Skills deliveries retain their exact six/seven-asset allowlists.

Before deployment, inspect the retained manifest and matching vars through the
deployment Skill. Use their exact image and database digest pins, embedded
manifest and runtime settings; a native variant's settings do not apply to the
standard source-compatible CLI automatically. Docker selects the service image
child on the deployment daemon, which may differ from the CLI machine. CLI
installation alone does not establish service, Agent, Kubernetes or model
compatibility.

A failed download, validation or executable check preserves the existing binary.
The `delivery-v` prefix is historical distribution metadata; `aiv --version`
always prints the product version. This CLI recipe uses no user-installed Python;
the separate Quickstart Python SDK demo has its own runtime requirements.
Before reporting installation complete, finish [durable PATH setup](prerequisites.md#finish-durable-path-setup)
and verify the permanent binary in fresh interactive and login shells with a
clean inherited PATH. A task-local export alone is insufficient. The CLI download itself does not log into the image registry, initialize a
datastore, or deploy services. Continue with the matching vars and deployment
prerequisites after checking the installed CLI.
