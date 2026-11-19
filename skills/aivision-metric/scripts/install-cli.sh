#!/bin/sh
# Resolve and verify one exact public product CLI release for this machine.
set -eu

die() { printf '%s\n' "$*" >&2; exit 1; }
mode=${1:---resolve}
[ "$#" -le 1 ] || die 'Usage: sh install-cli.sh [--resolve|--install]'
case "$mode" in --resolve|--install) ;; *) die 'Usage: sh install-cli.sh [--resolve|--install]' ;; esac
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository=antgroup/ai-vision
[ "${AIV_REPOSITORY:-$repository}" = "$repository" ] || die 'Product releases belong to antgroup/ai-vision.'
requested_tag=${AIV_TAG:-}
case "$requested_tag" in ''|v[0-9]*) ;; *) die 'Set AIV_TAG to an exact versioned product tag.' ;; esac
case "$requested_tag" in *[!A-Za-z0-9.-]*) die 'Set AIV_TAG to an exact versioned product tag.' ;; esac
case "$requested_tag" in *-daily.*) default_channel=daily ;; *) default_channel=stable ;; esac
channel=${AIV_CHANNEL:-$default_channel}
case "$channel" in daily|stable) ;; *) die 'Select AIV_CHANNEL=daily or AIV_CHANNEL=stable.' ;; esac
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
for tool in curl jq; do command -v "$tool" >/dev/null 2>&1 || die "$tool is required for CLI release discovery."; done
umask 077
tmp=$(mktemp -d)
staged=''
trap 'rm -rf "$tmp"; if [ -n "$staged" ]; then rm -f "$staged"; fi' EXIT
trap 'exit 1' HUP INT TERM

request() {
    curl -q --fail --silent --show-error --location --connect-timeout 15 --proto '=https' --proto-redir '=https' --tlsv1.2 "$@"
}
api="https://api.github.com/repos/$repository/releases"
if [ -n "$requested_tag" ]; then
    request "$api/tags/$requested_tag" -o "$tmp/exact.json"
    jq -ce '[[.]]' "$tmp/exact.json" > "$tmp/releases.json"
else
    page=1
    while :; do
        request "$api?per_page=100&page=$page" -o "$tmp/page.json"
        jq -ce 'if type == "array" then . else error("Invalid releases page") end' "$tmp/page.json" >> "$tmp/pages.jsonl"
        [ "$(jq 'length' "$tmp/page.json")" -eq 100 ] || break
        page=$((page + 1))
    done
    jq -s '.' "$tmp/pages.jsonl" > "$tmp/releases.json"
fi
selection=$(jq -ce --arg platform "$platform" --arg channel "$channel" --arg tag "$requested_tag" \
    -f "$script_dir/discover-cli.jq" "$tmp/releases.json") || die "No compatible published $channel CLI for $platform${requested_tag:+ at $requested_tag}."
tag=$(printf '%s\n' "$selection" | jq -r .tag)
version=$(printf '%s\n' "$selection" | jq -r .product_version)
package=$(printf '%s\n' "$selection" | jq -r .package)
request "$api/tags/$tag" -o "$tmp/selected.json"
jq -e --argjson expected "$selection" '
    def identity: [.name, .id, .size, .digest, .state];
    .tag_name == $expected.tag and .id == $expected.release_id and .draft == false
    and .prerelease == ($expected.profile == "daily") and (.published_at | type == "string" and length > 0)
    and (.assets as $assets | all($expected.assets[];
        . as $asset | [$assets[] | select(.name == $asset.name) | identity] == [$asset | identity]))
' "$tmp/selected.json" >/dev/null || die 'The exact release or its assets changed during discovery. Resolve it again.'

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
    else shasum -a 256 "$1" | awk '{print $1}'; fi
}
fetch_asset() {
    name=$1
    request "https://github.com/$repository/releases/download/$tag/$name" -o "$tmp/$name"
    actual_size=$(wc -c < "$tmp/$name" | tr -d '[:space:]')
    expected_size=$(printf '%s\n' "$selection" | jq -r --arg name "$name" '.assets[] | select(.name == $name) | .size')
    [ "$actual_size" = "$expected_size" ] || die "GitHub asset size mismatch for $name."
    digest=$(printf '%s\n' "$selection" | jq -r --arg name "$name" '.assets[] | select(.name == $name) | .digest // empty')
    [ -z "$digest" ] || [ "$digest" = "sha256:$(hash_file "$tmp/$name")" ] || die "GitHub asset digest mismatch for $name."
}
expected_hash() {
    awk -v file="$1" '
        $2 == file || $2 == "*" file {
            if (length($1) != 64 || $1 ~ /[^a-f0-9]/) invalid=1
            print $1; n++
        }
        END { if (n != 1 || invalid) exit 1 }
    ' "$tmp/SHA256SUMS" || die "Missing, invalid, or duplicate checksum for $1."
}
fetch_asset SHA256SUMS
fetch_asset release-manifest.json
[ "$(expected_hash release-manifest.json)" = "$(hash_file "$tmp/release-manifest.json")" ] || die 'Product manifest checksum mismatch.'
archive_hash=$(expected_hash "$package")
expected_hash release-images.vars.yaml >/dev/null
expected_hash release-seekdb.vars.yaml >/dev/null
jq -e --arg tag "$tag" --arg version "$version" --arg channel "$channel" \
    -f "$script_dir/verify-release-manifest.jq" "$tmp/release-manifest.json" >/dev/null || die 'Product manifest does not match the selected published release.'

if [ "$mode" = --resolve ]; then
    printf '%s\n' "$selection" | jq -c --arg repository "$repository" \
        '{repository: $repository, tag, base_tag, product_version, cli_platform, profile, package}'
    exit 0
fi
fetch_asset "$package"
[ "$archive_hash" = "$(hash_file "$tmp/$package")" ] || die "Checksum mismatch for $package."
entries=$(tar -tzf "$tmp/$package" aiv)
[ "$entries" = aiv ] || die 'The archive does not contain exactly one named aiv executable.'
case "$(tar -tvzf "$tmp/$package" aiv)" in -*) ;; *) die 'The archive executable must be a regular file.' ;; esac
tar -xOzf "$tmp/$package" aiv > "$tmp/aiv"
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
