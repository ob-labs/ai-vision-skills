#!/bin/sh
# Resolve and verify one exact published CLI release for this machine.
set -eu

die() { printf '%s\n' "$*" >&2; exit 1; }
mode=${1:---resolve}
[ "$#" -le 1 ] || die 'Usage: sh install-cli.sh [--resolve|--install]'
case "$mode" in --resolve|--install) ;; *) die 'Usage: sh install-cli.sh [--resolve|--install]' ;; esac
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
requested_tag=${AIV_TAG:-}
case "$requested_tag" in *[!A-Za-z0-9.-]*) die 'Set AIV_TAG to an exact versioned tag.' ;; esac
channel=${AIV_CHANNEL:-daily}
case "$requested_tag" in v[0-9]*) channel=${AIV_CHANNEL:-stable} ;; esac
case "$channel" in
  daily) repository=${AIV_REPOSITORY:-ob-labs/ai-vision-skills}
    [ "$repository" = ob-labs/ai-vision-skills ] || die 'Restricted Daily assets belong to ob-labs/ai-vision-skills.' ;;
  stable) repository=${AIV_REPOSITORY:-ob-labs/ai-vision-ob} ;;
  *) die 'Select AIV_CHANNEL=daily or AIV_CHANNEL=stable.' ;;
esac
case "$repository" in */*/*|/*|*/|*[!A-Za-z0-9_./-]*) die 'Select an OWNER/REPO repository.' ;; */*) ;; *) die 'Select an OWNER/REPO repository.' ;; esac
[ "$mode" != --install ] || [ -n "$requested_tag" ] || die 'Resolve a compatible release, then set AIV_TAG to its exact tag before installing.'
case "$(uname -s)" in Linux) os=linux ;; Darwin) os=darwin ;; *) die 'Use the native Windows PowerShell instructions on Windows.' ;; esac
case "$(uname -m)" in
  x86_64|amd64)
    arch=x64
    if [ "$os" = darwin ] &&
       hardware_arm64=$(PATH="${PATH:-/usr/bin:/bin}:/usr/sbin" sysctl -n hw.optional.arm64 2>/dev/null) &&
       [ "$hardware_arm64" = 1 ]; then arch=arm64; fi ;;
  aarch64|arm64) arch=arm64 ;;
  *) die 'No CLI for this architecture.' ;;
esac
platform="$os-$arch"
case "$platform" in linux-x64|darwin-arm64) ;; *) die 'CLI delivery is available for Linux x64, Apple Silicon, and Windows x64.' ;; esac
for tool in gh jq; do command -v "$tool" >/dev/null 2>&1 || die "$tool is required for CLI release discovery."; done
umask 077
tmp=$(mktemp -d)
staged=''
trap 'rm -rf "$tmp"; if [ -n "$staged" ]; then rm -f "$staged"; fi' EXIT
trap 'exit 1' HUP INT TERM

gh api --hostname github.com --paginate --slurp "repos/$repository/releases?per_page=100" > "$tmp/releases.json"
selection=$(jq -ce --arg platform "$platform" --arg channel "$channel" --arg tag "$requested_tag" \
  -f "$script_dir/discover-cli.jq" "$tmp/releases.json") || die "No compatible published $channel CLI for $platform${requested_tag:+ at $requested_tag}."
tag=$(printf '%s\n' "$selection" | jq -r .tag)
version=$(printf '%s\n' "$selection" | jq -r .product_version)
package=$(printf '%s\n' "$selection" | jq -r .package)
manifest=$(printf '%s\n' "$selection" | jq -r '.manifest // empty')
checksums=$(printf '%s\n' "$selection" | jq -r '.assets.checksums.name')

gh api --hostname github.com "repos/$repository/releases/tags/$tag" > "$tmp/selected.json"
jq -e --argjson expected "$selection" '
  def identity: [.name, .id, .size, .digest, .state];
  .tag_name == $expected.tag and .id == $expected.release_id and .draft == false
  and .prerelease == ($expected.profile != "stable") and (.published_at | type == "string" and length > 0)
  and (.assets as $assets | all($expected.assets[] | select(. != null);
    . as $asset | [$assets[] | select(.name == $asset.name) | identity] == [$asset | identity]))
' "$tmp/selected.json" >/dev/null || die 'The exact release changed during discovery. Resolve it again.'

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}
check_asset_digest() {
  digest=$(printf '%s\n' "$selection" | jq -r --arg name "$1" '.assets[] | select(.name == $name) | .digest // empty')
  [ -z "$digest" ] || [ "$digest" = "sha256:$(hash_file "$tmp/$1")" ] || die "GitHub asset digest mismatch for $1."
}
check_hash() {
  expected=$(awk -v file="$1" '$2 == file { print $1; n++ } END { if (n != 1) exit 1 }' "$tmp/$checksums") || die "Missing or duplicate checksum for $1."
  [ -n "$expected" ] && [ "$expected" = "$(hash_file "$tmp/$1")" ] || die "Checksum mismatch for $1."
}

if [ -n "$manifest" ] || [ "$mode" = --install ]; then
  set -- --pattern "$checksums"
  if [ -n "$manifest" ]; then set -- "$@" --pattern "$manifest"; fi
  if [ "$mode" = --install ]; then set -- "$@" --pattern "$package"; fi
  gh release download "$tag" --repo "github.com/$repository" "$@" --dir "$tmp"
  check_asset_digest "$checksums"
fi
if [ -n "$manifest" ]; then
  check_asset_digest "$manifest"
  check_hash "$manifest"
  jq -e --arg repo "$repository" --argjson expected "$selection" '
    if $expected.profile == "macos" then
      .profile == "macos-codex-preview" and .release_tag == $expected.tag and .base_release == $expected.base_tag
      and (.client["darwin/arm64"].aiv_sha256
           | type == "string" and test("^[a-f0-9]{64}$"))
      and (.assets[$expected.package].sha256 | type == "string" and test("^[a-f0-9]{64}$"))
    else
      .channel == "daily" and .product_version == $expected.product_version
      and .delivery.release_tag == $expected.tag and .delivery.repository == $repo
      and (.cli_platforms | index($expected.cli_platform) != null)
    end
  ' "$tmp/$manifest" >/dev/null || die 'Release manifest does not match the selected version, platform, or base release.'
fi

if [ "$mode" = --resolve ]; then
  printf '%s\n' "$selection" | jq -c --arg repository "$repository" \
    '{repository: $repository, tag, base_tag, product_version, cli_platform, profile, package}'
  exit 0
fi
check_asset_digest "$package"
check_hash "$package"
if [ "$manifest" = macos-codex-preview.json ]; then
  manifest_archive_hash=$(jq -r --arg package "$package" '.assets[$package].sha256' "$tmp/$manifest")
  [ "$manifest_archive_hash" = "$(hash_file "$tmp/$package")" ] || die 'The archive differs from the macOS manifest.'
fi

# Read only the named executable into private staging; tar never writes archive paths.
entries=$(tar -tzf "$tmp/$package" aiv)
[ "$entries" = aiv ] || die 'The archive does not contain exactly one named aiv executable.'
tar -xOzf "$tmp/$package" aiv > "$tmp/aiv"
if [ "$manifest" = macos-codex-preview.json ]; then
  manifest_binary_hash=$(jq -r '.client["darwin/arm64"].aiv_sha256' "$tmp/$manifest")
  [ "$manifest_binary_hash" = "$(hash_file "$tmp/aiv")" ] || die 'The executable differs from the macOS manifest.'
fi
chmod 755 "$tmp/aiv"
[ "$("$tmp/aiv" --version)" = "aiv $version" ] || die 'The executable version differs from the selected Release.'
install_dir=${AIV_INSTALL_DIR:-"$HOME/.local/bin"}
mkdir -p "$install_dir"
[ ! -d "$install_dir/aiv" ] || die 'Installation target is a directory.'
staged=$(mktemp "$install_dir/.aiv-install.XXXXXX")
cp "$tmp/aiv" "$staged"
chmod 755 "$staged"
mv -f "$staged" "$install_dir/aiv"
staged=''
printf 'Installed %s/aiv\naiv %s\n' "$install_dir" "$version"
