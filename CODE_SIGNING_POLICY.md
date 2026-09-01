# Code Signing Policy

## 1. Purpose and Scope

This policy defines the digital signing rules applied to executable
deliverables of the Application: a Python desktop client packaged as a
standalone executable (via PyInstaller or equivalent, detected at
runtime through `sys.frozen`), embedding a local Flask server and a
`pywebview` interface.

It covers:
- the main Windows executable (`.exe`) and any installer built from it
  (`.msi` / Inno Setup or NSIS `.exe`);
- third-party binaries bundled under `bin/` (e.g. `UnRAR.exe`,
  `ffmpeg.exe`);
- build and CI/CD scripts and artifacts;
- any subsequent software update (the version-tracking mechanism /
  `app_version` embedded in backup manifests).

It does not cover dynamic application content served by Flask
(`index.html`, `script.js`, `style.css`), which is not signed but is
protected through build integrity controls (see §6).

## 2. Why We Sign

The Application:
- runs a local server and a `pywebview` window with a JS/Python bridge
  (a high attack surface if the executable is tampered with);
- stores third-party account credentials (Thingiverse, MakerWorld, etc.)
  AES-encrypted via `cryptography.hazmat`, with a locally stored key
  (`encryption.key`);
- connects to printers and MQTT brokers, sometimes with TLS verification
  disabled (`ssl.CERT_NONE`);
- may register itself to run at Windows startup via the registry key
  `Software\Microsoft\Windows\CurrentVersion\Run`.

An unsigned executable, or one signed with a compromised key, exposes
users to impersonation of the Application (a fake installer, a poisoned
update) capable of exfiltrating these credentials or gaining persistent
access to the machine. Code signing is therefore a baseline trust
control, not a formality.

## 3. Certificate Authority and Certificate Type

- **Required certificate**: a Code Signing Certificate issued by a
  public Certificate Authority (CA) trusted by the Microsoft Trusted
  Root Program (e.g. DigiCert, Sectigo, SSL.com).
- **Recommended level**: an **EV (Extended Validation)** certificate
  stored on a hardware token or a cloud HSM, to gain immediate
  SmartScreen reputation and prevent any export of the private key.
- If EV is not immediately feasible (budget/organizational constraints),
  an OV (Organization Validation) certificate is acceptable as a
  transitional measure, with a documented plan to move to EV.
- The certificate must be issued to the legal entity publishing the
  Application, never to an individual, unless operating as a duly
  declared sole proprietorship.

## 4. Private Key Storage and Protection

- The private key must **never** exist as an exportable file in plain
  form on a developer workstation or a CI runner.
- Storage is limited to: a hardware USB token (FIPS 140-2 Level 2
  minimum), a cloud HSM, or an on-demand signing service (e.g. Azure
  Trusted Signing, DigiCert KeyLocker, SignPath).
- No sharing of the key/physical token between multiple people without
  individual traceability (a named badge or a dedicated, logged service
  account).
- The token's password/PIN is managed through the organization's secrets
  manager, never stored in plaintext in a repository, ticket, or chat.
- Any machine with access to the signing token/HSM is dedicated to that
  purpose or strictly isolated (no free web browsing, no installation of
  unaudited third-party dependencies).

## 5. Signing Process

1. **Reproducible build**: the executable is built from a fixed Git tag,
   using a versioned build environment (locked dependencies as listed
   in `check_deps`/`REQUIRED_MODULES`).
2. **Pre-signing analysis**: multi-engine antivirus scan (e.g. a private
   VirusTotal submission) of the executable before signing, to avoid
   signing a binary already compromised through a malicious dependency.
3. **Signing**: performed only in a controlled CI/CD pipeline or by an
   authorized operator, never manually on an unaudited personal machine.
   Every signing request must be explicitly authorized by an **Approver**
   (see §8) before submission to the signing service; requests without
   Approver sign-off are rejected.
4. **Timestamping**: every signature includes an RFC 3161 timestamp
   token (from the CA's TSA server), so the signature remains valid
   after the certificate expires.
5. **Signing of bundled third-party binaries**: third-party executables
   redistributed under `bin/` (UnRAR, ffmpeg, etc.) are verified
   (SHA-256 fingerprint compared against the value published by the
   original vendor) before inclusion; they are not re-signed under the
   Application's identity, but their provenance is recorded in the build
   manifest.
6. **Post-signing verification**: the certificate chain and signature
   validity are systematically checked (`signtool verify /pa /v`) before
   any release is published.

## 6. Update Chain Integrity

- Each newly signed version must correspond to an incremented, tracked
  `app_version`, consistent with the value recorded in the Application's
  backup manifests.
- Every update release must ship with: the signed executable, its
  SHA-256 fingerprint published separately (official website / GitHub
  release), and release notes.
- If an automatic update mechanism is added in the future, it must
  verify the Authenticode signature of the downloaded executable before
  replacing the installed binary, and must reject any update that is
  unsigned or signed by a certificate different from the one already
  trusted.
- Distribution channels (website, GitHub releases) must be served over
  strict HTTPS; no update may be offered over a plaintext channel.

## 7. Compromise Response

If the private key or token is suspected to be compromised:
1. Immediately revoke the certificate with the CA.
2. Pull all builds signed with the compromised key from official
   distribution channels.
3. Publish a security advisory to users, including SHA-256 fingerprints
   of legitimate versions.
4. Re-issue a new certificate and rebuild the entire signing chain (no
   reuse of secrets that may have been exposed, including
   `encryption.key` if the build machine could have accessed it).
5. Document a post-incident review before resuming releases.

## 8. Roles and Responsibilities

This project follows a three-tier Author / Reviewer / Approver model.
No signing request is submitted without passing through all three
roles, and no single person may hold more than one role on the same
change.

| Role | Member(s) | Responsibility |
|---|---|---|
| **Author** | Stellio contributors / committers | Writes and commits source code changes; opens the pull request or tag that will eventually be built and signed. Authors cannot approve their own signing requests. |
| **Reviewer** | Stellio maintainer(s) | Reviews the proposed changes (code review) before they are merged, checking for correctness and absence of malicious or unintended behavior. |
| **Approver** | Project publisher / lead maintainer | Gives final sign-off on the release candidate and explicitly approves the signing request submitted to the signing service (e.g. SignPath). Only Approvers can authorize a build to be signed. |

> **Current staffing note**: Stellio is currently maintained by a small
> team (in some cases a single maintainer acting in multiple
> capacities). Where the same individual temporarily holds more than
> one role, this is documented here and reviewed as the project and
> its contributor base grow; the long-term goal is to have Author,
> Reviewer, and Approver held by distinct people.

Every signing request must be traceable to: the Author(s) of the
underlying commits, the Reviewer(s) who approved the corresponding
pull request/merge, and the Approver who authorized the release for
signing.

## 9. Policy Review

This document is reviewed whenever the CA, the key storage mechanism, or
a target platform changes (e.g. adding macOS/Linux support), and at
every certificate renewal.