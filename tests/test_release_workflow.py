"""Exercise managed release publication without contacting GitHub."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def release_workflow():
    return yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())


def test_version_manifest_matches_application():
    from zpa import __version__

    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text())
    assert manifest["."] == __version__


@pytest.mark.parametrize("fail_upload", [False, True])
def test_managed_release_preserves_changelog_and_requires_upload(tmp_path, fail_upload):
    if os.name == "nt":
        bash = Path(os.environ.get("ProgramFiles", "")) / "Git/bin/bash.exe"
        if not bash.is_file():
            pytest.skip("Git Bash is required for the release shell test")
        executable = str(bash)
    else:
        executable = shutil.which("bash")
        if not executable:
            pytest.skip("Bash is required for the release shell test")

    steps = release_workflow()["jobs"]["publish"]["steps"]
    script = next(step["run"] for step in steps if step.get("name") == "Create release")
    mock = """
    gh() {
      printf '%s %s\\n' "$1" "$2" >> calls.log
      case "$1 $2" in
        'release view') printf '## Bug Fixes\\nExisting commit changelog\\n' ;;
        'release upload') if [ "$FAIL_UPLOAD" = "true" ]; then return 1; fi ;;
      esac
    }
    """
    result = subprocess.run(  # noqa: S603
        [executable, "-e", "-c", mock + script],
        cwd=tmp_path,
        env={
            **os.environ,
            "TAG": "v2.0.1",
            "SIGNED": "false",
            "MANAGED_RELEASE": "true",
            "GITHUB_REPOSITORY": "example/zpa",
            "FAIL_UPLOAD": str(fail_upload).lower(),
        },
        capture_output=True,
        text=True,
    )
    notes = (tmp_path / "release-notes.md").read_text()
    assert "Existing commit changelog" in notes
    assert "This release is unsigned" in notes
    calls = (tmp_path / "calls.log").read_text().splitlines()
    assert calls[:2] == ["release view", "release upload"]
    if fail_upload:
        assert result.returncode != 0
        assert "release edit" not in calls
    else:
        assert result.returncode == 0, result.stderr
        assert calls[-1] == "release edit"
