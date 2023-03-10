$WIX_FILE = ".\msi\Product.wxs"

[xml]$data = Get-Content $WIX_FILE

$currentVersion = $data.Wix.Product.Version

[version]$v = $currentVersion

$BEGIN_ERA = "2023.01.01"

$revision = [System.Math]::Round(((Get-Date).Ticks / 1e9) - ((Get-Date $BEGIN_ERA).Ticks / 1e9))

$newVersion = "{0}.{1}.{2}.{3}" -f $v.Major, $v.Minor, ([int]$v.Build + 1), $revision 

# $data.Wix.Product.Version = $newVersion

((Get-Content -path $WIX_FILE -Raw) -replace $currentVersion, $newVersion) | Set-Content -Path $WIX_FILE


