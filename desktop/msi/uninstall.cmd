pushd %~dp0
msiexec  /l* uninstall.log /uninstall bin\agent.msi
popd
