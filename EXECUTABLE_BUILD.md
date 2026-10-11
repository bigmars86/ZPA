# Building ZPA

## Windows Build

Run from a source checkout with Python and uv installed:

```bash
uv sync --locked --group build
uv run python scripts/build_executable.py --platform windows
```

The script generates the PyInstaller specification and version resource in `specs/`,
uses `build/` for intermediate files, and writes the standalone executable to `dist/ZPA.exe`.
Those directories are git-ignored. Generated absolute build paths are local artifacts,
not machine-specific paths embedded in the source repository.

The Windows version resource is derived from `__version__` in `src/zpa/__init__.py`.
The executable bundles themes, translations, and icons from `src/zpa/resources/`.
No configuration file is bundled by default: the app creates `zpa.ini` on first launch.

## Options

```bash
uv run python scripts/build_executable.py --clean
uv run python scripts/build_executable.py --include-ini /path/to/sanitized/zpa.ini
```

`--clean` removes `build/`, `dist/`, and generated `specs/` files.
`--include-ini` optionally takes a path (default `zpa.ini`). **Never distribute a build
containing your credentials or participant data.** Official releases do not use this option.

Building for another platform requires running on that platform; the script does not
cross-compile. Only Windows executable builds are covered by the current release workflow.
The macOS branch references a missing `app.icns` and is not release-ready; universal
Intel/Apple Silicon builds are not currently configured or supported.

## Automated Versioning And Releases

The prepared [Versioning workflow](.github/workflows/versioning.yml) uses release-please
to interpret Conventional Commits, propose version/changelog PRs, and create draft releases.
It remains disabled until `RELEASE_AUTOMATION_ENABLED=true` is configured in repository
variables. See [CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers) for commit prefixes,
PR permissions, CI behavior with bot-created PRs, and the release approval process.

Merging a release PR directly calls the [Release workflow](.github/workflows/release.yml):

1. Check out the release tag and confirm it matches the application version.
2. Install locked build dependencies and build on a GitHub-hosted Windows runner.
3. If enabled, submit the unsigned artifact to SignPath and verify its returned signature.
4. Generate the final executable's SHA-256 checksum and build provenance attestation.
5. Upload the assets and publish the draft, preserving its conventional-commit changelog.

Signing errors stop publication. SignPath requires approval and setup before enabling it;
see the README's [code signing policy](README.md#code-signing-policy).

To retry a failed managed release, manually run the Release workflow for its existing tag
with `managed-release=true`. Manual `v*` tags are also supported for unmanaged releases;
they must match the application version and use GitHub-generated notes rather than the
release-please changelog.

## Verification

```bash
uv run pytest
uv run pre-commit run --all-files
gh attestation verify ZPA.exe --repo bigmars86/ZPA
```

Check the downloaded executable's SHA-256 against `ZPA.exe.sha256` and read the signing
status in its release notes. Provenance attestation is not Authenticode signing and neither
is proof of application correctness or production readiness. See [SECURITY.md](SECURITY.md)
for current limitations.
