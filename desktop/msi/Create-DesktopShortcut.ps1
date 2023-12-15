Push-Location $PSScriptRoot

$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
$TargetPath = Join-Path $cfg.backups_path "emar_backups.zip"
$IconLocation = (Get-Item "eMARVault_256x256.ico").FullName
$ShortcutPath = Join-Path $env:PUBLIC Desktop\eMARVault.lnk

$shell = New-Object -comObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $TargetPath
$shortcut.IconLocation = $IconLocation
$shortcut.WorkingDirectory = $cfg.backups_path
try {
    $shortcut.Save()
}
catch {
    Write-Error "Error: $_"
    exit 1
}

Pop-Location
