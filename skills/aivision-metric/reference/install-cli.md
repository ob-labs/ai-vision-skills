# Installing the `aiv` CLI

Reuse an installed compatible CLI. Verify its version and the command needed by
the selected Skill in a fresh terminal.

```bash
command -v aiv
aiv --version
aiv cast --help
```

On Windows, use `Get-Command aiv` to inspect the installed executable.

## Discover a published CLI

The [product Releases](https://github.com/antgroup/ai-vision/releases) supply
Stable `vMAJOR.MINOR.PATCH` and Daily `vMAJOR.MINOR.PATCH-daily.YYYYMMDD[.N]`
assets. Stable is the default. Select Daily explicitly with `AIV_CHANNEL=daily`,
or give `AIV_TAG` a full versioned Daily tag. The helper requires `curl` and
`jq` and uses public HTTPS. GitHub CLI and an account token are unnecessary.

The helper selects the newest compatible published version and requires its
CLI archive, product manifest, checksums, and both database vars files. Its
output includes the selected `tag`, `product_version`, and `cli_platform`.
Check the platform separately on the deployment host and the Agent client.
Stable and Daily downloads are limited to the assets offered by that release.
Product Linux and macOS archives have x64 and ARM64 variants. A Windows x64
installation requires `aiv-windows-x64.zip` from the same public release. Reuse
an existing compatible Windows CLI if the release has no Windows archive.

Install only an exact published tag. When no compatible release is available,
keep the existing CLI and report the missing platform or version. Workflow
candidate artifacts and rolling aliases are separate from the versioned
release selection.

### Linux and macOS

Set `AIV_SKILL_DIR` to this installed Skill directory. Discovery chooses the
Apple Silicon archive on a Mac running a Rosetta shell.

```bash
: "${AIV_SKILL_DIR:?Set this to the installed Skill directory}"
sh "$AIV_SKILL_DIR/scripts/install-cli.sh" --resolve
```

For Daily, set `AIV_CHANNEL=daily` for discovery. After checking the result, set
`AIV_TAG` to its exact tag and install:

```bash
: "${AIV_TAG:?Set this to the verified versioned tag}"
AIV_TAG="$AIV_TAG" sh "$AIV_SKILL_DIR/scripts/install-cli.sh" --install
```

The installer verifies the release metadata, product manifest, archive checksum,
and `aiv --version` before replacing the executable in `~/.local/bin`. Set
`AIV_INSTALL_DIR` to retain a custom install location. A failed check preserves
any existing executable. Add the install directory to `PATH` using your shell startup file, then verify
`command -v aiv` and `aiv --version` in a fresh terminal.

### Windows x64

Run native PowerShell with `curl.exe` and `jq`. This path is available only when
the public release includes the Windows archive.

```powershell
if (-not $env:AIV_SKILL_DIR) { throw 'Set AIV_SKILL_DIR to the installed Skill directory' }
& "$env:AIV_SKILL_DIR/scripts/install-cli.ps1" -Mode Resolve
```

Set `$env:AIV_TAG` to the exact returned tag before installing.

```powershell
& "$env:AIV_SKILL_DIR/scripts/install-cli.ps1" -Mode Install
```

The default installation directory is `%LOCALAPPDATA%\AI Vision\bin`. To preserve
a custom directory, set `AIV_INSTALL_DIR`. Add the selected directory to your
user `Path` and run `Get-Command aiv` and `aiv --version` in a new terminal.
