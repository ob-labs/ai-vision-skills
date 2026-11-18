# Distribution Ownership

`ob-labs/ai-vision-skills` maintains the four Skills, their bundled references
and scripts, and catalog checks. `antgroup/ai-vision` owns product source,
canonical deploy assets, product releases, and build and qualification evidence.
An installed Skill has its own execution resources and needs no product checkout.

## Distributed Stable and Daily

The [public product releases](https://github.com/antgroup/ai-vision/releases)
provide Stable `vMAJOR.MINOR.PATCH` and Daily
`vMAJOR.MINOR.PATCH-daily.YYYYMMDD[.N]` versions. Download each asset from the
same exact published tag and verify `SHA256SUMS`. The release manifest records
the source SHA, product version, build identity, and actual digest for each of
the five service packages. Keep those references during deployment and upgrades.

| Assets | Ownership and use |
| --- | --- |
| `aiv-linux-{x64,arm64}.tar.gz`, `aiv-darwin-{x64,arm64}.tar.gz` | Select the archive for the actual CLI host and verify `aiv --version`. |
| `release-manifest.json`, `SHA256SUMS` | Exact product identity and checksums for the published assets. |
| `release-images.vars.yaml`, `release-seekdb.vars.yaml` | Verified settings for bundled OceanBase CE and seekdb. Preserve private settings and existing datastore identity. |
| `ghcr.io/antgroup/ai-vision/` | `frontend`, `backend`, `ingest-gateway`, `diagnosis`, and `data-backend` images. The data-backend is a digest-pinned mirror of the selected upstream SigNoz image. |
| Upstream OceanBase CE and seekdb | Select the upstream database digest from the product manifest. |

Resolve compatibility with the actual CLI, Docker daemon or cluster, and Agent
client. A candidate-only Actions run can qualify its exact artifacts with no
published Release. The public installer uses published versions. For trial
validation, use the exact Actions assets and retain the run and attempt evidence.

## All-in-One

The [All-in-One guide](../skills/aivision-deploy/reference/all-in-one.md) covers
personal deployment on Linux Docker. Use a separately qualified bundle for the
native Docker host architecture. Its version, base Daily, image archive,
manifest, optional Agent CLI, and checksums must correspond to the same bundle.
A distributed release's five service images do not by themselves supply this
single-container bundle. An operator can install a verified local bundle with
`--from-dir` without publication.

Historical restricted `all-in-one-preview-v*` and `delivery-v*` releases
retain their recorded assets and qualification only for their own versions.
Existing authorized users can rely on pinned historical assets while available.
The historical catalog references are kept for that purpose. Retirement,
permission changes, and publication of historical assets are separate actions.

## Authentication boundaries

Git access to the Skills catalog, public product asset downloads, image pulls,
AI Vision login, query SpaceKeys, and model-provider keys are separate operations.
Public product assets and public GHCR packages support anonymous access. Keep
application credentials and private configuration outside version control.
