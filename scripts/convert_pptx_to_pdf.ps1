param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination
)

$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$destinationPath = [System.IO.Path]::GetFullPath($Destination)
$destinationDir = [System.IO.Path]::GetDirectoryName($destinationPath)
[System.IO.Directory]::CreateDirectory($destinationDir) | Out-Null

$powerPoint = $null
$presentation = $null
$existingPowerPoint = @(Get-Process POWERPNT -ErrorAction SilentlyContinue).Count -gt 0
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    # ReadOnly=True, Untitled=False, WithWindow=False. 32 = ppSaveAsPDF.
    $presentation = $powerPoint.Presentations.Open($sourcePath, -1, 0, 0)
    $presentation.SaveAs($destinationPath, 32)
}
finally {
    if ($null -ne $presentation) { $presentation.Close() }
    if ($null -ne $powerPoint -and -not $existingPowerPoint) { $powerPoint.Quit() }
}
