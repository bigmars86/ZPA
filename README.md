# ZPA (Zoom Poll Analyzer)

[![CI](https://img.shields.io/github/actions/workflow/status/bigmars86/ZPA/ci.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/bigmars86/ZPA/actions/workflows/ci.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/bigmars86/ZPA/codeql.yml?branch=main&label=CodeQL)](https://github.com/bigmars86/ZPA/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/bigmars86/ZPA)](https://github.com/bigmars86/ZPA/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/bigmars86/ZPA/total)](https://github.com/bigmars86/ZPA/releases)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Analyze Zoom meeting polls, review participant responses, and export or email the results.

ZPA is a desktop application for meeting organizers who need a clear view of poll results.
It retrieves data from Zoom, brings responses and participant information together, and
helps organizers prepare reports without manually copying answers between systems.

ZPA is currently beta software, not production-certified. Review the
[known security limitations](SECURITY.md#known-limitations) before using it with sensitive data.

## Download

**[Download ZPA.exe](https://github.com/bigmars86/ZPA/releases/latest/download/ZPA.exe)**
or browse [all releases](https://github.com/bigmars86/ZPA/releases).
The Windows executable includes Python and its dependencies; no installation is required.
Place it in a writable folder and start it. To uninstall, remove the executable and its
configuration file after backing up any settings you need.

Each release includes a SHA-256 checksum and build provenance that can be verified with:

```bash
gh attestation verify ZPA.exe --repo bigmars86/ZPA
```

Signing status is stated in each release. Until SignPath Foundation approval and setup are
complete, releases are unsigned and Windows may show an unknown-publisher warning.
See the [code signing policy](#code-signing-policy).

## Features

- Retrieve polls and participants from completed Zoom meetings and select past meeting instances.
- Review participant responses, exclusions, anonymous responses, and numeric totals.
- Export CSV, JSON, YAML, or XML, or email results using your SMTP server.
- English, German, and Greek interfaces with system, light, dark, and Solarized themes.
- Configurable fonts, network proxy settings, and poll question filtering.

## Zoom Setup

1. Create a **Server-to-Server OAuth** app in the [Zoom Marketplace](https://marketplace.zoom.us/).
2. Configure permissions for meeting details, past meeting participants, meeting instances,
   and poll reports. Use the read/admin scopes required by the endpoints in the
   [Zoom API documentation](https://developers.zoom.us/docs/api/); scope names and availability
   depend on your account and Zoom's current scope model.
3. Activate the app and obtain its **Account ID**, **Client ID**, and **Client Secret**.
4. Enter these in ZPA's **File > Settings** and test the connection.

Your Zoom account must have access to the meeting and its reports. Report APIs generally
require a paid account and appropriate host/admin permissions. The meeting must have ended
and contain recorded poll responses.

## Usage

1. Configure your Zoom credentials in **File > Settings**.
2. Enter a meeting ID and, when needed, select a past meeting instance.
3. Load the data and review the responses and totals.
4. Export the results or send them to your configured email recipients.

## Configuration

If `zpa.ini` is missing, the app creates it automatically with the defaults below.
No template download or manual file creation is necessary. Existing configuration files
are loaded without being overwritten on startup; settings are saved when you change them.

- **Windows executable:** `zpa.ini` next to `ZPA.exe`.
- **Source checkout:** `zpa.ini` in the project root.
- **Custom path:** `zpa --ini-file /path/to/zpa.ini`; missing parent folders are created too.

Configure settings through **File > Settings**, or edit the INI while the app is closed.
Credentials and SMTP passwords are stored in **plain text**. Protect the file with filesystem
permissions and never share it. All `*.ini` files are git-ignored. Exported participant data
also needs appropriate privacy protection. See [SECURITY.md](SECURITY.md).

| Section | Setting | Default | Purpose |
| --- | --- | --- | --- |
| Zoom | `account_id` | empty | Server-to-Server OAuth account ID. |
| Zoom | `client_id` | empty | OAuth client ID. |
| Zoom | `client_secret` | empty | OAuth client secret; keep private. |
| Zoom | `meeting_id` | empty | Meeting to analyze. |
| UI | `language` | `en` | Interface language: `en`, `de`, or `el`. |
| UI | `theme` | `system` | `system`, `light`, `dark`, `solarized-light`, or `solarized-dark`. |
| UI | `max_height` | `600` | Window height setting in pixels. |
| UI | `font_size` | `8` | Table font size in points. |
| UI | `ui_font_size` | `9` | Interface font size in points. |
| Application | `debug` | `false` | Diagnostic output; may include participant data. |
| Application | `exclude_names` | empty | Comma-separated participant names to exclude. |
| Application | `poll_question` | empty | Poll question text filter. |
| Application | `ini_location` | current INI path | Location recorded by the app; use `--ini-file` to choose it at startup. |
| Export | `format` | `csv` | `csv`, `json`, `yaml`, or `xml`. |
| Export | `separator` | `;` | CSV separator; semicolon works well with many Excel locales. |
| Network | `proxy` | empty | Explicit HTTP/HTTPS proxy URL when autodetection is disabled; empty means direct. |
| Network | `proxy_autodetect` | `false` | Enable to use system/environment/PAC proxy settings instead of the manual value. |
| Email | `smtp_server` | empty | SMTP hostname; email remains unconfigured by default. |
| Email | `smtp_port` | `587` | SMTP submission port. |
| Email | `smtp_username` | empty | SMTP login and sender address. |
| Email | `smtp_password` | empty | SMTP password; keep private. |
| Email | `smtp_use_tls` | `true` | Use STARTTLS; `false` selects implicit TLS (SMTP_SSL), not plaintext SMTP. |
| Email | `recipients` | empty | Comma-separated recipient email addresses. |

## Run From Source

Python 3.9+ is required; Python 3.13 is recommended for development. Python 3.9 is
retained for compatibility but is no longer maintained upstream; use a supported Python
release for deployments.

```bash
git clone https://github.com/bigmars86/ZPA.git
cd ZPA
pip install uv
uv sync --locked
uv run zpa
```

Alternatively, install with `pip install -e .` and run `zpa` or `python -m zpa`.
For diagnostic output, run `uv run python -m zpa` from a terminal.

## Development

```bash
uv sync --locked
uv run pre-commit install --overwrite
uv run pre-commit run --all-files
uv run pytest
uv sync --locked --group build
uv run python scripts/build_executable.py
```

Build output is written to `dist/`. Release builds never bundle your local INI or credentials.
CI checks lint, formatting, secrets, tests, and Windows builds. CodeQL and dependency review
provide additional security checks; Dependabot maintains dependency and action updates.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [EXECUTABLE_BUILD.md](EXECUTABLE_BUILD.md).

Conventional-commit versioning is prepared in the Versioning workflow, disabled by default.
When enabled, it proposes reviewed version/changelog PRs and publishes releases only after
the executable build succeeds. See [the release process](CONTRIBUTING.md#releasing-maintainers).

## Code Signing Policy

**Status: integration prepared; Foundation approval and signing configuration pending.**
The following attribution applies only after approval and to releases marked as signed:

Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by
[SignPath Foundation](https://signpath.org/).

- Author, reviewer, and signing approver: [Marcel Vilas (@bigmars86)](https://github.com/bigmars86).
- External contributions require maintainer review. Each Foundation signing request requires
  manual approval, and maintainers must use multi-factor authentication on GitHub and SignPath.
- Only Windows binaries built from this repository on GitHub-hosted runners are submitted.
  The workflow verifies the returned Authenticode signature before publishing, then calculates
  the checksum and provenance for the final executable. Signing failures stop publication.
- The app contacts Zoom to authenticate and retrieve requested meeting data, and the user's
  configured SMTP server to send requested emails. Connection checks also make network requests.
  Operating-system proxy settings may route these requests through a proxy. There is no
  application telemetry. Zoom's [privacy policy](https://explore.zoom.us/en/privacy/) applies
  to its services; your email and proxy providers' policies apply when you use those services.

### Maintainer Setup

After approval, install the [SignPath GitHub App](https://github.com/apps/signpath) for this
repository and configure the project, artifact configuration, and manual-approval signing
policy in SignPath. The unsigned workflow artifact is a ZIP containing `ZPA.exe`; configure
that file as the signing target and enforce its product name (`Zoom Poll Analyzer`) and version
metadata. Do not sign bundled third-party binaries separately with this project's certificate.

Configure these in **GitHub Settings > Secrets and variables > Actions**:

| Kind | Name | Value |
| --- | --- | --- |
| Secret | `SIGNPATH_API_TOKEN` | SignPath submitter token. |
| Variable | `SIGNPATH_ORGANIZATION_ID` | Organization ID assigned by SignPath. |
| Variable | `SIGNPATH_PROJECT_SLUG` | Project slug assigned/configured in SignPath. |
| Variable | `SIGNPATH_SIGNING_POLICY_SLUG` | Foundation manual-approval signing policy slug. |
| Variable | `SIGNPATH_ENABLED` | Set to `true` only after all setup is complete. |

Without `SIGNPATH_ENABLED=true`, bootstrap releases remain explicitly unsigned so the project
can establish a public release and reputation before applying. Once enabled, there is no
unsigned fallback if signing fails. Approve signing requests within the workflow's one-hour
signing wait window.

## License

Copyright (C) 2024-2026 Marcel Vilas.

ZPA is licensed under the [GNU General Public License version 3 only](LICENSE)
(`GPL-3.0-only`). Distributing modified versions requires making corresponding source
available under GPL v3. Commercial use is permitted. There is no warranty.

ZPA is not affiliated with or endorsed by Zoom Video Communications, Inc.

## Support And Contributions

[Report a bug or request a feature](https://github.com/bigmars86/ZPA/issues).
Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request and
[SECURITY.md](SECURITY.md) for private vulnerability reporting.
