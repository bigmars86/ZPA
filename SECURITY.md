# Security Policy

## Supported versions

Security fixes are only provided for the [latest release](https://github.com/bigmars86/ZPA/releases/latest).

## Reporting a vulnerability

Please **do not** open a public issue for security problems.
Report them privately via [GitHub Security Advisories](https://github.com/bigmars86/ZPA/security/advisories/new)
("Report a vulnerability" on the *Security* tab). You will get a response as soon as possible;
once a fix is released, the advisory will be published with credit to the reporter (unless you prefer otherwise).

## Credentials and personal data

ZPA stores the Zoom API credentials and the SMTP password in **plain text** in `zpa.ini`
(next to `ZPA.exe`, or in the project root when running from source).

- Keep `zpa.ini` private and protected by file-system permissions. It is git-ignored - never commit it
  and never attach it to issues.
- Do not build a distributable exe with `--include-ini` from an INI that contains credentials.
- Poll exports contain participant names; treat them as personal data.
- If credentials were exposed, rotate the Client Secret in the Zoom Marketplace and change the SMTP
  password immediately.

## Verifying release downloads

Every release asset is built by GitHub Actions and has a signed build provenance attestation:

```bash
gh attestation verify ZPA.exe --repo bigmars86/ZPA
```
