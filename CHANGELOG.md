# Changelog

Future entries are generated from Conventional Commits by release-please.

## [1.0.1](https://github.com/bigmars86/ZPA/compare/v1.0.0...v1.0.1) (2026-10-12)


### Dependencies

* bump pyinstaller ([4d9c6ad](https://github.com/bigmars86/ZPA/commit/4d9c6adafcc9c2a3dd4d3eb44155d035728d6779))

## 1.0.0 (2026-10-11)

### Features

- Initial public release of Zoom Poll Analyzer.
- Retrieve completed meeting poll responses and participant information.
- Group answered, excluded, and unanswered rows with a separate total row.
- Export CSV, JSON, YAML, and XML or email reports through a configured SMTP provider.
- English, German, and Greek interfaces, configurable themes, and automatic INI creation.

### Security And Reliability

- Verified SMTP certificate chains and hostnames, escaped email HTML, and bounded Zoom requests.
- Central token expiry handling and one authentication retry after HTTP 401.
- Explicit direct, system-autodetect, and manual proxy modes.
- Automated tests, lint, full-history secret scanning, and Windows executable builds.
- Prepared SignPath Foundation integration; signing requires approval and configuration.
