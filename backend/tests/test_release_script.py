import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RELEASE_SCRIPT = PROJECT_ROOT / "release.sh"


def test_release_script_has_valid_bash_syntax():
    result = subprocess.run(
        ["bash", "-n", str(RELEASE_SCRIPT)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_release_help_does_not_create_a_release():
    result = subprocess.run(
        ["bash", str(RELEASE_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--push" in result.stdout
    assert "1.0.1" in result.stdout


def test_release_script_can_be_sourced_without_running_main():
    result = subprocess.run(
        ["bash", "-c", f'source "{RELEASE_SCRIPT}"; declare -F main parse_args'],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "parse_args" in result.stdout
