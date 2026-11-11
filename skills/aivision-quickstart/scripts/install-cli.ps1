param([ValidateSet('Resolve', 'Install')] [string] $Mode = 'Resolve')

$ErrorActionPreference = 'Stop'
$architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
if ($architecture -ne 'X64') { throw 'The Windows CLI archive requires Windows x64.' }
$tag = [string] $env:AIV_TAG
if ($tag -cnotmatch '^[A-Za-z0-9.-]*$') { throw 'Set AIV_TAG to an exact versioned tag.' }
$channel = if ($env:AIV_CHANNEL) { $env:AIV_CHANNEL } elseif ($tag -match '^v[0-9]') { 'stable' } else { 'daily' }
$repository = switch ($channel) {
    'daily' { 'ob-labs/ai-vision-skills' }
    'stable' { 'ob-labs/ai-vision-ob' }
    default { throw 'Select AIV_CHANNEL=daily or AIV_CHANNEL=stable.' }
}
if ($env:AIV_REPOSITORY) {
    if ($channel -eq 'daily' -and $env:AIV_REPOSITORY -ne $repository) { throw 'Restricted Daily assets belong to ob-labs/ai-vision-skills.' }
    $repository = $env:AIV_REPOSITORY
}
if ($repository -cnotmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') { throw 'Select an OWNER/REPO repository.' }
if ($Mode -eq 'Install' -and -not $tag) { throw 'Resolve a compatible release, then set AIV_TAG to its exact tag before installing.' }
Get-Command gh, jq | Out-Null

function Invoke-Gh([string[]] $Arguments) {
    $output = & gh @Arguments
    if ($LASTEXITCODE -ne 0) { throw "GitHub CLI request failed (exit $LASTEXITCODE)." }
    $output
}

function Get-CheckedAssetHash([string] $Path, $Asset) {
    $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Asset.digest -and "sha256:$hash" -cne $Asset.digest) { throw "GitHub asset digest mismatch for $($Asset.name)." }
    $hash
}

$pages = Invoke-Gh @('api', '--hostname', 'github.com', '--paginate', '--slurp', "repos/$repository/releases?per_page=100")
# jq 1.6/1.7 under Windows PowerShell can drop an empty native command argument.
$tagArgument = if ($tag) { $tag } else { '__auto__' }
$selection = $pages | jq -ce --arg platform windows-x64 --arg channel $channel --arg tag $tagArgument -f (Join-Path $PSScriptRoot 'discover-cli.jq')
if ($LASTEXITCODE -ne 0) { throw "No compatible published $channel Windows x64 CLI at the requested selection." }
$selected = $selection | ConvertFrom-Json
$release = (Invoke-Gh @('api', '--hostname', 'github.com', "repos/$repository/releases/tags/$($selected.tag)")) | ConvertFrom-Json
if ($release.id -ne $selected.release_id -or $release.tag_name -cne $selected.tag -or $release.draft -or -not $release.published_at -or
    $release.prerelease -ne ($selected.profile -ne 'stable')) { throw 'The exact release changed during discovery.' }
foreach ($asset in $selected.assets.PSObject.Properties.Value) {
    if ($null -eq $asset) { continue }
    $current = @($release.assets | Where-Object { $_.name -ceq $asset.name })
    if ($current.Count -ne 1 -or $current[0].id -ne $asset.id -or $current[0].size -ne $asset.size -or
        $current[0].digest -cne $asset.digest -or $current[0].state -cne $asset.state) { throw 'The exact release assets changed during discovery.' }
}

$tmp = [IO.Path]::Combine([IO.Path]::GetTempPath(), 'aiv-release-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($tmp) | Out-Null
$staged = $null
try {
    $checksum = $null
    if ($selected.profile -eq 'windows') {
        Invoke-Gh @('release', 'download', $selected.tag, '--repo', "github.com/$repository", '--pattern', $selected.manifest, '--dir', $tmp) | Out-Null
        $manifestPath = Join-Path $tmp $selected.manifest
        Get-CheckedAssetHash $manifestPath $selected.assets.manifest | Out-Null
        $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
        $archiveRecord = $manifest.assets.PSObject.Properties[$selected.package].Value
        $checksum = $archiveRecord.sha256
        if ($manifest.release.tag -cne $selected.base_tag -or $manifest.release.repository -cne $repository -or
            $manifest.product_version -cne $selected.product_version -or $manifest.client_platform -cne 'windows-x64' -or
            "sha256:$checksum" -cne $selected.assets.package.digest -or $archiveRecord.size -ne $selected.assets.package.size) {
            throw 'Windows preview manifest does not match the selected version, platform, or archive.'
        }
    }
    if ($Mode -eq 'Resolve') {
        [ordered] @{ repository = $repository; tag = $selected.tag; base_tag = $selected.base_tag; product_version = $selected.product_version;
            cli_platform = $selected.cli_platform; profile = $selected.profile; package = $selected.package } | ConvertTo-Json -Compress
        return
    }

    $download = @('release', 'download', $selected.tag, '--repo', "github.com/$repository", '--pattern', $selected.package, '--dir', $tmp)
    if (-not $checksum) { $download += @('--pattern', 'SHA256SUMS') }
    Invoke-Gh $download | Out-Null
    if (-not $checksum) {
        $pattern = '^([a-f0-9]{64})\s+\*?' + [regex]::Escape($selected.package) + '$'
        $checksumsPath = Join-Path $tmp 'SHA256SUMS'
        Get-CheckedAssetHash $checksumsPath $selected.assets.checksums | Out-Null
        $checksumLines = @(Get-Content -LiteralPath $checksumsPath | Select-String -CaseSensitive -Pattern $pattern)
        if ($checksumLines.Count -ne 1) { throw 'Missing or duplicate Windows CLI checksum.' }
        $checksum = $checksumLines[0].Matches[0].Groups[1].Value
    }
    $archivePath = Join-Path $tmp $selected.package
    if ((Get-CheckedAssetHash $archivePath $selected.assets.package) -cne $checksum) { throw 'Windows CLI ZIP checksum mismatch.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $binary = Join-Path $tmp 'aiv.exe'
    $archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
    try {
        $entry = @($archive.Entries | Where-Object { $_.FullName -ceq 'aiv.exe' })
        if ($entry.Count -ne 1 -or $entry[0].Length -eq 0) { throw 'The ZIP does not contain exactly one aiv.exe.' }
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entry[0], $binary)
    } finally { $archive.Dispose() }
    $actualVersion = & $binary --version
    if ($LASTEXITCODE -ne 0 -or $actualVersion -cne "aiv $($selected.product_version)") { throw 'The executable version differs from the selected release.' }
    $destination = if ($env:AIV_INSTALL_DIR) { $env:AIV_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'AI Vision\bin' }
    [IO.Directory]::CreateDirectory($destination) | Out-Null
    $target = Join-Path $destination 'aiv.exe'
    $staged = Join-Path $destination ('.aiv-' + [Guid]::NewGuid().ToString('N') + '.exe')
    [IO.File]::Copy($binary, $staged)
    if ([IO.File]::Exists($target)) { [IO.File]::Replace($staged, $target, $null) }
    else { [IO.File]::Move($staged, $target) }
    Write-Output "Installed $target"
    Write-Output $actualVersion
} finally {
    if ($staged -and [IO.File]::Exists($staged)) { [IO.File]::Delete($staged) }
    Remove-Item -LiteralPath $tmp -Recurse -Force
}
