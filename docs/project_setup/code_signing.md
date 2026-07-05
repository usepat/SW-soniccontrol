@ingroup ProjectSetup

# Code Signing {#CodeSigning}

For the current Windows release flow, there are two artifacts that matter:

- `dist/SonicControl/SonicControl.exe` from `scripts/create_exe.bat`
- `dist/SonicControlInstaller/SonicControlInstaller.exe` from `scripts/installer.iss`

If you ship additional standalone executables or DLLs next to the main app, sign those as well. In this project that includes bundled tools such as `picotool.exe` and `arm-none-eabi-*.exe` whenever those files are redistributed as part of the installer or copied into the final application directory. Files that are only data, Python source, or resources usually do not need their own signature.

## Which key material to use

For public Windows distribution, do not generate your own trust root. Use a code-signing certificate from a trusted certificate authority. In practice that means:

- the private key stays on your machine, in a hardware token, or in a signing service
- the public key is distributed as part of the certificate
- Windows signing usually consumes a `.pfx` file that contains the certificate and the private key

A self-generated certificate is only suitable for internal testing. External users will still get trust warnings until they install that certificate into their trusted certificate store.

## Can the public certificate be distributed separately?

Yes, for internal distribution you can ship the public certificate as a `.cer` or `.crt` file and install it on the target Windows machines. That does not expose the private key.

For a self-signed internal code-signing certificate, the usual setup is:

- keep the private key only on the signing machine or signing service
- distribute only the public certificate to client machines
- install the public certificate into `Trusted Root Certification Authorities`
- also install the signer certificate into `Trusted Publishers` if you want Windows to treat that publisher as trusted for internal deployment

This is acceptable for development labs, test benches, and managed internal systems. It is not a substitute for a publicly trusted CA-issued code-signing certificate when shipping software outside your organization.

## Recommended signing order

1. Build the application with PyInstaller.
2. Sign `dist/SonicControl/SonicControl.exe` and any extra shipped `.exe` or `.dll` files, including bundled tools such as `picotool.exe` and `arm-none-eabi-*.exe` if they are redistributed.
3. Build the installer with Inno Setup.
4. Sign `dist/SonicControlInstaller/SonicControlInstaller.exe`.

Signing both the application and the installer gives better results with SmartScreen and makes the individual executable remain signed even after extraction from the installer.

## Signing with a real certificate

On Windows, the usual tool is `signtool.exe` from the Windows SDK.

The `/f` argument must point to an existing certificate file on disk, typically a `.pfx`. In the examples below, `soniccontrol-signing.pfx` is a filename, not a certificate nickname or Windows certificate store entry.

```powershell
signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /f C:\secure\soniccontrol-signing.pfx /p <password> dist\SonicControl\SonicControl.exe

signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /f C:\secure\soniccontrol-signing.pfx /p <password> dist\SonicControlInstaller\SonicControlInstaller.exe
```

If your certificate lives in the Windows certificate store instead of a `.pfx` file, do not pass the store entry name to `/f`. Use store-based selection flags such as `/n`, `/sha1`, and `/s` instead.

If `signtool` reports `Store IsDiskFile() failed` with `0x80070003`, one of the file paths passed on the command line does not exist. For this project, check these first:

- the `.pfx` path passed to `/f`
- `dist\SonicControl\SonicControl.exe`
- `dist\SonicControlInstaller\SonicControlInstaller.exe`

Timestamping matters. Without it, the signature may become invalid once the certificate expires.

If you want Inno Setup to sign the installer automatically, define a sign tool in the Inno Setup compiler configuration and reference it from the setup file:

```ini
[Setup]
SignTool=mystandard
```

Inno Setup can also sign original source files when the corresponding file flags are used, but for this project the simpler starting point is to sign the PyInstaller output first and the final installer second.

## Creating a test key pair and certificate

On Windows, the most direct option is to create a self-signed code-signing certificate in the certificate store and then export it as a `.pfx` file.

```powershell
$cert = New-SelfSignedCertificate `
  -Type CodeSigningCert `
  -Subject "CN=SonicControl Test Signing" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -KeyAlgorithm RSA `
  -KeyLength 3072 `
  -HashAlgorithm SHA256

$password = ConvertTo-SecureString "choose-a-strong-password" -AsPlainText -Force

New-Item -ItemType Directory -Path "C:\secure" -Force | Out-Null

Export-PfxCertificate `
  -Cert $cert `
  -FilePath "C:\secure\soniccontrol-test-signing.pfx" `
  -Password $password

Export-Certificate `
  -Cert $cert `
  -FilePath "C:\secure\soniccontrol-test-signing.cer"
```

`Export-PfxCertificate` does not create missing parent directories. If you want to store the `.pfx` somewhere else, create that directory first or change `-FilePath` to an existing folder such as `$env:USERPROFILE\Documents\soniccontrol-test-signing.pfx`.

This gives you:

- `C:\secure\soniccontrol-test-signing.pfx`: certificate plus private key, used by `signtool /f`
- `C:\secure\soniccontrol-test-signing.cer`: public certificate only, used to trust the signer on other machines

If you prefer OpenSSL or need to generate the files outside the Windows certificate store, create and export them like this:

```powershell
openssl req -x509 -newkey rsa:3072 -sha256 -days 825 -nodes `
  -keyout soniccontrol-test-signing.key.pem `
  -out soniccontrol-test-signing.crt.pem `
  -subj "/CN=SonicControl Test Signing/"

openssl pkcs12 -export `
  -out soniccontrol-test-signing.pfx `
  -inkey soniccontrol-test-signing.key.pem `
  -in soniccontrol-test-signing.crt.pem
```

This produces:

- `soniccontrol-test-signing.key.pem`: the private key, keep it secret
- `soniccontrol-test-signing.crt.pem`: the public certificate
- `soniccontrol-test-signing.pfx`: bundle typically used by Windows signing tools

You can sign with that test certificate, but another machine will trust it only after importing the public certificate into the appropriate Windows certificate store.

If you want a Windows-friendly export for installation, convert it to `.cer`:

```powershell
openssl x509 -outform der -in soniccontrol-test-signing.crt.pem -out soniccontrol-test-signing.cer
```

For internal rollout, install that public certificate on client machines. A typical manual path is to import it into `Local Machine\Trusted Root Certification Authorities`, and for smoother publisher trust also into `Local Machine\Trusted Publishers`.

## What to sign in practice

For this repository, a pragmatic default is:

- always sign `SonicControl.exe`
- always sign `SonicControlInstaller.exe`
- sign `picotool.exe` if it is shipped with the application or installer
- sign `arm-none-eabi-*.exe` tools if they are shipped with the application or installer
- sign any other bundled tools only if they are shipped as separate executable files that users or the app launch directly

That keeps the release process simple while covering the binaries that Windows users actually execute.