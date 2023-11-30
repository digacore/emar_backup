pushd %~dp0
msiexec  /l*V uninstall.log /uninstall bin\agent.msi
popd
