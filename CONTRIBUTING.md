# Contributing to ZPA

Thanks for your interest in improving ZPA! Bug reports, ideas and pull requests are welcome.

## Development setup

Requirements: Python 3.9+ (3.13 recommended), [uv](https://docs.astral.sh/uv/) and Git.

```bash
git clone https://github.com/bigmars86/ZPA.git
cd ZPA
uv sync                      # creates .venv with the app and the dev tools
uv run pre-commit install --overwrite # run the checks automatically on every commit
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

Release automation is prepared but disabled until the maintainer sets the repository variable
`RELEASE_AUTOMATION_ENABLED=true`. This is not a production-readiness certification.
The release manifest starts from the initial `1.0.0` release; do not reset published versions
or tags without a separately approved history migration.

Use [Conventional Commits](https://www.conventionalcommits.org/) for commits or squash-merge
PR titles:

- `fix: ...` increments the patch version.
- `feat: ...` increments the minor version.
- `feat!: ...` or a `BREAKING CHANGE:` footer increments the major version.
- `docs:`, `refactor:`, `test:`, `ci:`, `build:`, `deps:`, `chore:`, and `revert:` are included
  in the generated changelog; not every maintenance-only commit triggers a new release.

1. Enable **Allow GitHub Actions to create and approve pull requests** in repository Actions
   settings. No automatic PR approval or merge is configured here.
2. The [Versioning workflow](.github/workflows/versioning.yml) opens/updates a release PR
   containing the version bump in `src/zpa/__init__.py`, the manifest, and a generated
   `CHANGELOG.md` with commit links. Existing non-conventional commits are not retroactively
   rewritten or guaranteed to appear in these notes.
3. Review and test the release PR, then merge it. Release-please creates a tag and a **draft**
   GitHub release and directly calls the [Release workflow](.github/workflows/release.yml)
   using the exact tag. This does not depend on token-created tag events triggering workflows.
4. The release workflow checks the version, builds `ZPA.exe`, optionally signs it with
   SignPath, creates the checksum/provenance, uploads the assets, and publishes the draft.
   The release-please commit changelog is retained and download/signing notes are appended.
   A failed build or signing request leaves the release as a draft.

The built-in `GITHUB_TOKEN` can run versioning and call the release build, but its bot-created
PRs do not trigger CI automatically. Close/reopen the release PR as a maintainer to trigger
CI, or configure `RELEASE_PLEASE_TOKEN` with a fine-grained token limited to this repository
(contents, issues, and pull requests write access). Never put this token in a tracked file.

For recovery, manually run the Release workflow with the existing tag and
`managed-release=true`. Manual tags remain supported, but normally let release-please
manage both the tag and version. See the README's SignPath setup before enabling signing.

## License

By contributing, you agree that your contributions are licensed under the
[GNU General Public License v3.0 only](LICENSE).
