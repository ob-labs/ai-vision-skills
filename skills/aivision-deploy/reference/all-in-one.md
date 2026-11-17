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

### Run the installer directly

Authenticate `gh` on `github.com` with an account that can read the private
`ob-labs/ai-vision-skills` repository. From an empty directory, set `preview_tag`
to the exact tag from the [All-in-One preview Release](https://github.com/ob-labs/ai-vision-skills/releases).
Download that release's installer and checksum, then run it. Check that the
selected release offers the format and sample features you want to use.

```sh
: "${preview_tag:?Set this to the All-in-One preview tag}"
gh release download "$preview_tag" --repo ob-labs/ai-vision-skills \
  --pattern install-all-in-one.py --pattern SHA256SUMS &&
  (grep -E '^[0-9a-f]{64}  install-all-in-one\.py$' SHA256SUMS | sha256sum --check) &&
  python3 ./install-all-in-one.py --tag "$preview_tag"
```

### Install with a coding Agent

From the installed `aivision-deploy` Skill, set `AIV_SKILL_DIR` to the absolute
path of that directory. Use the same `gh` access. Resolve and display the tag
before installing. Without `--tag`, the installer uses the most recently
published compatible preview.

```sh
: "${AIV_SKILL_DIR:?Set this to the installed aivision-deploy directory}"
installer="$AIV_SKILL_DIR/scripts/install-all-in-one.py"
preview_tag=$(python3 "$installer" --resolve) &&
  printf 'Installing %s\n' "$preview_tag" &&
  python3 "$installer" --tag "$preview_tag"
```

Keep `preview_tag` for retries and recreation. The installer checks the Docker
daemon, instance name and local ports before downloading. It verifies the
selected archive and loads it into Docker. This installation uses Release
assets and embedded seekdb.

On Docker Server 23 or later, the installer prefers a verified `.tar.zst`
image archive when the selected preview offers it. Older servers and older
previews can use `.tar.gz`. Set `--archive-format gzip` to request gzip
explicitly. The online installer caches verified downloads under
`${XDG_CACHE_HOME:-$HOME/.cache}/aivision/all-in-one` and reuses an exact image
already loaded in Docker on `auto`. Cache files can be removed when no install
is running. The named data volume is separate from this cache.

### Install offline

For a local or offline install, transfer the complete verified candidate or the
matching [private Release](https://github.com/ob-labs/ai-vision-skills/releases)
assets into a single directory. Both architectures need `install-all-in-one.py`
and `SHA256SUMS`.

| Docker host | Manifest | Choose one image archive | CLI |
|---|---|---|---|
| Linux x86-64 | `all-in-one-manifest.json` | `aiv-all-in-one-linux-amd64.tar.zst` or `.tar.gz` | `aiv-linux-x64.tar.gz` when included |
| Linux ARM64 | `all-in-one-manifest-arm64.json` | `aiv-all-in-one-linux-arm64.tar.zst` or `.tar.gz` | `aiv-linux-arm64.tar.gz` |

Verify the files before running the installer. This path works without `gh` on
the Docker host. If an authorized Release contains both architectures and you
only download one set, use `sha256sum --check --ignore-missing SHA256SUMS`.
Confirm every file in your set is present and reports `OK`.

```sh
cd /path/to/all-in-one-release-assets
sha256sum --check --ignore-missing SHA256SUMS &&
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

## View a sample Trace

If the installed preview includes `sample-trace.py`, register in the Web UI
and run its installer once more with `--sample-trace` in a terminal on the
Linux Docker host. This creates a small synthetic Trace to explore the UI and
makes zero model calls. Continue to Agent onboarding below if your preview
does not include the sample helper.

```sh
python3 ./install-all-in-one.py --sample-trace
```

If you installed from a Skill, run its copy of the installer. Use the same
`--name` for a custom instance. The installer reads its existing ports, then
uses the matching release's sample helper. For an offline install, include
`sample-trace.py` from that release and add `--from-dir "$PWD"`.

Enter the existing local AI Vision account's email and password at the
prompt. The terminal hides the password. Open the returned Trace link in the
browser while signed in to the same account. The Trace appears under the
sample space and Agent and is labeled as synthetic. On a VM, keep the Web
port forwarded while opening the link. AgentLens remains available for rule
diagnosis. Connect your own Agent below when you want to see its telemetry.

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
   : "${preview_tag:?Set this to the exact All-in-One preview tag}"
   installer=./install-all-in-one.py
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
