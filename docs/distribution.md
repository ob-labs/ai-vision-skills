# Distribution

| Location | Responsibility |
| --- | --- |
| [AI Vision Skills](https://github.com/ob-labs/ai-vision-skills) | Skill discovery and installation from Git, bundled references and scripts, and catalog CI. |
| [AI Vision Releases](https://github.com/antgroup/ai-vision/releases) | Product release notes, CLI archives, manifests, checksums, and matching deployment variables. |
| `ghcr.io/antgroup/ai-vision/` | The product's frontend, backend, ingest gateway, diagnosis, and data backend images. |

The Git repository is the source for `npx skills`. Keep each Skill independently
installable and its discovery path stable. Product implementation, packaging,
validation, and publication belong in the product repository. A deployed
platform serves its own enrollment and Agent integration resources.

Resolve a compatible published product version before installing or upgrading.
Use the manifest, checksums, archives, and deployment variables of the same
versioned Release. Check the CLI client platform, Docker host, and Agent
execution machine separately. Record what the product Release actually
qualifies. Reuse an installed compatible CLI when possible and report missing
assets clearly.

Git access, Release access, image pulls, AI Vision account login, query
SpaceKeys, and model-provider credentials use their own authorization. Confirm
the relevant access separately.

## Historical deliveries

The restricted-trial Daily and All-in-One Releases in this catalog were
retired. The existing Git tags identify historical snapshots. Historical
manifests, image digests, build identities, and qualification records describe
their original scope. Active installation paths use the product distribution
endpoints above.
