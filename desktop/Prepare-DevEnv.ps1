Push-Location $PSScriptRoot

Copy-Item -Path ".\7z\*" -Destination "."
Copy-Item -Path ".\msi\Create-DesktopShortcut.ps1" -Destination "."

Pop-Location
