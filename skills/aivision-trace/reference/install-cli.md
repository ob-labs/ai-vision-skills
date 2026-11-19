# Installing the `aiv` CLI

Reuse an installed compatible CLI. On Linux or macOS, expose its permanent
install directory in the current terminal and check the executable. If it
lives elsewhere, use that directory instead.

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v aiv
aiv --version
```

On Windows, use `Get-Command aiv` and `aiv --version` in PowerShell. Check the
command help for the capability you need before changing the deployment or
profile.

## Discover a published CLI

Use [official AI Vision Releases](https://github.com/antgroup/ai-vision/releases).
The standard release build targets Linux and macOS on x64 and ARM64. A native
Windows x64 installation requires its own published ZIP in the selected
Release. Check availability before proceeding. CLI availability is independent
of Docker host or Agent compatibility.

Set `AIV_SKILL_DIR` to the installed directory of this Skill. It contains
`SKILL.md` and `scripts/`. The bundled [shell helper](../scripts/install-cli.sh)
and [PowerShell helper](../scripts/install-cli.ps1) share a
[release selector](../scripts/discover-cli.jq) and require `curl` and `jq`.
These helpers read the public Releases over HTTPS.

Without overrides, discovery selects the highest compatible stable version.
For a preview, explicitly select `AIV_CHANNEL=daily`. An exact `AIV_TAG` pins a
versioned tag such as `vX.Y.Z` (Stable) or
`vX.Y.Z-daily.YYYYMMDD[.N]` (Daily). If you set only the exact tag, the helper
infers the channel. Rolling aliases are excluded.

The helper checks the exact Release and verifies its manifest and checksums.
Review the resolved repository, tag, product version, platform, and archive.
If no compatible Release exists, use a compatible CLI already available on
your machine or follow the [product source-build instructions](https://github.com/antgroup/ai-vision/tree/HEAD/aivision-cli#source-build-pointing-at-a-different-repo-or-branch)
when source is available and you intend to build it. For a new deployment,
wait for the matching deployment assets or follow the product's source
deployment instructions. A missing asset leaves the current installation in
place.

### Linux or macOS

```bash
: "${AIV_SKILL_DIR:?Set this to the installed Skill directory}"
sh "$AIV_SKILL_DIR/scripts/install-cli.sh" --resolve
```

For an explicitly selected Daily, add `AIV_CHANNEL=daily` before the command.
Set `AIV_TAG` to the exact tag from discovery, then run:

```bash
: "${AIV_TAG:?Set this to the verified tag from discovery}"
AIV_TAG="$AIV_TAG" sh "$AIV_SKILL_DIR/scripts/install-cli.sh" --install
```

The helper verifies the archive SHA-256 and executable version before replacing
the CLI. The default destination is `$HOME/.local/bin/aiv`. Set
`AIV_INSTALL_DIR` to preserve a custom location. Add the directory to your user
PATH and verify `command -v aiv`, `aiv --version`, and the relevant command help
in a new terminal. See [durable PATH setup](path-setup.md).

### Windows x64

Run the following only for an official Release with a Windows x64 ZIP and
matching checksums.

```powershell
if (-not $env:AIV_SKILL_DIR) { throw 'Set AIV_SKILL_DIR to the installed Skill directory.' }
& "$env:AIV_SKILL_DIR/scripts/install-cli.ps1" -Mode Resolve
```

Set `$env:AIV_TAG` to the exact tag from discovery, then run:

```powershell
& "$env:AIV_SKILL_DIR/scripts/install-cli.ps1" -Mode Install
```

The default destination is `%LOCALAPPDATA%\AI Vision\bin\aiv.exe`. Set
`AIV_INSTALL_DIR` to preserve a custom location. Add the directory to your user
Path and verify `Get-Command aiv`, `aiv --version`, and the relevant command help
in a new PowerShell window.
