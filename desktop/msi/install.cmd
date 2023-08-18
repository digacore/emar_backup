pushd %~dp0
msiexec  /l* install.log /i bin\agent.msi /quiet
popd
