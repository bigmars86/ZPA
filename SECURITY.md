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

## Known limitations

The current beta is not certified for production use. Automated offline regressions cover
email HTML escaping, verified SMTP TLS, proxy modes, Zoom request timeouts, token expiry,
one bounded authentication retry, and response-report selection. Live Zoom permissions,
provider-specific SMTP setup, and end-to-end report accuracy still require acceptance testing.

SMTP uses `ssl.create_default_context()` for both STARTTLS and implicit TLS. It verifies
the certificate chain against trusted CAs and matches the certificate to the configured
SMTP hostname before sending credentials. Expired, self-signed/untrusted, or mismatched
certificates are rejected; there is no insecure fallback. Use your provider's documented
hostname and a complete certificate chain. Private CAs must be installed in the system
trust store, or supplied via Python's `SSL_CERT_FILE` / `SSL_CERT_DIR` configuration.

New configurations use no proxy. Enable autodetection to resolve the system proxy, or
disable it and set `proxy` for an explicit proxy. Blank/direct mode ignores environment
proxies, including when performing the connection check.

Zoom requests have a 30-second socket timeout; tokens refresh before their reported expiry.
Only 401 responses receive one retry after refresh. Other failures are shown to the user,
not silently converted to missing poll answers. Report access requires the appropriate
Zoom account permissions. The timeout applies to each network operation, not an entire
paginated meeting download.

A successful build or code-signing certificate is not proof of application correctness.

## Verifying release downloads

Every release asset is built by GitHub Actions and has a signed build provenance attestation:

```bash
gh attestation verify ZPA.exe --repo bigmars86/ZPA
```
