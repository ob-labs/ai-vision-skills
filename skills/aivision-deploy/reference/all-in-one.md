# AI Vision All-in-One Preview

Choose All-in-One for a quick trial or personal use. One container starts AI
Vision with embedded seekdb, and one named Docker volume holds its data. Use
the [distributed deployment](../SKILL.md#choose-a-deployment-mode) for a shared
installation, an external database, or an existing distributed stack.

## Install and open AI Vision

Use a **Linux x86-64 or ARM64** machine or VM with Python 3.8+ and access to a
local Docker daemon of the same architecture. The installer selects assets
for the native Linux architecture. Online installation requires a published
preview with a complete asset set for that architecture. A verified local
preview bundle also supports offline installation.
The preview uses 2 CPU and a 6 GiB container memory limit.
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

For a local or offline install, transfer the complete verified candidate or the
matching [private Release](https://github.com/ob-labs/ai-vision-skills/releases)
assets into a single directory. Both architectures need `install-all-in-one.py`
and `SHA256SUMS`.

| Docker host | Additional assets |
|---|---|
| Linux x86-64 | `all-in-one-manifest.json`, `aiv-all-in-one-linux-amd64.tar.gz`, `aiv-linux-x64.tar.gz` when included |
| Linux ARM64 | `all-in-one-manifest-arm64.json`, `aiv-all-in-one-linux-arm64.tar.gz`, `aiv-linux-arm64.tar.gz` |

Verify the files before running the installer. This path works without `gh` on
the Docker host. If an authorized Release contains both architectures and you
only download one set, use `sha256sum --check --ignore-missing SHA256SUMS`.
Confirm every file in your set is present and reports `OK`.

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

Run `getconf GNU_LIBC_VERSION` on the Linux Agent machine and require glibc
2.35 or later. Match the CLI to the **Agent machine's** CPU. Check the
qualification of the selected preview for its matching native Agent payload.
The Docker host, browser and Agent can be different machines. For a different
client OS, check the published backend and client combination in the
[distributed guide](prerequisites.md#select-the-agent-client-backend-configuration).

1. Install or reuse the matching Linux `aiv` on the Agent machine. Copy the
   All-in-One installer there, or use the copy in the installed `aivision-deploy`
   Skill. Use the exact `preview_tag` that installed the platform. The
   installer selects the matching CLI for the Agent machine, verifies its
   SHA-256, architecture and version, and installs it to `~/.local/bin/aiv`.
   It uses the preview's own CLI archive when included. For an older x86-64
   preview that lists a base release, the online installer finds that exact
   base release's verified x86-64 CLI.

   ```sh
   : "${AIV_SKILL_DIR:?Set this to the installed aivision-deploy directory}"
   : "${preview_tag:?Set this to the exact All-in-One preview tag}"
   installer="$AIV_SKILL_DIR/scripts/install-all-in-one.py"
   python3 "$installer" --tag "$preview_tag" --resolve-cli &&
     python3 "$installer" --tag "$preview_tag" --install-cli
   ```

   For an offline Agent machine, transfer the installer, `SHA256SUMS`, the
   preview manifest for that architecture and its matching CLI archive. From
   that directory, use `python3 ./install-all-in-one.py --from-dir "$PWD"
   --install-cli`. The CLI-only install requires no Docker. An older x86-64
   preview whose CLI came from a separate base release needs a verified copy
   of that base CLI brought to the offline machine. Complete
   [PATH setup](prerequisites.md#finish-durable-path-setup), and verify
   `command -v aiv`, `aiv --version` and `aiv connect --help`. The platform
   provides the Agent collection payload during onboarding.
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

Use the same-version procedure above for the preview. For example, recreate
an existing deployment using its recorded original tag even after another
preview has been published. Use a new `--name` and unused ports to try a
different tag alongside it. Cross-version preview upgrades and moving
existing distributed data into this volume need separate validation.
