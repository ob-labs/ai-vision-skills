# Distribution Ownership

## Current state

This private repository owns the four maintained Skills and the restricted-trial Daily delivery channel. A delivery is available only after its exact `delivery-v<product-version>` GitHub prerelease is published with the required assets. Instructions, source changes, or a successful registry probe do not establish product publication or runtime acceptance.

The previously accepted delivery is product version `0.0.1-daily.20261028.2`, GitHub tag `delivery-v0.0.1-daily.20261028.2`, with the Linux x64 CLI and `linux/amd64` images only. The prepared default is the new `delivery-v0.0.1-daily.20261029`: Linux x64 and ARM64 CLI archives, and multi-platform service indices declaring `linux/amd64` plus `linux/arm64`. **The new target remains planned until its exact prerelease, seven assets and qualification evidence are published and verified.** A missing or draft Release stops installation; a catalog change is not a release receipt. Preserve the older delivery's immutable archives and full-version image tags.

The selected backend must serve the native Agent's own Linux x64 or ARM64 installer target, with glibc 2.35 or newer. Debian Bookworm/glibc 2.36 is the recorded client baseline. Check the Agent machine separately from the deployment machine: the static Go CLI and containerized services can run on a Docker host whose glibc is older. Such a host does not qualify the native installer; glibc 2.32 cannot launch this bundle. Keep the client ABI and actual test environment explicit in delivery evidence, and use a compatible Agent machine rather than a source-installer fallback.

Existing organization and repository permissions apply; this delivery adds no user or team access grants. Access by a recipient without product-source permissions must be checked independently. A maintainer's successful clone or package push does not prove recipient access.

The corrected CLI is compiled with `native_distribution`: source-mode Python resources are excluded before linking and the actual executable is checked. Default source builds remain product-owned and are not restricted-trial artifacts. The earlier `delivery-v0.0.1-daily.20261028` Release was withdrawn because its CLI contains legacy deployment Python and fails this boundary; its downloads are no longer available. Original local artifacts and qualification evidence remain retained.

On 2026-10-29, an explicit maintainer-authorized, one-time database-source correction updated the existing `.2` manifest, both deployment vars and checksums. The CLI and installer bytes, five application images and product build identity did not change. The delivery tag still points to catalog commit `9ac54119a9197b94d9efb7b1b0be94ed835672a8`; this correction did not rebuild or requalify the runtime. Normal future delivery archives and full-version image tags remain immutable. New runtime or architecture changes require a new Daily revision.

## Permanent ownership

| Location | Responsibility |
|---|---|
| This repository's `skills/` | All maintained AI Vision Skills, bundled references/scripts, and catalog checks |
| Product repository | Platform/CLI/plugin source, canonical `deploy/` assets, image builds, and product qualification |
| `ghcr.io/ob-labs/ai-vision-skills/` | Five private application packages, pinned by actual manifest digests; no database packages |
| Official upstream `oceanbase/oceanbase-ce` and `oceanbase/seekdb` | Fixed database digest dependencies selected by the current manifest and matching vars; not republished with each Daily |

An installed Skill must contain its execution prerequisites. Product source links are maintainer provenance, not a requirement to clone or read private source before using a Skill. Plugin binaries and onboarding scripts continue to be served by the deployed platform; this catalog is not a second plugin distribution endpoint.

## Transitional binary delivery

For each restricted Daily delivery:

1. Freeze one product version, qualified CLI archive, image digests, and deployment variables from the product build workflow. Product/CLI source and canonical deployment assets stay in the product repository; do not copy application source here.
2. Use an immutable `delivery-v<product-version>` prerelease tag. The prepared dual-platform release allows exactly the seven assets below; the explicit older `.20261028.2` delivery retains its six-asset x64-only contract. No source bundle, `release-plan.json`, `plugin-dist.tar.gz`, build plan, log, or internal report belongs in that asset set.
3. Render `ob-labs/ai-vision-skills` into `install-aiv.sh` before generating its checksum. Private asset downloads, including installer downloads, use the operator's authenticated GitHub CLI. An anonymous curl URL does not acquire private access by changing its repository.
4. Retain actual product version, source SHA, component build identities, source URLs, and build/workflow provenance. `aiv --version` is `0.0.1-daily.20261029` for the prepared default, never `delivery-v0.0.1-daily.20261029`. Distribution here does not imply that the product was built here.
5. Publish only the five application packages under `ghcr.io/ob-labs/ai-vision-skills/`: `aivision-be`, `aivision-fe`, `agentlens`, `antcollector-gw`, and `signoz-ob`. Use each full product-version tag, such as `:0.0.1-daily.20261029`, and advance `:daily` only to the latest accepted Daily. Do not publish short `:daily.<date>` tags. Use fixed official upstream digest references for OceanBase CE and seekdb from the current manifest and matching vars; do not create database packages or republish databases with each Daily. Deploy using the manifest's exact digests; never derive image references from the Release tag or deploy using mutable `:daily`. Native deployment vars must include `NATIVE_PYTHON_RUNTIME: "true"`.
6. Qualify every selected architecture/datastore combination before promoting the combined index. Keep native and emulated results distinct. For the requested offline/manual security scanning bundles, export the five service images per architecture and exclude database images; retain exact configs, layer checksums, image digests and platforms. Database dependencies stay upstream and separate. Add no scanner CI, mandatory reports, or extra repository/package access grants.
7. Verify the published assets, automatic recipient CLI selection on both selected Linux architectures, both supported Docker datastore paths, and actual telemetry ingestion/readback before claiming the combination is ready. Keep Docker, Kubernetes, ARM, and real-model evidence distinct.

| Prepared dual-platform delivery asset | Purpose |
| --- | --- |
| `aiv-linux-x64.tar.gz` | Linux x64 CLI, with the actual product version |
| `aiv-linux-arm64.tar.gz` | Linux ARM64 CLI, with the same product version |
| `install-aiv.sh` | Installer configured for authenticated private delivery |
| `release-manifest.json` | Product/build provenance, exact image references, and platform evidence |
| `release-images.vars.yaml` | Matching OceanBase CE deployment variables |
| `release-seekdb.vars.yaml` | Matching seekdb deployment variables |
| `SHA256SUMS` | One checksum for each of the other six assets |

The same installed Skill command selects `aiv-linux-x64.tar.gz` for `x86_64`/`amd64`
and `aiv-linux-arm64.tar.gz` for `aarch64`/`arm64`. It does not infer service
platforms from the CLI machine. The deployment daemon resolves the manifest's
multi-platform image index to its own native child. Confirm each service index
and the separately pinned upstream database index contain the actual daemon
platform; a missing native child is a publication gap, not an emulation or
source-build fallback. An explicit `.20261028.2` selection stays Linux x64 only.

Existing deployments or saved vars that still reference the retired private `oceanbase-ce` or `seekdb` packages must use the current matching `release-images.vars.yaml` or `release-seekdb.vars.yaml` before deployment. Retain the deployment's existing credentials, datastore selection and data identity when updating those references.

Resolve restricted Daily downloads against the fixed tag in this repository and confirm that it is a published prerelease with the required assets. Do not follow the old product `daily` pointer, use `releases/latest` for a prerelease, or substitute mutable Dev images when the requested version is missing. A missing compatible Release or platform stops installation and preserves the installed binary. Stable product Releases may retain their original channel; their existence does not establish today's restricted Daily.

## Authentication boundaries

Skill Git access, private Release downloads, container pulls, AI Vision account sessions, query SpaceKeys, and model-provider keys are separate credentials. Authenticate only the operation requiring access. A query against an existing platform does not need a new deployment or collection plugin.

Do not add a shared GitHub token to Skill files. Do not grant source access merely to enable image pulls. Preserve existing builder access when package permissions are eventually reviewed, and test recipient access independently.

## After product open source

First verify public product Releases and intended image access. Switch Skill installation references for `aiv` and upgrades to those product Releases. Keep the Skill source `ob-labs/ai-vision-skills` and all Skill names stable.

Stop product binary publication here and revoke temporary cross-repository publishing credentials. Before making this repository public, review historical restricted Release assets and private package workflow access. Only historical assets approved for publication may remain publicly accessible; move or retire others through the agreed retention process.

The repository then maintains Skills and their supporting resources only. Public skills.sh discovery is checked after actual public installation; private repository creation is not directory indexing or a security certification.
