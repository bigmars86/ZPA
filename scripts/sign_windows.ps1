<#
.SYNOPSIS
  Code-sign the ZPA executable on Windows.

.DESCRIPTION
  Signing with a certificate that the target PC trusts removes the
  "Unknown publisher" prompt on THAT PC.

  A self-signed certificate (the default here) is only trusted on machines where
  you install the exported .cer into BOTH "Trusted Root Certification
  Authorities" and "Trusted Publishers". Good for a known set of PCs you control.

  To be trusted on ANY Windows PC with no per-machine setup, you need a
  code-signing certificate from a public CA. An EV certificate additionally
  clears the SmartScreen "protected your PC" prompt immediately. Point -PfxPath
  at that certificate instead of using the self-signed default.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\sign_windows.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\sign_windows.ps1 -PfxPath cert.pfx -PfxPassword (Read-Host -AsSecureString)
#>
param(
    [string]$ExePath = "dist\ZPA.exe",
    [string]$PfxPath,
    [System.Security.SecureString]$PfxPassword,
    [string]$Subject = "Zoom Poll Analyzer",
    [string]$TimestampServer = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "Executable not found: $ExePath. Build it first (build.bat)."
}

if ($PfxPath) {
    if (-not (Test-Path $PfxPath)) { throw "PFX not found: $PfxPath" }
    $cert = Get-PfxCertificate -FilePath $PfxPath -Password $PfxPassword
} else {
    Write-Host "No -PfxPath given: using / creating a self-signed code-signing certificate."
    # Match by the Code Signing EKU OID (1.3.6.1.5.5.7.3.3) rather than the
    # display name, which is localized (e.g. "Codesignatur" on German Windows).
    $cert = Get-ChildItem Cert:\CurrentUser\My |
        Where-Object {
            $_.Subject -eq "CN=$Subject" -and $_.HasPrivateKey -and
            ($_.EnhancedKeyUsageList.ObjectId -contains '1.3.6.1.5.5.7.3.3')
        } |
        Sort-Object NotAfter -Descending |
        Select-Object -First 1
    if (-not $cert) {
        $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=$Subject" `
            -CertStoreLocation Cert:\CurrentUser\My -KeyExportPolicy Exportable `
            -NotAfter (Get-Date).AddYears(5)
        Write-Host "Created self-signed certificate: $($cert.Thumbprint)"
    } else {
        Write-Host "Reusing certificate: $($cert.Thumbprint)"
    }
    # Export the public certificate so other PCs can be told to trust it
    $cerPath = Join-Path (Split-Path $ExePath -Parent) "ZPA-code-signing.cer"
    Export-Certificate -Cert $cert -FilePath $cerPath | Out-Null
    Write-Host "Public certificate exported: $cerPath"
    Write-Host "On each target PC (run once, as Administrator) trust it in BOTH stores:"
    Write-Host "  Import-Certificate -FilePath ZPA-code-signing.cer -CertStoreLocation Cert:\LocalMachine\Root"
    Write-Host "  Import-Certificate -FilePath ZPA-code-signing.cer -CertStoreLocation Cert:\LocalMachine\TrustedPublisher"
}

Write-Host "Signing $ExePath ..."
$result = Set-AuthenticodeSignature -FilePath $ExePath -Certificate $cert `
    -TimestampServer $TimestampServer -HashAlgorithm SHA256
Write-Host "Signature status: $($result.Status)"
if ($result.Status -ne "Valid") {
    Write-Warning "Signature not 'Valid' yet - expected for a self-signed cert on a machine that does not trust it. Import the .cer as shown above."
}
