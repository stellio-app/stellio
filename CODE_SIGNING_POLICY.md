# Code Signing Policy

_Last updated: 18 October 2026_

> **Current status in one sentence**: the Windows installer and the Linux
> AppImage are **not code-signed** yet; every release file is published with a
> SHA-256 checksum, and the built-in updater verifies it. Code signing is a
> goal (see §6), not something this project does today.

## 1. Purpose and Scope

This policy describes how the executable deliverables of Stellio are
built, protected and verified. Stellio is a Python desktop client packaged
as a standalone executable (PyInstaller, detected at runtime through
`sys.frozen`), embedding a local Flask server and a `pywebview` interface.

It covers:
- the Windows installer (Inno Setup `.exe`) and the update patch (`.zip`);
- the macOS `.dmg` builds (arm64 and x86_64);
- the Linux AppImage;
- third-party binaries bundled under `bin/` (`ffmpeg`, `UnRAR`);
- the build and release workflow (`.github/workflows/build-and-sign.yml`).

It does not cover the web assets served by Flask (`index.html`,
`script.js`, `style.css`), which are shipped inside the same builds.

## 2. Current Status by Platform

| Platform | Deliverable | Signature today |
|---|---|---|
| Windows | Installer `.exe` (artifact `stellio-installer-unsigned`) and update patch `.zip` | **Not signed.** No certificate and no signing service is configured; Windows SmartScreen may show a warning. |
| macOS | `.dmg` (arm64 / x86_64) | Signed with an Apple Developer ID certificate when the repository secrets `MACOS_CERTIFICATE`, `MACOS_CERTIFICATE_PWD` and `MACOS_SIGNING_IDENTITY` are set, otherwise **ad-hoc** only. The workflow has **no notarization step**, so Gatekeeper may still warn. |
| Linux | AppImage | **Not signed.** |

## 3. Integrity Measures in Place Today

- **Checksums**: the workflow produces a `.sha256` file for the Windows
  installer, the update patch `.zip`, each macOS `.dmg` and the Linux
  AppImage, and publishes it next to the file in the GitHub release.
- **Updater verification**: the built-in updater looks for the published
  checksum of the asset it downloads. When one exists, the downloaded file is
  hashed, and the file is deleted and the update cancelled on any mismatch.
  When no checksum is published, integrity relies on HTTPS only (this is
  logged).
- **Pinned third-party binaries**: `ffmpeg` is downloaded from a fixed,
  dated release (Windows and Linux: BtbN `autobuild-2026-10-18-13-01`;
  macOS: eugeneware `b6.0`), and the build fails if its SHA-256 does not
  match the value written in the workflow. These hashes were computed on the
  downloaded files, not copied from the vendor's checksum list.
  `UnRAR.exe` (Windows): the SHA-256 of the file extracted from RARLAB's
  `unrarw64.exe` is pinned (version 7.22.0, Authenticode-signed by win.rar
  GmbH), and the build fails if it differs; the signature status is also
  printed in the build log. `UnRAR` (macOS): the workflow compares the
  archive's SHA-256 with a pinned value as soon as one is set; until then it
  prints the hash in the build log as a warning. On Linux, `unrar` comes
  from the Ubuntu repository and is authenticated by apt's repository
  signature.
- **Controlled publication**: a release is only created when
  `CURRENT_VERSION` in `main.py` changes, and it is created as a **draft**
  that the maintainer reviews and publishes manually.
- **Transport**: distribution channels (GitHub releases, the project
  website) are served over HTTPS.

## 4. Known Limitations

- The Windows installer and the update patch are not signed; the updater
  performs **no Authenticode verification**.
- The published checksum comes from the same release as the file. It
  detects corruption and tampering in transit, but it does **not** protect
  against a compromise of the GitHub account or repository.
- There is no antivirus scan in the CI pipeline.
- `requirements.txt` lists package names without pinned versions, so builds
  are not fully reproducible.
- RARLAB publishes new UnRAR versions at an unchanged URL, so the pinned
  `UnRAR.exe` hash makes the Windows build fail on purpose after each RARLAB
  release until it has been verified and the value updated.
- BtbN removes old `autobuild-*` tags after a few weeks, so the pinned
  `ffmpeg` URL for Windows and Linux will eventually need to be updated.
  To update it: pick a new tag, download the file, compute its SHA-256
  yourself, and change both values in the workflow.

## 5. How to Verify a Download

Compare the SHA-256 of the file with the content of its `.sha256` file:

- Windows (PowerShell): `Get-FileHash -Algorithm SHA256 .\Stellio-Setup-<version>.exe`
- Linux: `sha256sum Stellio-v<version>-linux-x86_64.AppImage`
- macOS: `shasum -a 256 Stellio-v<version>-macOS-<arch>.dmg`

## 6. Target Policy When Signing Is Introduced

This section describes the rules the project intends to follow once Windows
signing is set up. It is not in force today.

- **Certificate**: a code signing certificate issued by a public CA trusted
  by the Microsoft Trusted Root Program; EV recommended (immediate
  SmartScreen reputation), OV acceptable as a transitional measure.
- **Key protection**: the private key never exists as an exportable file on a
  workstation or CI runner. Storage is limited to a hardware token
  (FIPS 140-2 Level 2 minimum), a cloud HSM, or a signing service (e.g.
  SignPath, Azure Trusted Signing, DigiCert KeyLocker). Secrets and PINs live
  in a secrets manager, never in a repository, ticket or chat.
- **Process**: signing only in the CI pipeline from a fixed Git tag, with
  explicit approval before each signing request; an RFC 3161 timestamp on
  every signature; `signtool verify /pa /v` before any release is published.
- **Updater**: once installers are signed, the updater must verify the
  Authenticode signature of the downloaded file before replacing the
  installed binary, and reject any update that is unsigned or signed by a
  different certificate than the one already trusted.
- **Roles**: Author (writes the change), Reviewer (reviews it before merge),
  Approver (authorizes the release for signing). Stellio is currently
  maintained by a single person who holds all three roles; the long-term goal
  is to have them held by distinct people.

## 7. Compromise Response

If a build, a release, the GitHub account or a signing secret (such as the
macOS certificate) is suspected to be compromised:
1. Remove the affected releases from the official distribution channels.
2. Revoke or rotate every exposed secret (macOS certificate, tokens, and any
   signing certificate once one exists).
3. Publish a security advisory with the SHA-256 checksums of the legitimate
   versions.
4. Rebuild from a clean state; do not reuse secrets that may have been
   exposed, including `encryption.key` if the build machine could have
   accessed it.
5. Document a post-incident review before resuming releases.

## 8. Policy Review

This document is reviewed whenever a signing mechanism is added or changed,
a target platform changes, the build workflow changes, or a pinned
third-party binary is updated.
