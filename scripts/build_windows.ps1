param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$projectRoot = (
    Resolve-Path (
        Join-Path $PSScriptRoot ".."
    )
).Path

Push-Location $projectRoot

try {
    if (-not $SkipTests) {
        python -m pytest

        if ($LASTEXITCODE -ne 0) {
            throw "Test suite failed."
        }
    }

    python -m PyInstaller `
        --noconfirm `
        --clean `
        FactoryMES.spec

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }

    $executablePath = Join-Path `
        $projectRoot `
        "dist\FactoryMES\FactoryMES.exe"

    if (-not (Test-Path $executablePath)) {
        throw (
            "Build completed without expected executable: " +
            $executablePath
        )
    }

    $artifactDirectory = Join-Path `
        $projectRoot `
        "artifacts"

    New-Item `
        -ItemType Directory `
        -Force `
        -Path $artifactDirectory |
        Out-Null

    $archivePath = Join-Path `
        $artifactDirectory `
        "FactoryMES-windows-x64.zip"

    if (Test-Path $archivePath) {
        Remove-Item `
            -LiteralPath $archivePath `
            -Force
    }

    Compress-Archive `
        -Path (
            Join-Path `
                $projectRoot `
                "dist\FactoryMES\*"
        ) `
        -DestinationPath $archivePath `
        -CompressionLevel Optimal

    Write-Host ""
    Write-Host "Build completed successfully."
    Write-Host "Executable: $executablePath"
    Write-Host "Artifact:   $archivePath"
}
finally {
    Pop-Location
}
