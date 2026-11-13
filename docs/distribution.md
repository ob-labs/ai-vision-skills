# Distribution Ownership

## Current state

This private repository owns the four maintained Skills and the restricted-trial Daily delivery channel. A base delivery uses a published `delivery-v<product-version>` GitHub prerelease. It can include separately named Apple Silicon preview assets alongside the base files. Historical platform companions identify the exact base they extend. Published assets and manifest platform fields determine what is available.

Discover published candidates through authenticated GitHub Release metadata. Select by product version, requested client platform and available artifacts. The current trial covers Linux x64 services and CLI, Apple Silicon macOS clients, and Windows x64 client previews. For deployment, validate the Linux x64 Docker host in the base manifest and use the database vars from the selected release. Show the resolved version before upgrading and keep its exact tag through the operation.

Ordinary later publication preserves earlier accepted Releases, assets and tags. Retirement requires separate maintainer authorization; never silently substitute an older download for the selected version. Preserve private historical artifacts, checksums, catalog/build identities and qualification records for audit. Historical readers and tests may still recognize the six-asset, x64-only `.20261028.2` format; that compatibility does not promise a GitHub Release or downloadable assets. Published assets remain immutable while retained; retirement does not authorize moving an old tag or changing its bytes.

For the Linux x64 Agent trial, the selected backend must serve the matching native installer, which requires glibc 2.35 or newer. Debian Bookworm/glibc 2.36 is the recorded client baseline. Check the Agent machine separately from the deployment machine: the static Go CLI and containerized services can run on a Docker host whose glibc is older. Such a host does not qualify the native installer; glibc 2.32 cannot launch this bundle. Keep the client ABI and actual test environment explicit in delivery evidence, and use a compatible Agent machine rather than a source-installer fallback.

Existing organization and repository permissions apply; this delivery adds no user or team access grants. Access by a recipient without product-source permissions must be checked independently. A maintainer's successful clone or package push does not prove recipient access.

The corrected CLI is compiled with `native_distribution`: source-mode Python resources are excluded before linking and the actual executable is checked. Default source builds remain product-owned and are not restricted-trial artifacts. The earlier `delivery-v0.0.1-daily.20261028` Release was withdrawn because its CLI contains legacy deployment Python and fails this boundary; its downloads are no longer available. Original local artifacts and qualification evidence remain retained.

On 2026-10-29, an explicit maintainer-authorized, one-time database-source correction updated the existing `.2` manifest, both deployment vars and checksums. The CLI and installer bytes, five application images and product build identity did not change. The historical `.2` delivery recorded catalog commit `9ac54119a9197b94d9efb7b1b0be94ed835672a8`; this correction did not rebuild or requalify its runtime. That record does not establish current download availability. New runtime or architecture changes require a new accepted Daily revision; automatic Release deletion is not part of ordinary publication.

The manifest's catalog commit identifies the frozen Skill snapshot selected for that Release. Later documentation-only changes on `main` may clarify availability or upgrade guidance without moving the delivery tag or rewriting `delivery.catalog_sha`. They do not publish a Release or change its installer.

## Permanent ownership

| Location | Responsibility |
|---|---|
| This repository's `skills/` | All maintained AI Vision Skills, bundled references/scripts, and catalog checks |
| Product repository | Platform/CLI/plugin source, canonical `deploy/` assets, image builds, and product qualification |
| `ghcr.io/ob-labs/ai-vision-skills/` | Five private application packages, pinned by actual manifest digests; no database packages |
| Official upstream `oceanbase/oceanbase-ce` and `oceanbase/seekdb` | Fixed database digest dependencies selected by the current manifest and matching vars; not republished with each Daily |

An installed Skill must contain its execution prerequisites. Product source links are maintainer provenance, not a requirement to clone or read private source before using a Skill. Plugin binaries and onboarding scripts continue to be served by the deployed platform; this catalog is not a second plugin distribution endpoint.

## All-in-One preview delivery

The [All-in-One Preview](../skills/aivision-deploy/reference/all-in-one.md) is
for quick trials and personal use. An immutable
`all-in-one-preview-v<version>` prerelease carries `install-all-in-one.py`,
`SHA256SUMS`, and the complete asset set for each architecture qualified for
that release. Linux x86-64 uses `all-in-one-manifest.json`,
`aiv-all-in-one-linux-amd64.tar.gz`, and the matching `aiv-linux-x64.tar.gz`
CLI. Linux ARM64 uses
`all-in-one-manifest-arm64.json`, `aiv-all-in-one-linux-arm64.tar.gz`, and the
matching `aiv-linux-arm64.tar.gz` CLI. Both manifest formats bind the platform
and image archive to the exact image ID and record the base Daily. Bundled
`agent_cli` metadata binds the archive length, archive and executable SHA-256,
and CLI version. The installed Skill
discovers this profile separately from the distributed base and CLI channels.
The preview uses Release assets; the distributed GHCR packages, `:daily`
tags, and database vars continue to follow the base-delivery contract below.

Before publication, verify the intended assets through a fresh install on
each intended native Linux architecture. Check Agent onboarding, Trace
readback, rule diagnosis, and same-version recreation with the named volume.
Read back the private Release metadata and assets after publication.

## Transitional binary delivery

For each restricted Daily delivery:

1. Freeze one product version, qualified CLI archive, image digests, and deployment variables from the qualified product build. Product/CLI source and canonical deployment assets stay in the product repository; do not copy application source here.
2. Use an immutable `delivery-v<product-version>` prerelease tag for the base. Publish checksums, the manifest, matching database vars and the archives for the selected platforms. Mac preview metadata must name its exact base and asset tag and bind its own assets and backend digest. For an integrated preview, both tags equal the base tag. Keep the published base file bytes intact. Keep source bundles, build plans, logs and internal reports in the product team's private build storage.
3. Render `ob-labs/ai-vision-skills` into `install-aiv.sh` before generating its checksum. Private asset downloads, including installer downloads, use the operator's authenticated GitHub CLI. An anonymous curl URL does not acquire private access by changing its repository.
4. Retain actual product version, source SHA, component build identities, source URLs, and build or workflow provenance. Check that `aiv --version` reports the product version recorded by the selected Release.
5. Publish the five application packages under `ghcr.io/ob-labs/ai-vision-skills/`: `aivision-be`, `aivision-fe`, `agentlens`, `antcollector-gw`, and `signoz-ob`. Use each full product-version tag and advance `:daily` to the latest accepted base Daily. Platform-specific preview backends use separate tags. Use fixed official upstream digest references for OceanBase CE and seekdb. Deploy using the exact manifest digests. Native deployment vars must include `NATIVE_PYTHON_RUNTIME: "true"`.
6. Complete the selected delivery's declared validation matrix before promotion. Keep service, CLI, client and database execution platforms explicit. Read the selected Release notes for its actual native, emulated or mixed-platform coverage. An x86 application case using native ARM64 CE is a mixed-platform case, not a full AMD64 database-startup pass; do not carry a historical delivery's limits or results forward as current qualification. Do not claim pending cases passed; publish the actual completed scope in the Release notes. For the requested offline/manual security scanning bundles, export the five service images per architecture and exclude database images; retain exact configs, layer checksums, image digests and platforms. Database dependencies stay upstream and separate. Add no scanner CI, mandatory reports, or extra repository/package access grants.
7. Verify the published assets and automatic CLI selection for the published targets. Complete actual telemetry ingestion and readback before claiming that scope is ready. State the application and database platforms, deployment mode and any real-model validation explicitly.

| Release asset | Purpose |
| --- | --- |
| `aiv-linux-<arch>.tar.gz` | CLI archive for a selected Linux architecture |
| `aiv-darwin-<arch>.tar.gz` | CLI archive for a selected Mac architecture |
| `aiv-windows-x64.zip` | Windows x64 CLI when the base delivery includes the client preview |
| `install-aiv.sh` | Base installer configured for authenticated private delivery |
| `install-aiv-macos.sh` | Apple Silicon installer in a base Release with integrated Mac assets |
| `release-manifest.json` | Product/build provenance, exact image references, and platform evidence |
| `release-images.vars.yaml` | Matching OceanBase CE deployment variables |
| `release-seekdb.vars.yaml` | Matching seekdb deployment variables |
| `macos-codex-preview.json` | Exact base relationship, Mac client artifact identities and backend digest |
| `release-macos-oceanbase.vars.yaml`, `release-macos-seekdb.vars.yaml` | Integrated Mac backend vars for the selected datastore |
| `SHA256SUMS.macos` | Checksums for the integrated macOS assets |
| `SHA256SUMS` | Base checksums, or profile checksums in a separately published historical Mac companion |

The installed Skill selects the archive for the current trial platform. Older
assets can remain available for already pinned installations. Validate the
deployment daemon's platform independently and confirm that the service and
upstream database references include it. A deliberately validated mixed-platform
trial records the database host separately.

Existing deployments or saved vars that still reference the retired private `oceanbase-ce` or `seekdb` packages must use the current matching `release-images.vars.yaml` or `release-seekdb.vars.yaml` before deployment. Retain the deployment's existing credentials, datastore selection and data identity when updating those references.

List the published prereleases in this repository, select a compatible version and then use its exact tag for the download. Filter on the client's package and any required server platform before comparing product versions. Check the Mac preview manifest's base relationship for both the integrated and historical companion layouts. Use the profile-specific checksums from the selected asset tag. Windows client preview manifests can be included in the base Release. If discovery finds only an older compatible platform release, state the selected version and the platform gap before proceeding. Preserve an existing CLI on a failed download or compatibility check. Stable product Releases use their product channel.

## Authentication boundaries

Skill Git access, private Release downloads, container pulls, AI Vision account sessions, query SpaceKeys, and model-provider keys are separate credentials. Authenticate only the operation requiring access. A query against an existing platform does not need a new deployment or collection plugin.

Do not add a shared GitHub token to Skill files. Do not grant source access merely to enable image pulls. Preserve existing builder access when package permissions are eventually reviewed, and test recipient access independently.

## After product open source

First verify public product Releases and intended image access. Switch Skill installation references for `aiv` and upgrades to those product Releases. Keep the Skill source `ob-labs/ai-vision-skills` and all Skill names stable.

Stop product binary publication here and revoke temporary cross-repository publishing credentials. Before making this repository public, review historical restricted Release assets and private package workflow access. Only historical assets approved for publication may remain publicly accessible; move or retire others through the agreed retention process.

The repository then maintains Skills and their supporting resources only. Public skills.sh discovery is checked after actual public installation; private repository creation is not directory indexing or a security certification.
