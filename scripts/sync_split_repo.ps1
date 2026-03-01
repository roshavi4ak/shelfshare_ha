param(
    [string]$SourcePath = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$DestinationPath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path 'shelfshare_ha'),
    [switch]$NoDelete,
    [switch]$DryRun,
    [switch]$Commit,
    [switch]$Push,
    [string]$CommitMessage = 'Sync ShelfShare HA integration from monorepo workspace'
)

$ErrorActionPreference = 'Stop'

function Invoke-RobocopySync {
    param(
        [string]$From,
        [string]$To,
        [switch]$Mirror,
        [switch]$ListOnly
    )

    $mode = if ($Mirror) { '/MIR' } else { '/E' }

    $args = @(
        $From,
        $To,
        $mode,
        '/R:2',
        '/W:1',
        '/NFL',
        '/NDL',
        '/NP',
        '/XD', '.git', 'dist', '__pycache__',
        '/XF', '*.pyc', '*.pyo'
    )

    if ($ListOnly) {
        $args += '/L'
    }

    & robocopy @args
    $exitCode = $LASTEXITCODE

    if ($exitCode -gt 7) {
        throw "Robocopy failed with exit code $exitCode"
    }

    return $exitCode
}

function Ensure-GitRepo {
    param([string]$RepoPath)

    if (-not (Test-Path (Join-Path $RepoPath '.git'))) {
        throw "Destination is not a git repository: $RepoPath"
    }
}

$sourceResolved = (Resolve-Path $SourcePath).Path

if (-not (Test-Path $sourceResolved)) {
    throw "Source path does not exist: $SourcePath"
}

if (-not (Test-Path $DestinationPath)) {
    New-Item -ItemType Directory -Path $DestinationPath | Out-Null
}

$destResolved = (Resolve-Path $DestinationPath).Path

Write-Host "Source      : $sourceResolved"
Write-Host "Destination : $destResolved"
Write-Host "Mode        : $(if ($NoDelete) { 'Copy (no delete)' } else { 'Mirror (delete extras in destination)' })"
Write-Host "Dry run     : $DryRun"

$copyResult = Invoke-RobocopySync -From $sourceResolved -To $destResolved -Mirror:(-not $NoDelete) -ListOnly:$DryRun
Write-Host "Robocopy exit code: $copyResult"

if ($DryRun) {
    Write-Host 'Dry run completed. No files were changed.'
    exit 0
}

if ($Commit -or $Push) {
    Ensure-GitRepo -RepoPath $destResolved

    Push-Location $destResolved
    try {
        git add -A

        $staged = git diff --cached --name-only
        if ($staged) {
            git commit -m $CommitMessage | Out-Host
        } else {
            Write-Host 'No git changes to commit.'
        }

        if ($Push) {
            git push | Out-Host
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host 'Sync completed successfully.'
