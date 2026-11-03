# Distribution Ownership

## Current installation ownership

This repository remains private and owns the four maintained Skills and their
bundled resources. Default CLI/deployment download instructions now target
`ob-labs/ai-vision-ob`; stable and Daily/preview selections require an exact
published `v<product-version>` Release. A source change or instruction is not a
publication receipt. No particular future `0.1.0` Daily date is assumed to exist.
The standard source-compatible CLI is the default. A native variant is optional
only when explicitly selected and actually published with its own evidence.

All four independently installed Skills carry the same executable recipe.
Public metadata/assets use anonymous `curl`; `jq` validates JSON. Authenticated
`gh` remains fallback for the currently private product repository. The recipe
requires an explicit immutable tag, verifies the exact Release and manifest
repository/version/tag/channel plus checksums, and preserves an installed CLI
on failure. It does not follow mutable `daily`, `latest` or Dev selectors.

The selected Release's actual manifest and vars define image digests, runtime
settings and supported platforms. Do not copy native-profile assumptions into
standard deployment. Product publication owns four application images;
`ob-labs/signoz` owns SigNoz publication and the product pins its digest.
Database dependencies retain fixed official upstream digests. Publication,
image access, runtime qualification and repository visibility remain separate.

## Historical restricted delivery

The former private delivery channel used `delivery-v<product-version>`
prereleases in this repository. The last prepared target was
`delivery-v0.1.0-daily.20261101`, with Linux x64/ARM64 archives and seven assets.
That record does not establish a published or currently downloadable Release.
Only an explicit historical request selects this repository and one of the
three retained reader tags; its authenticated access, exact asset and platform
guards remain. New product downloads do not use this publisher.

Ordinary later publication preserves earlier accepted Releases, assets and tags. Retirement requires separate maintainer authorization; never silently substitute an older download for the selected version. Preserve private historical artifacts, checksums, catalog/build identities and qualification records for audit. Historical readers and tests may still recognize the six-asset, x64-only `.20261028.2` format; that compatibility does not promise a GitHub Release or downloadable assets. Published assets remain immutable while retained; retirement does not authorize moving an old tag or changing its bytes.

For those historical deliveries, the selected backend must serve the native Agent's own Linux x64 or ARM64 installer target, with glibc 2.35 or newer. Debian Bookworm/glibc 2.36 is the recorded client baseline. Check the Agent machine separately from the deployment machine: the static Go CLI and containerized services can run on a Docker host whose glibc is older. Such a host does not qualify the native installer; glibc 2.32 cannot launch this bundle. Keep the client ABI and actual test environment explicit in delivery evidence, and use a compatible Agent machine rather than a source-installer fallback.

Existing organization and repository permissions apply; this delivery adds no user or team access grants. Access by a recipient without product-source permissions must be checked independently. A maintainer's successful clone or package push does not prove recipient access.

The historical corrected CLI was compiled with `native_distribution`: source-mode Python resources are excluded before linking and the actual executable is checked. Default source builds remain product-owned and are not restricted-trial artifacts. The earlier `delivery-v0.0.1-daily.20261028` Release was withdrawn because its CLI contains legacy deployment Python and fails this boundary; its downloads are no longer available. Original local artifacts and qualification evidence remain retained.

On 2026-10-29, an explicit maintainer-authorized, one-time database-source correction updated the existing `.2` manifest, both deployment vars and checksums. The CLI and installer bytes, five application images and product build identity did not change. The historical `.2` delivery recorded catalog commit `9ac54119a9197b94d9efb7b1b0be94ed835672a8`; this correction did not rebuild or requalify its runtime. That record does not establish current download availability. New runtime or architecture changes require a new accepted Daily revision; automatic Release deletion is not part of ordinary publication.

The manifest's catalog commit identifies the frozen Skill snapshot selected for that Release. Later documentation-only changes on `main` may clarify availability or upgrade guidance without moving the delivery tag or rewriting `delivery.catalog_sha`. They do not publish a Release or change its installer.

## Permanent ownership

| Location | Responsibility |
|---|---|
| This repository's `skills/` | All maintained AI Vision Skills, bundled references/scripts, and catalog checks |
| Product repository | Platform/CLI/plugin source, canonical `deploy/` assets, image builds, and product qualification |
| Product Release/package channel | Product-owned four application images and a pinned upstream SigNoz digest, matching manifest and vars |
| Historical `ghcr.io/ob-labs/ai-vision-skills/` | Retained private trial packages and frozen digests; no new product publication or database packages |
| Official upstream `oceanbase/oceanbase-ce` and `oceanbase/seekdb` | Fixed database digest dependencies selected by the current manifest and matching vars; not republished with each Daily |

An installed Skill must contain its execution prerequisites. Product source links are maintainer provenance, not a requirement to clone or read private source before using a Skill. Plugin binaries and onboarding scripts continue to be served by the deployed platform; this catalog is not a second plugin distribution endpoint.

## Historical transitional binary contract

The retained restricted delivery contract below describes historical artifacts;
it is not an instruction to publish another product build from this catalog:


1. Freeze one product version, qualified CLI archive, image digests, and deployment variables from the qualified product build. Product/CLI source and canonical deployment assets stay in the product repository; do not copy application source here.
2. Use an immutable `delivery-v<product-version>` prerelease tag. The `0.1.0-daily.20261101` target allows exactly the seven assets below. The older `.20261028.2` six-asset contract is retained for historical-reader tests, not as a supported download target. No source bundle, `release-plan.json`, `plugin-dist.tar.gz`, build plan, log, or internal report belongs in that asset set.
3. Render `ob-labs/ai-vision-skills` into `install-aiv.sh` before generating its checksum. Private asset downloads, including installer downloads, use the operator's authenticated GitHub CLI. An anonymous curl URL does not acquire private access by changing its repository.
4. Retain actual product version, source SHA, component build identities, source URLs, and build/workflow provenance. `aiv --version` was `0.1.0-daily.20261101` for that historical target, never `delivery-v0.1.0-daily.20261101`. Distribution here does not imply that the product was built here.
5. Publish only the five application packages under `ghcr.io/ob-labs/ai-vision-skills/`: `aivision-be`, `aivision-fe`, `agentlens`, `antcollector-gw`, and `signoz-ob`. Use each full product-version tag, such as `:0.1.0-daily.20261101`, and advance `:daily` only to the latest accepted Daily. Do not publish short `:daily.<date>` tags. Use fixed official upstream digest references for OceanBase CE and seekdb from the current manifest and matching vars; do not create database packages or republish databases with each Daily. Deploy using the manifest's exact digests; never derive image references from the Release tag or deploy using mutable `:daily`. Native deployment vars must include `NATIVE_PYTHON_RUNTIME: "true"`.
6. Complete the selected delivery's declared validation matrix before promotion. Keep service, CLI, client and database execution platforms explicit. Read the selected Release notes for its actual native, emulated or mixed-platform coverage. An x86 application case using native ARM64 CE is a mixed-platform case, not a full AMD64 database-startup pass; do not carry a historical delivery's limits or results forward as current qualification. Do not claim pending cases passed; publish the actual completed scope in the Release notes. For the requested offline/manual security scanning bundles, export the five service images per architecture and exclude database images; retain exact configs, layer checksums, image digests and platforms. Database dependencies stay upstream and separate. Add no scanner CI, mandatory reports, or extra repository/package access grants.
7. Verify the published assets and automatic recipient CLI selection on both selected Linux architectures. Complete actual telemetry ingestion/readback for the declared application/datastore matrix before claiming that scope is ready. State any mixed database platform explicitly; keep Docker, Kubernetes and real-model evidence distinct.

| Restricted dual-platform delivery asset | Purpose |
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
platform; a missing native child is a publication gap, not an implicit emulation
or source-build fallback. A deliberately validated mixed-platform trial records
the database host separately. The historical `.20261028.2` format is Linux x64
only and does not establish an available download.

Existing deployments or saved vars that still reference the retired private `oceanbase-ce` or `seekdb` packages must use the current matching `release-images.vars.yaml` or `release-seekdb.vars.yaml` before deployment. Retain the deployment's existing credentials, datastore selection and data identity when updating those references.

Resolve restricted Daily downloads against the fixed tag in this repository and confirm that it is a published prerelease with the required assets. Do not follow the old product `daily` pointer, use `releases/latest` for a prerelease, or substitute mutable Dev images when the requested version is missing. A missing compatible Release or platform stops installation and preserves the installed binary. Stable product Releases may retain their original channel; their existence does not establish today's restricted Daily.

## Authentication boundaries

Skill Git access, private Release downloads, container pulls, AI Vision account sessions, query SpaceKeys, and model-provider keys are separate credentials. Authenticate only the operation requiring access. A query against an existing platform does not need a new deployment or collection plugin.

Do not add a shared GitHub token to Skill files. Do not grant source access merely to enable image pulls. Preserve existing builder access when package permissions are eventually reviewed, and test recipient access independently.

## Publication and eventual visibility

Installation references are prepared for product Releases; this change publishes
no artifacts and changes no repository or package visibility. First verify the
selected product Release and intended recipient image access before claiming
that an installable public Daily exists. Keep the Skill source
`ob-labs/ai-vision-skills` and all Skill names stable.

Stop product binary publication here and revoke temporary cross-repository publishing credentials. Before making this repository public, review historical restricted Release assets and private package workflow access. Historical artifacts remain immutable and retained. Any future publication, movement or retirement requires its own explicit decision; this installer cutover authorizes none of them.

The repository then maintains Skills and their supporting resources only. Public skills.sh discovery is checked after actual public installation; private repository creation is not directory indexing or a security certification.
