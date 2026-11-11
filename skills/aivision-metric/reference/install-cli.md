# Installing the `aiv` CLI

Reuse an installed compatible CLI, including when offline. On Linux or macOS,
expose the permanent install directory in this terminal and check the executable
and relevant command. Use the confirmed directory if the CLI is installed elsewhere.

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v aiv
aiv --version
aiv query metadata --help
```

On Windows, use `Get-Command aiv` and run the same version and help commands in
PowerShell. For a capability missing from the installed CLI, select a compatible
release before changing the platform deployment or user profile.

## Discover a published CLI

CLI delivery supports Linux x64, Apple Silicon, and Windows x64. Intel Mac,
Linux ARM64, and Windows ARM64 delivery are paused. Selectors apply this scope
to both channels and to explicit tags.

Set `AIV_SKILL_DIR` to the installed directory of **this** Skill, which contains
`SKILL.md` and `scripts/`. The [shell helper](../scripts/install-cli.sh) and
[PowerShell helper](../scripts/install-cli.ps1) use the same
[release selector](../scripts/discover-cli.jq). They require `gh` and `jq`.
Authenticate `gh` to `github.com` with an account that can read the selected
repository. Release access and image pull access are independent.

For **Daily**, discovery queries the private `ob-labs/ai-vision-skills` Releases
API across all pages. It picks the highest numeric product version and update
for the current client platform among compatible published prereleases. The result
can be older than a Daily published for a different platform. **Stable** uses
published stable `v` releases from `ob-labs/ai-vision-ob`; set `AIV_CHANNEL=stable`
when that is the selected channel. An explicit `AIV_TAG` pins an exact release;
set it before resolving if a deployment or upgrade requires a specific build.
Discovery is read-only and uses no fixed default version or `releases/latest`.

Read the returned JSON before proceeding. `tag` is the exact release for the CLI,
`product_version` is the version printed by `aiv --version`, and `base_tag` is
the corresponding base release. On macOS, a published Codex update can use a
companion tag, with its base relation verified from the release manifest. The
client architecture is independent of the Docker host architecture. Use the
matching platform and datastore variables from the verified deployment guide.

### Linux and macOS

```bash
: "${AIV_SKILL_DIR:?Set this to the installed Skill directory}"
sh "$AIV_SKILL_DIR/scripts/install-cli.sh" --resolve
```

Discovery uses the client machine's architecture. Apple Silicon selects the arm64
archive even if its shell runs under Rosetta. Review the selected version against the installed CLI and the
platform you intend to connect to. Set `AIV_TAG` to the exact returned `tag` for
this installation or upgrade, and keep the same channel and repository settings.

```bash
: "${AIV_TAG:?Set this to the verified tag from discovery}"
AIV_TAG="$AIV_TAG" sh "$AIV_SKILL_DIR/scripts/install-cli.sh" --install
```

The helper rechecks the pinned release, validates downloaded assets against
published SHA-256 values, and checks the executable version before replacing the
permanent binary. The default is `~/.local/bin/aiv`; set `AIV_INSTALL_DIR` to
keep an existing CLI's custom directory. A failed verification leaves the prior
executable in place. Finish [durable PATH setup](path-setup.md) and verify the
chosen binary in fresh interactive and login shells.

### Windows x64

Run native PowerShell on Windows x64. The Daily route selects the published
Windows preview when it includes the verified x64 ZIP and preview manifest. The
helper validates the preview manifest and ZIP against authenticated GitHub asset
digests. Stable ZIPs use the selected stable Release's checksums. Preview
availability alone does not establish native Windows qualification.

```powershell
if (-not $env:AIV_SKILL_DIR) { throw 'Set AIV_SKILL_DIR to the installed Skill directory.' }
& "$env:AIV_SKILL_DIR/scripts/install-cli.ps1" -Mode Resolve
```

Review the result, set `$env:AIV_TAG` to its exact `tag`, then run:

```powershell
& "$env:AIV_SKILL_DIR/scripts/install-cli.ps1" -Mode Install
```

The default is `%LOCALAPPDATA%\AI Vision\bin\aiv.exe`. Set `AIV_INSTALL_DIR`
to preserve a custom path. Add that directory to the Windows user `Path` if
needed. In a new PowerShell window, verify `Get-Command aiv`, `aiv --version`,
and the required command help.

An existing platform can be queried with its endpoint and SpaceKey. Docker, registry authentication, and local Agent hooks are separate operations.
