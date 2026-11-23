# AI Vision All-in-One Personal Edition

Use All-in-One for a personal installation. One container starts AI
Vision with embedded seekdb, and one named Docker volume holds its data. Use
the [distributed deployment](../SKILL.md#choose-a-deployment-mode) for a shared
installation, an external database, or an existing distributed stack.

## Install and open AI Vision

Use a **Linux x86-64 or ARM64** machine or VM with Python 3.8+ and access to a
local Docker daemon of the same architecture. Choose an online release or a
verified local bundle with assets for that host. Allow up to 2 CPUs and 6 GiB
of memory for the container, plus disk space for the image and growing data
volume. The web port `5174` and OTLP/HTTP port `4318` bind to loopback. Choose
unused ports if another service already uses either one.

### Run the installer directly

Check [AI Vision Releases](https://github.com/antgroup/ai-vision/releases) for
a Daily prerelease tagged `vX.Y.Z-daily.YYYYMMDD[.N]` with All-in-One assets
for your host. In an empty directory, set `release_tag` to the exact tag.
Use `curl` and `sha256sum` to download and verify the official installer
from that Release. Public downloads work without GitHub sign-in.
If a compatible Daily is unavailable, use a trusted local bundle, a compatible
[distributed release](../SKILL.md#choose-release-or-daily), or an existing
instance.

```sh
: "${release_tag:?Set this to the exact All-in-One Daily tag}"
release_url="https://github.com/antgroup/ai-vision/releases/download/$release_tag"
installer=./install-all-in-one.py
printf '%s\n' "$release_tag" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+-daily\.[0-9]{8}(\.[0-9]+)?$' &&
  curl -q --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --output "$installer" "$release_url/install-all-in-one.py" &&
  curl -q --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --output SHA256SUMS "$release_url/SHA256SUMS" &&
  (grep -E '^[0-9a-f]{64}  install-all-in-one\.py$' SHA256SUMS | sha256sum --check) &&
  python3 "$installer" --tag "$release_tag"
```

Keep the verified installer and `release_tag` for retries and recreation.
The installer checks Docker, the instance name and local ports before
downloading. It checks the architecture manifest against the shared release
manifest and verifies the image archive before loading it into Docker.
The container uses embedded seekdb.

When the installer reports healthy, open the reported Web URL and follow the
[account registration and first-use handoff](../SKILL.md#help-the-user-sign-in-and-get-started).
If the browser runs outside the Linux VM, [forward the ports](#access-ai-vision-from-a-vm).

On Docker Server 23 or later, the installer prefers a verified `.tar.zst`
archive when available. The `.tar.gz` archive also works with older servers.
Set `--archive-format gzip` to request gzip explicitly. The online installer
caches verified downloads under
`${XDG_CACHE_HOME:-$HOME/.cache}/aivision/all-in-one` and reuses an exact image
already loaded in Docker on `auto`. Cache files can be removed when no install
is running. The named data volume is separate from this cache.

### Install with a coding Agent

Identify the published Daily with All-in-One assets for the Docker host.
Show its exact tag, then use the [verified Release installer](#run-the-installer-directly)
on that host. If the image download stalls, offer the user the
[optional download proxy](#speed-up-a-slow-download). Use the
[offline bundle workflow](#install-offline) when the user supplies local
assets. After startup, help the user register or sign in
and [open their first Trace](../SKILL.md#help-the-user-sign-in-and-get-started).

### Speed up a slow download

Start with the official Release download. If it stalls or times out, you can
prefix the public image archive URL with `https://ghfast.top/` or
`https://gh-proxy.org/`. Both proxies delivered the complete ARM64 `.tar.zst` for
[Daily `v0.6.0-daily.20261123.2`](https://github.com/antgroup/ai-vision/releases/tag/v0.6.0-daily.20261123.2)
with the official SHA-256. Availability and speed vary by network. Use a
third-party proxy only if the user chooses it.

Use a separate directory for each Daily tag. Get `SHA256SUMS`, the manifests,
the CLI, and any installer or sample helper from the official Release. Use the
proxy only for an anonymous HTTPS download of the public image archive. Keep
credentials and private URLs out of the proxy request.

Set `release_tag` to the exact Daily tag. Edit `proxy` to choose a host and
select your archive from the [offline asset table](#install-offline). This
example uses ARM64. Rerun the same command to resume an interrupted transfer.

```sh
: "${release_tag:?Set this to the exact All-in-One Daily tag}"
release_url="https://github.com/antgroup/ai-vision/releases/download/$release_tag"
archive=aiv-all-in-one-linux-arm64.tar.zst
proxy=https://ghfast.top
printf '%s\n' "$release_tag" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+-daily\.[0-9]{8}(\.[0-9]+)?$' &&
  curl -q --fail --location --proto '=https' --proto-redir '=https' \
    --continue-at - --output "$archive" "${proxy%/}/$release_url/$archive" &&
  (awk -v archive="$archive" '$2 == archive { print }' SHA256SUMS | sha256sum --check)
```

If verification fails, discard the archive. When the archive passes, follow
[Install offline](#install-offline) to verify the rest of the bundle and install.

### Install offline

For a local or offline install, transfer the complete verified candidate or the
matching [product Release](https://github.com/antgroup/ai-vision/releases)
assets into a single directory. Use the installer bundled with this Skill or
the verified release installer. Keep the original `SHA256SUMS`, the Daily's
shared `release-manifest.json`, and the files for your host listed below.

| Docker host | Manifest | Choose one image archive | CLI |
|---|---|---|---|
| Linux x86-64 | `all-in-one-manifest.json` | `aiv-all-in-one-linux-amd64.tar.zst` or `.tar.gz` | `aiv-linux-x64.tar.gz` |
| Linux ARM64 | `all-in-one-manifest-arm64.json` | `aiv-all-in-one-linux-arm64.tar.zst` or `.tar.gz` | `aiv-linux-arm64.tar.gz` |

Verify the files before running the installer. This path works without `gh` on
the Docker host. Check that both manifests, the chosen image archive and the
matching CLI archive are present and report `OK`. Add the verified
`sample-trace.py` if you want to try the example from a terminal. The checksum
command skips files absent from the directory.

```sh
: "${installer:?Set this to the absolute path to install-all-in-one.py}"
cd /path/to/all-in-one-release-assets
sha256sum --check --ignore-missing SHA256SUMS &&
  python3 "$installer" --from-dir "$PWD"
```

Use `--name`, `--web-port`, and `--otlp-port` for a separate trial. Record the
actual name, version, ports, and the corresponding `<name>-data` volume.
When the installer reports healthy, open `http://127.0.0.1:5174` or the
reported Web URL. Follow the [account registration and first-use handoff](../SKILL.md#help-the-user-sign-in-and-get-started).

### Access AI Vision from a VM

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

After registering, run the installer with `--sample-trace` on the Linux
Docker host if the release or offline bundle includes `sample-trace.py`.
The Daily helper imports or reuses the platform's built-in synthetic example
in your personal Space with zero model calls. You can also open it from
**Help → Try an example** in the browser, or connect an Agent below.

Set `installer` to the same verified installer you used for deployment.
Restore that path when working in a new shell.

```sh
python3 "${installer:?Set this to the verified installer path}" --sample-trace
```

Use the same `--name` for a custom instance. The installer reads its existing
ports, then uses the matching release's sample helper. For an offline install, include
`sample-trace.py` from that release and add `--from-dir "$PWD"`.

Confirm the import and enter your local AI Vision account's email and password
when prompted. The terminal hides the password. Open the returned Trace link
in the browser while signed in to the same account. The example is labeled as
synthetic. On a VM, keep the Web port forwarded while opening the link.
AgentLens remains available for rule diagnosis. Connect your own Agent below
when you want to see its telemetry.

## Connect an Agent and find its Trace

Run `getconf GNU_LIBC_VERSION` on the Linux Agent machine and require glibc
2.35 or later. Match the CLI to the **Agent machine's** CPU. Check the
selected release for its matching native Agent payload.
The Docker host, browser and Agent can be different machines. For a different
client OS, verify that the selected release supports it before generating
an installation authorization.

1. Install or reuse the matching Linux `aiv` on the Agent machine. For a public
   Daily, copy the verified Release installer to that machine. For a local
   bundle, use its verified installer or the script bundled with
   `aivision-deploy`. Use the exact `release_tag` that installed the platform.
   The installer selects the matching CLI for the Agent machine,
   verifies its SHA-256, architecture and version, and installs it to
   `~/.local/bin/aiv`.
   It uses the bundle's CLI archive when included. For older x86-64 bundles
   with a separate base release, the installer verifies the CLI from that
   exact base release.

   ```sh
   : "${release_tag:?Set this to the exact All-in-One release tag}"
   installer="${installer:-./install-all-in-one.py}"
   python3 "$installer" --tag "$release_tag" --resolve-cli &&
     python3 "$installer" --tag "$release_tag" --install-cli
   ```

   For an offline Agent machine, transfer the installer, `SHA256SUMS`,
   the Daily's `release-manifest.json`, the manifest for the Agent architecture
   and its matching CLI archive. Use
   `python3 "$installer" --from-dir "$PWD" --install-cli` from that directory.
   The CLI-only install requires no Docker. An older x86-64 bundle whose CLI
   came from a separate base release needs a verified copy
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

Pin the recorded release tag for recreation. To try a different release
alongside it, use a new `--name` and unused ports. Upgrades across releases
and migration from a distributed deployment require separate validation.
