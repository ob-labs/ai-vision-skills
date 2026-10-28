# Distribution Ownership

## Current state

This private repository owns the four maintained Skills and the restricted-trial Daily delivery channel. A delivery is available only after its exact `delivery-v<product-version>` GitHub prerelease is published with the required assets. Instructions, source changes, or a successful registry probe do not establish product publication or runtime acceptance.

The current customer delivery target is product version `0.0.1-daily.20261028.2`, GitHub tag `delivery-v0.0.1-daily.20261028.2`. It supports the Linux x64 CLI and `linux/amd64` images only. Finish publication and full validation for all AMD64 artifacts before processing ARM. Adding ARM support requires a new Daily revision, such as `.3`, without changing the published x86 archives, images, or checksums of the earlier delivery.

The native Agent onboarding client requires Linux x64 with glibc 2.35 or newer. Debian Bookworm is the qualified client runtime. Check the Agent machine separately from the deployment machine: the static Go CLI and containerized services can run on a Docker host whose glibc is older. Such a host does not qualify the native installer; glibc 2.32 cannot launch this bundle. Keep the client ABI and actual test environment explicit in delivery evidence, and use a compatible Agent machine rather than a source-installer fallback.

Existing organization and repository permissions apply; this delivery adds no user or team access grants. Access by a recipient without product-source permissions must be checked independently. A maintainer's successful clone or package push does not prove recipient access.

The corrected CLI is compiled with `native_distribution`: source-mode Python resources are excluded before linking and the actual executable is checked. Default source builds remain product-owned and are not restricted-trial artifacts. The earlier `delivery-v0.0.1-daily.20261028` CLI contains legacy deployment Python and needs replacement; its published bytes and image references are preserved.

## Permanent ownership

| Location | Responsibility |
|---|---|
| This repository's `skills/` | All maintained AI Vision Skills, bundled references/scripts, and catalog checks |
| Product repository | Platform/CLI/plugin source, canonical `deploy/` assets, image builds, and product qualification |
| `ghcr.io/ob-labs/ai-vision-skills/` | Restricted-trial application images and optional database mirrors, pinned by actual manifest digests |

An installed Skill must contain its execution prerequisites. Product source links are maintainer provenance, not a requirement to clone or read private source before using a Skill. Plugin binaries and onboarding scripts continue to be served by the deployed platform; this catalog is not a second plugin distribution endpoint.

## Transitional binary delivery

For each restricted Daily delivery:

1. Freeze one product version, qualified CLI archive, image digests, and deployment variables from the product build workflow. Product/CLI source and canonical deployment assets stay in the product repository; do not copy application source here.
2. Use an immutable `delivery-v<product-version>` prerelease tag. This release allows exactly the six assets below. No source bundle, `release-plan.json`, `plugin-dist.tar.gz`, build plan, log, or internal report belongs in that asset set.
3. Render `ob-labs/ai-vision-skills` into `install-aiv.sh` before generating its checksum. Private asset downloads, including installer downloads, use the operator's authenticated GitHub CLI. An anonymous curl URL does not acquire private access by changing its repository.
4. Retain actual product version, source SHA, component build identities, source URLs, and build/workflow provenance. `aiv --version` is `0.0.1-daily.20261028.2` for this target, never `delivery-v0.0.1-daily.20261028.2`. Distribution here does not imply that the product was built here.
5. Publish the five application packages under `ghcr.io/ob-labs/ai-vision-skills/`: `aivision-be`, `aivision-fe`, `agentlens`, `antcollector-gw`, and `signoz-ob`. Optional database mirrors are `oceanbase-ce` and `seekdb` in the same namespace. Use the manifest's exact references and digests; never derive an image reference from the Release tag. Native deployment vars must include `NATIVE_PYTHON_RUNTIME: "true"`.
6. Complete all AMD64 publication and validation before processing ARM. Provide the exact version, archive checksums, image digests, and actual platforms to the existing offline/manual security scanning process. Add no scanner CI, mandatory reports, or extra repository/package access grants.
7. Verify the published assets, recipient CLI installation, both supported Docker datastore paths, and actual telemetry ingestion/readback before claiming the combination is ready. Keep Docker, Kubernetes, ARM, and real-model evidence distinct.

| Current delivery asset | Purpose |
| --- | --- |
| `aiv-linux-x64.tar.gz` | Linux x64 CLI, with the actual product version |
| `install-aiv.sh` | Installer configured for authenticated private delivery |
| `release-manifest.json` | Product/build provenance, exact image references, and platform evidence |
| `release-images.vars.yaml` | Matching OceanBase CE deployment variables |
| `release-seekdb.vars.yaml` | Matching seekdb deployment variables |
| `SHA256SUMS` | One checksum for each of the other five assets |

Resolve restricted Daily downloads against the fixed tag in this repository and confirm that it is a published prerelease with the required assets. Do not follow the old product `daily` pointer, use `releases/latest` for a prerelease, or substitute mutable Dev images when the requested version is missing. A missing compatible Release or platform stops installation and preserves the installed binary. Stable product Releases may retain their original channel; their existence does not establish today's restricted Daily.

## Authentication boundaries

Skill Git access, private Release downloads, container pulls, AI Vision account sessions, query SpaceKeys, and model-provider keys are separate credentials. Authenticate only the operation requiring access. A query against an existing platform does not need a new deployment or collection plugin.

Do not add a shared GitHub token to Skill files. Do not grant source access merely to enable image pulls. Preserve existing builder access when package permissions are eventually reviewed, and test recipient access independently.

## After product open source

First verify public product Releases and intended image access. Switch Skill installation references for `aiv` and upgrades to those product Releases. Keep the Skill source `ob-labs/ai-vision-skills` and all Skill names stable.

Stop product binary publication here and revoke temporary cross-repository publishing credentials. Before making this repository public, review historical restricted Release assets and private package workflow access. Only historical assets approved for publication may remain publicly accessible; move or retire others through the agreed retention process.

The repository then maintains Skills and their supporting resources only. Public skills.sh discovery is checked after actual public installation; private repository creation is not directory indexing or a security certification.
