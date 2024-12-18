$wixFolder = Join-Path $PSScriptRoot -ChildPath 'wix\'
$candleToolPath = Join-Path $wixFolder -ChildPath candle.exe
$lightToolPath = Join-Path $wixFolder -ChildPath light.exe

try {
    Push-Location $PSScriptRoot

    if (-not (Test-Path $wixFolder)) {
        throw "Folder $wixFolder does not exist. Start DownloadAndExtractWix.ps1 script to create it."
    }
    if ((-not (Test-Path $candleToolPath)) -or (-not (Test-Path $lightToolPath))) {
        throw "Tools required to build installer (candle.exe and light.exe) do not exist in wix folder."
    }

    $wxsFileName = "ProductUnPrompt.wxs"
    $wixobjFileName = "ProductUnPrompt.wixobj"
    $msiFileName = "agent_unprompt.msi"

    # compiling wxs file into wixobj
    & "$candleToolPath" $wxsFileName -out obj\$wixobjFileName -arch x64 -ext wix\WixUtilExtension.dll
    if ($LASTEXITCODE -ne 0) {
        throw "Compilation of $wxsFileName failed with exit code $LASTEXITCODE"
    }

    # linking wixobj into msi
    & "$lightToolPath" obj\$wixobjFileName -ext WixUtilExtension -out bin\$msiFileName -pdbout bin\agent_unprompt.wixpdb
    if ($LASTEXITCODE -ne 0) {
        throw "Linking of $wixobjFileName failed with exit code $LASTEXITCODE"
    }
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}
