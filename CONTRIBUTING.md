# Contributing to ZPA

Thanks for your interest in improving ZPA! Bug reports, ideas and pull requests are welcome.

## Development setup

Requirements: Python 3.8+ (3.13 recommended), [uv](https://docs.astral.sh/uv/) and Git.

```bash
git clone https://github.com/bigmars86/ZPA.git
cd ZPA
uv sync                      # creates .venv with the app and the dev tools
uv run pre-commit install    # run the checks automatically on every commit
uv run zpa                   # start the application
```

On first start ZPA creates `zpa.ini` in the project root. It holds your credentials and is git-ignored -
keep it that way.

## Quality checks

| Check | Command |
| --- | --- |
| All pre-commit hooks: ruff lint + format, YAML/JSON/TOML checks, workflow security lint (zizmor), secret scan (gitleaks) | `uv run pre-commit run --all-files` |
| Tests | `uv run pytest` |
| Windows exe build | `uv sync --group build` and then `uv run python scripts/build_executable.py` |

CI runs the same checks on every pull request, plus a gitleaks scan of the full history,
CodeQL analysis, a dependency review and a test build of `ZPA.exe`.

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Keep changes focused and update the documentation where needed.
3. UI texts must exist in every translation file (`src/zpa/resources/translations/{en,de,el}.json`);
   the test suite checks this.
4. Never commit `zpa.ini`, credentials or exported poll results.
5. Open the pull request and fill in the checklist.

## Releasing (maintainers)

1. Bump `__version__` in `src/zpa/__init__.py` (the single source of the version) and merge to `main`.
2. Tag the release commit and push the tag:

   ```bash
   git tag v2.1.0
   git push origin v2.1.0
   ```

3. The [Release workflow](.github/workflows/release.yml) verifies that the tag matches `__version__`,
   builds `ZPA.exe`, creates a SHA-256 checksum and a build provenance attestation, and publishes the
   GitHub release with generated release notes. Tags with a suffix (e.g. `v2.1.0rc1`) become pre-releases.

## License

By contributing, you agree that your contributions are licensed under the
[GNU General Public License v3.0 or later](LICENSE).
