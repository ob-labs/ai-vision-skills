# AI Vision All-in-One Preview

Choose All-in-One for a quick trial or personal use. One container starts AI
Vision with embedded seekdb, and one named Docker volume holds its data. Use
the [distributed deployment](../SKILL.md#choose-a-deployment-mode) for a shared
installation, an external database, or an existing distributed stack.

## Install and open AI Vision

Use a **Linux x86-64** machine or VM with Python 3.8+ and access to a running
local Docker daemon. The preview uses 2 CPU and a 6 GiB container memory limit.
Allow 6 GiB for the container and disk space for the image and growing data
volume. Ports `5174` for Web and `4318` for OTLP/HTTP bind to loopback. Choose
unused ports if another service already uses either one.

From the installed Skill, set `AIV_SKILL_DIR` to the absolute path of its
`aivision-deploy` directory. For an online install, authenticate `gh` on
`github.com` with an account that can read the private `ob-labs/ai-vision-skills`
repository. The installer finds a published All-in-One preview, then verifies
the selected manifest and archive before loading the image. Show the tag before
installation and pin it for the operation. Without `--tag`, the installer uses
the most recently published compatible preview.

```sh
: "${AIV_SKILL_DIR:?Set this to the installed aivision-deploy directory}"
installer="$AIV_SKILL_DIR/scripts/install-all-in-one.py"
preview_tag=$(python3 "$installer" --resolve) &&
  printf 'Installing %s\n' "$preview_tag" &&
  python3 "$installer" --tag "$preview_tag"
```

Keep `preview_tag` for retries and recreation. For an explicit version, use
its exact published tag. The preview uses private Release assets and loads
the verified archive into Docker. It needs no container-registry login,
`aiv cast`, or separate database image. A missing compatible release or a
failed verification stops installation.

For an offline host, download `install-all-in-one.py`,
`all-in-one-manifest.json`, `aiv-all-in-one-linux-amd64.tar.gz`, and `SHA256SUMS`
from the same [private Release](https://github.com/ob-labs/ai-vision-skills/releases)
and transfer them to a single directory. Verify the files before running the
installer. This path uses the bundled archive and works without `gh` on the
Docker host.

```sh
cd /path/to/all-in-one-release-assets
sha256sum --check SHA256SUMS &&
  python3 ./install-all-in-one.py --from-dir "$PWD"
```

Use `--name`, `--web-port`, and `--otlp-port` for a separate trial. Record the
actual name, version, ports, and the corresponding `<name>-data` volume.
When the installer reports healthy, open `http://127.0.0.1:5174` or the
reported Web URL. Register or sign in through the Web UI.

If the browser or Agent runs outside the VM, run the following from that
client machine and keep the SSH connection open. Use the same port numbers as
the selected installation so the platform's generated URLs work from the client.

```sh
ssh -N -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:5174:127.0.0.1:5174 \
  -L 127.0.0.1:4318:127.0.0.1:4318 \
  user@linux-vm
```

## Connect an Agent and find its Trace

The verified preview path uses a Linux x86-64 Agent client with glibc 2.35 or
later. Run `getconf GNU_LIBC_VERSION` on the machine running the Agent. The
Docker host, browser and Agent can be different machines. For native Agent
onboarding on a different client OS, check the matching published backend
and client combination in the [distributed guide](prerequisites.md#select-the-agent-client-backend-configuration).

1. Install or reuse the matching Linux `aiv` on the Agent machine. The
   installer output and `all-in-one-manifest.json` identify its `base_release`.
   If `aiv` is missing or incompatible, set `base_release` to that exact tag
   and use the [bundled CLI installer](install-cli.md#discover-a-published-cli)
   with `gh` and `jq` on the connected Agent machine:

   ```sh
   : "${AIV_SKILL_DIR:?Set this to the installed aivision-deploy directory}"
   : "${base_release:?Set this to the matching CLI release tag printed by the installer}"
   AIV_CHANNEL=daily AIV_TAG="$base_release" sh "$AIV_SKILL_DIR/scripts/install-cli.sh" --install
   ```

   For an offline Agent machine, bring the matching verified Linux CLI from the
   base release. Confirm `command -v aiv`, `aiv --version` and
   `aiv connect --help` in the same terminal you will use for onboarding. The
   platform provides the Agent collection payload during onboarding.
2. Open **Agent Access** (`/access`), select your Space and Agent (for example,
   Codex), and generate the installation command. Run the complete command
   unchanged on the Agent machine. The single-use authorization expires after
   15 minutes. Keep it out of chat and logs. The Agent uses its own account
   and model configuration for real requests.
3. Restart the Agent. In Codex, review and trust the new hooks with `/hooks`,
   then run a small task. Open its Trace under the same Space and Agent and
   check the time and task content. Use a rule diagnosis on that Trace if
   diagnosis is part of the trial and read back the persisted result.

## Stop, restart or recreate

These commands use the default name. Substitute the actual installation name
for a custom trial.

```sh
docker inspect --format '{{.State.Health.Status}}' aiv-all-in-one
docker logs --tail 80 aiv-all-in-one
docker stop --time 120 aiv-all-in-one
docker start aiv-all-in-one
```

To recreate the container, retain the same image version, name, ports and
named volume. Stop it with `docker stop --time 120 aiv-all-in-one`, remove the
stopped container with `docker rm aiv-all-in-one`, then rerun the installer
with the same `--tag` (or the same `--from-dir`) and options. The installer
reattaches `aiv-all-in-one-data` at `/data` by default. This volume holds local
accounts, configuration, Traces and diagnosis records. Keep it when replacing
the container. Sign in again and read back a known Trace after recreation.

Use the same-version procedure above for the preview. Cross-version preview
upgrades and moving existing distributed data into this volume need separate
validation. Resolve a release on request, show its exact tag, and preserve
the current instance and data when evaluating another preview.
