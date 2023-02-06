#================

$cred = Get-Credential  -Message "Please enter credatials for scheduled backup update" -UserName $env:UserName
$username = $cred.username
$password = $cred.GetNetworkCredential().password

function Test-Credential {
    <#
    .SYNOPSIS
        Takes a PSCredential object and validates it against the domain (or local machine, or ADAM instance).

    .PARAMETER cred
        A PScredential object with the username/password you wish to test. Typically this is generated using the Get-Credential cmdlet. Accepts pipeline input.

    .OUTPUTS
        A boolean, indicating whether the credentials were successfully validated.

    #>
    param(
        [parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [System.Management.Automation.PSCredential]$credential
    )
    begin {
        Add-Type -assemblyname system.DirectoryServices.accountmanagement
        $DS = New-Object System.DirectoryServices.AccountManagement.PrincipalContext([System.DirectoryServices.AccountManagement.ContextType]::Machine) 
    }
    process {
        $DS.ValidateCredentials($credential.UserName, $credential.GetNetworkCredential().password)
    }
}
