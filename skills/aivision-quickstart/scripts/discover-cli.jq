# Input: an array of GitHub Releases API pages from gh api --paginate --slurp.
def decimal: "(?:0|[1-9][0-9]*)";
def semver: "\(decimal)\\.\(decimal)\\.\(decimal)";
def daily: "\(semver)-daily\\.[0-9]{8}(?:\\.[1-9][0-9]*)?";
def version_order:
  [scan("[0-9]+") | tonumber] + [0, 0];
def uploaded($name):
  [.assets[]? | select(.name == $name and .state == "uploaded" and .size > 0)]
  | if length == 1 then .[0] else empty end;
def published:
  select(.draft == false and (.published_at | type == "string" and length > 0));

if (["daily", "stable"] | index($channel)) == null then error("Select daily or stable") else . end
| if (["linux-x64", "darwin-arm64", "windows-x64"] | index($platform)) == null
  then error("Supported CLI platforms: Linux x64, Apple Silicon, and Windows x64") else . end
| [.[][] | published] as $releases
| "aiv-\($platform).\(if $platform == "windows-x64" then "zip" else "tar.gz" end)" as $package
| [
    $releases[]
    | select($tag == "" or $tag == "__auto__" or .tag_name == $tag)
    | .tag_name as $name
    | uploaded($package) as $binary
    | (if $channel == "stable" then
        select(.prerelease == false)
        | $name | capture("^v(?<version>\(semver))$")
        | {product_version: .version, base_tag: $name, profile: "stable", update: 0, manifest: null}
      elif ($name | startswith("macos-codex-preview-v")) then
        select(.prerelease == true and $platform == "darwin-arm64")
        | $name | capture("^macos-codex-preview-v(?<version>\(daily))\\.(?<update>[1-9][0-9]*)$")
        | "delivery-v\(.version)" as $base
        | select(any($releases[]; .tag_name == $base and .prerelease == true
                    and ([uploaded("release-manifest.json"), uploaded("SHA256SUMS")] | length == 2)))
        | {product_version: .version, base_tag: $base, profile: "macos", update: (.update | tonumber), manifest: "macos-codex-preview.json"}
      else
        select(.prerelease == true and $name != "delivery-v0.0.1-daily.20261028")
        | $name | capture("^delivery-v(?<version>\(daily))$")
        | {product_version: .version, base_tag: $name, update: 0}
        | if $platform == "windows-x64" then . + {profile: "windows", manifest: "windows-preview.json"}
          else . + {profile: "daily", manifest: "release-manifest.json"} end
      end) as $selection
    | uploaded("SHA256SUMS") as $sums
    | (if $selection.manifest then uploaded($selection.manifest) else null end) as $manifest
    | if $selection.profile == "windows" then
        select([$binary.digest, $manifest.digest] | all(type == "string" and test("^sha256:[a-f0-9]{64}$")))
      else . end
    | $selection + {tag: $name, cli_platform: $platform, package: $package, release_id: .id,
                    assets: {package: $binary, manifest: $manifest, checksums: $sums}}
  ]
| sort_by((.product_version | version_order)[0:5] + [.update, .tag])
| last // empty
