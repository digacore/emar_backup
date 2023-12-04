pushd %~dp0
msiexec  /L*V install.log /i bin\agent.msi /quiet
popd
