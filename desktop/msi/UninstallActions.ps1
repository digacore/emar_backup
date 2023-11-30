# Write to file c:\Emar.uninstall.log success or failure
Add-Content -Path c:\tmp\Emar.uninstall.log -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - uninstall start"
