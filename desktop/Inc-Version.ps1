$WSX_FILE = ".\msi\Product.wxs"
$VERSION_TXT = ".\msi\version.txt"
$CONFIG_JSON = ".\config.json"

[xml]$data = Get-Content $WSX_FILE

$currentVersion = $data.Wix.Product.Version

[version]$v = $currentVersion

$BEGIN_ERA = "2023.01.01"

$revision = [System.Math]::Round(((Get-Date).Ticks / 1e9) - ((Get-Date $BEGIN_ERA).Ticks / 1e9))

$newVersion = "{0}.{1}.{2}.{3}" -f $v.Major, $v.Minor, ([int]$v.Build + 1), $revision 

((Get-Content -Path $WSX_FILE) -replace $currentVersion, $newVersion -join "`n") | Set-Content -NoNewline -Force -Path $WSX_FILE
((Get-Content -Path $VERSION_TXT) -replace $currentVersion, $newVersion -join "`n") | Set-Content -NoNewline -Force -Path $VERSION_TXT
((Get-Content -Path $CONFIG_JSON) -replace $currentVersion, $newVersion -join "`n") | Set-Content -NoNewline -Force -Path $CONFIG_JSON
