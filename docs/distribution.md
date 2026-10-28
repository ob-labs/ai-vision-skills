# Distribution Ownership

## Current state

The repository starts as a private, canonical Skill catalog. The initial migration contains four complete Skills and catalog validation. It does not publish `aiv` binaries, create trial Releases, move application images, grant additional users or teams access, or perform runtime acceptance.

Existing organization and repository permissions apply. The user requested no additional access grants for this setup. Access by a new recipient without product-source permissions remains part of later delivery acceptance, not evidence established by a maintainer's successful clone.

## Permanent ownership

| Location | Responsibility |
|---|---|
| This repository's `skills/` | All maintained AI Vision Skills, bundled references/scripts, and catalog checks |
| Product repository | Platform/CLI/plugin source, canonical `deploy/` assets, image builds, and product qualification |
| Existing container registry | Five application service images and selected database dependencies with their actual digests |

An installed Skill must contain its execution prerequisites. Product source links are maintainer provenance, not a requirement to clone or read private source before using a Skill. Plugin binaries and onboarding scripts continue to be served by the deployed platform; this catalog is not a second plugin distribution endpoint.

## Transitional binary delivery

When the separately planned binary delivery work is executed:

1. Freeze one product version and its qualified CLI archives, image digests, and deployment variables in the product build workflow.
2. Publish an explicit allowlist of product artifacts to a private Release here, without rebuilding them or changing their product identity.
3. Use an immutable `delivery-v<product-version>` prerelease tag. Obtain the four CLI archives, `release-manifest.json`, selected CE/seekdb vars, and `SHA256SUMS` from the same tag. A catalog tag never defines `aiv --version`.
4. Render the delivery repository into `install-aiv.sh` before generating its checksum. Use an authenticated Release download route for private assets; the current curl-based installer does not gain private authentication simply by changing its repository argument.
5. Keep source SHA, component build identities, workflow provenance, and OCI references truthful. Downloads from this repository do not imply the product was built here.
6. Provide the exact version, archive checksums, image digests, and platforms to the existing offline/manual security scanning process. Internal reports are not Release assets unless explicitly requested.
7. Verify recipient installation and actual telemetry ingestion/readback before claiming the combination is ready.

Do not guess a trial tag, use `releases/latest` to resolve a trial prerelease, or substitute mutable Dev images when a requested version is missing. Until this channel exists, use an existing compatible CLI or an available authorized product Release and state the missing delivery capability clearly.

## Authentication boundaries

Skill Git access, private Release downloads, container pulls, AI Vision account sessions, query SpaceKeys, and model-provider keys are separate credentials. Authenticate only the operation requiring access. A query against an existing platform does not need a new deployment or collection plugin.

Do not add a shared GitHub token to Skill files. Do not grant source access merely to enable image pulls. Preserve existing builder access when package permissions are eventually reviewed, and test recipient access independently.

## After product open source

First verify public product Releases and intended image access. Switch Skill installation references for `aiv` and upgrades to those product Releases. Keep the Skill source `ob-labs/ai-vision-skills` and all Skill names stable.

Stop product binary publication here and revoke temporary cross-repository publishing credentials. Before making this repository public, review historical restricted Release assets and private package workflow access. Only historical assets approved for publication may remain publicly accessible; move or retire others through the agreed retention process.

The repository then maintains Skills and their supporting resources only. Public skills.sh discovery is checked after actual public installation; private repository creation is not directory indexing or a security certification.
