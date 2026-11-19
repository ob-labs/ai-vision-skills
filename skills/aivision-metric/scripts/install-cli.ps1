param([ValidateSet('Resolve', 'Install')] [string] $Mode = 'Resolve')

$ErrorActionPreference = 'Stop'
$architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
if ($architecture -ne 'X64') { throw 'The Windows CLI archive requires Windows x64.' }
$repository = 'antgroup/ai-vision'
if ($env:AIV_REPOSITORY -and $env:AIV_REPOSITORY -cne $repository) { throw 'Product releases belong to antgroup/ai-vision.' }
$tag = [string] $env:AIV_TAG
if ($tag -and $tag -cnotmatch '^v[0-9][A-Za-z0-9.-]*$') { throw 'Set AIV_TAG to an exact versioned product tag.' }
$channel = if ($env:AIV_CHANNEL) { $env:AIV_CHANNEL } elseif ($tag -clike '*-daily.*') { 'daily' } else { 'stable' }
if ($channel -cnotin @('daily', 'stable')) { throw 'Select AIV_CHANNEL=daily or AIV_CHANNEL=stable.' }
if ($Mode -eq 'Install' -and -not $tag) { throw 'Resolve a compatible release, then set AIV_TAG to its exact tag before installing.' }
$curl = Get-Command curl.exe -CommandType Application -TotalCount 1 -ErrorAction SilentlyContinue
if (-not $curl) { $curl = Get-Command curl -CommandType Application -TotalCount 1 }
Get-Command jq | Out-Null

function Get-PublicFile([string] $Url, [string] $Path) {
    & $curl.Source -q --fail --silent --show-error --location --connect-timeout 15 --proto '=https' --proto-redir '=https' --tlsv1.2 $Url -o $Path
    if ($LASTEXITCODE -ne 0) { throw "GitHub HTTPS request failed (exit $LASTEXITCODE)." }
}

function Get-CheckedAssetHash([string] $Path, $Asset) {
    if ((Get-Item -LiteralPath $Path).Length -ne $Asset.size) { throw "GitHub asset size mismatch for $($Asset.name)." }
    $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Asset.digest -and "sha256:$hash" -cne $Asset.digest) { throw "GitHub asset digest mismatch for $($Asset.name)." }
    $hash
}

function Get-ReleaseAsset($Asset) {
    $path = Join-Path $tmp $Asset.name
    Get-PublicFile "https://github.com/$repository/releases/download/$($selected.tag)/$($Asset.name)" $path
    $path
}

function Get-ExpectedHash([string] $Name, [string] $Checksums) {
    $pattern = '^([a-f0-9]{64})\s+\*?' + [regex]::Escape($Name) + '$'
    $lines = @(Get-Content -LiteralPath $Checksums | Select-String -CaseSensitive -Pattern $pattern)
    if ($lines.Count -ne 1) { throw "Missing or duplicate checksum for $Name." }
    $lines[0].Matches[0].Groups[1].Value
}

$tmp = [IO.Path]::Combine([IO.Path]::GetTempPath(), 'aiv-release-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($tmp) | Out-Null
$staged = $null
try {
    $api = "https://api.github.com/repos/$repository/releases"
    $pagePath = Join-Path $tmp 'page.json'
    if ($tag) {
        Get-PublicFile "$api/tags/$tag" $pagePath
        $pages = '[[' + (Get-Content -Raw -LiteralPath $pagePath) + ']]'
    } else {
        $pagesList = [Collections.Generic.List[string]]::new()
        for ($page = 1; ; $page++) {
            Get-PublicFile "${api}?per_page=100&page=$page" $pagePath
            $pageJson = jq -ce 'if type == "array" then . else error("Invalid releases page") end' $pagePath
            if ($LASTEXITCODE -ne 0) { throw 'Invalid GitHub Releases page.' }
            $pagesList.Add($pageJson)
            if ((jq 'length' $pagePath) -ne '100') { break }
        }
        $pages = '[' + ($pagesList -join ',') + ']'
    }
    $tagArgument = if ($tag) { $tag } else { '__auto__' }
    $selection = $pages | jq -ce --arg platform windows-x64 --arg channel $channel --arg tag $tagArgument -f (Join-Path $PSScriptRoot 'discover-cli.jq')
    if ($LASTEXITCODE -ne 0) { throw "No compatible published $channel CLI for Windows x64." }
    $selected = $selection | ConvertFrom-Json
    Get-PublicFile "$api/tags/$($selected.tag)" $pagePath
    $release = Get-Content -Raw -LiteralPath $pagePath | ConvertFrom-Json
    if ($release.id -ne $selected.release_id -or $release.tag_name -cne $selected.tag -or $release.draft -or -not $release.published_at -or
        $release.prerelease -ne ($selected.profile -eq 'daily')) { throw 'The exact release changed during discovery.' }
    foreach ($asset in $selected.assets.PSObject.Properties.Value) {
        $current = @($release.assets | Where-Object { $_.name -ceq $asset.name })
        if ($current.Count -ne 1 -or $current[0].id -ne $asset.id -or $current[0].size -ne $asset.size -or
            $current[0].digest -cne $asset.digest -or $current[0].state -cne $asset.state) { throw 'The exact release assets changed during discovery.' }
    }

    $checksumsPath = Get-ReleaseAsset $selected.assets.checksums
    Get-CheckedAssetHash $checksumsPath $selected.assets.checksums | Out-Null
    $manifestPath = Get-ReleaseAsset $selected.assets.manifest
    if ((Get-CheckedAssetHash $manifestPath $selected.assets.manifest) -cne (Get-ExpectedHash $selected.assets.manifest.name $checksumsPath)) {
        throw 'Product manifest checksum mismatch.'
    }
    jq -e --arg tag $selected.tag --arg version $selected.product_version --arg channel $channel -f (Join-Path $PSScriptRoot 'verify-release-manifest.jq') $manifestPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Product manifest does not match the selected published release.' }
    $archiveHash = Get-ExpectedHash $selected.package $checksumsPath
    Get-ExpectedHash $selected.assets.oceanbase.name $checksumsPath | Out-Null
    Get-ExpectedHash $selected.assets.seekdb.name $checksumsPath | Out-Null
    if ($Mode -eq 'Resolve') {
        [ordered] @{ repository = $repository; tag = $selected.tag; base_tag = $selected.base_tag; product_version = $selected.product_version;
            cli_platform = $selected.cli_platform; profile = $selected.profile; package = $selected.package } | ConvertTo-Json -Compress
        return
    }

    $archivePath = Get-ReleaseAsset $selected.assets.package
    if ((Get-CheckedAssetHash $archivePath $selected.assets.package) -cne $archiveHash) { throw 'Windows CLI ZIP checksum mismatch.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $binary = Join-Path $tmp 'aiv.exe'
    $archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
    try {
        $entries = @($archive.Entries | Where-Object { $_.FullName -ceq 'aiv.exe' })
        if ($entries.Count -ne 1 -or $entries[0].Length -eq 0) { throw 'The ZIP does not contain exactly one aiv.exe.' }
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entries[0], $binary)
    } finally { $archive.Dispose() }
    $actualVersion = & $binary --version
    if ($LASTEXITCODE -ne 0 -or $actualVersion -cne "aiv $($selected.product_version)") { throw 'The executable version differs from the selected release.' }
    $destination = if ($env:AIV_INSTALL_DIR) { $env:AIV_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'AI Vision\bin' }
    [IO.Directory]::CreateDirectory($destination) | Out-Null
    $target = Join-Path $destination 'aiv.exe'
    $staged = Join-Path $destination ('.aiv-' + [Guid]::NewGuid().ToString('N') + '.exe')
    [IO.File]::Copy($binary, $staged)
    # Preserve a null backup path across PowerShell's string parameter conversion.
    if ([IO.File]::Exists($target)) { [IO.File]::Replace($staged, $target, [NullString]::Value) }
    else { [IO.File]::Move($staged, $target) }
    Write-Output "Installed $target"
    Write-Output $actualVersion
} finally {
    if ($staged -and [IO.File]::Exists($staged)) { [IO.File]::Delete($staged) }
    Remove-Item -LiteralPath $tmp -Recurse -Force
}
