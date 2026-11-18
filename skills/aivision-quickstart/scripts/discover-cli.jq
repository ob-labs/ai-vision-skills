# Input: an array of public GitHub Releases API pages.
def decimal: "(?:0|[1-9][0-9]*)";
def semver: "\(decimal)\\.\(decimal)\\.\(decimal)";
def published:
  select(.draft == false and (.published_at | type == "string" and length > 0));
def uploaded($name):
  [.assets[]? | select(.name == $name)]
  | if length == 1 then .[0] | select(.state == "uploaded" and .size > 0) else empty end;

if (["daily", "stable"] | index($channel)) == null then error("Select daily or stable") else . end
| if (["linux-x64", "linux-arm64", "darwin-x64", "darwin-arm64", "windows-x64"] | index($platform)) == null
  then error("Unsupported CLI platform") else . end
| "aiv-\($platform).\(if $platform == "windows-x64" then "zip" else "tar.gz" end)" as $package
| [
    .[][] | published
    | select($tag == "" or $tag == "__auto__" or .tag_name == $tag)
    | .tag_name as $name
    | (if $channel == "stable" then
        select(.prerelease == false) | $name | capture("^v(?<version>\(semver))$")
      else
        select(.prerelease == true)
        | $name | capture("^v(?<version>\(semver)-daily\\.[0-9]{8}(?:\\.[1-9][0-9]*)?)$")
      end) as $version
    | uploaded($package) as $binary
    | uploaded("release-manifest.json") as $manifest
    | uploaded("SHA256SUMS") as $checksums
    | uploaded("release-images.vars.yaml") as $oceanbase
    | uploaded("release-seekdb.vars.yaml") as $seekdb
    | {tag: $name, base_tag: $name, product_version: $version.version, release_id: .id,
       profile: $channel, cli_platform: $platform, package: $package,
       assets: {package: $binary, manifest: $manifest, checksums: $checksums,
                oceanbase: $oceanbase, seekdb: $seekdb}}
  ]
| sort_by(.product_version | [scan("[0-9]+") | tonumber] + [0, 0] | .[0:5])
| last // empty
