import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
START_SCRIPT = PROJECT_ROOT / "start.sh"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(START_SCRIPT), *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_start_script_has_valid_bash_syntax():
    result = subprocess.run(
        ["bash", "-n", str(START_SCRIPT)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_help_lists_supported_commands_without_starting_services():
    result = _run("help")
    assert result.returncode == 0
    assert "sync" in result.stdout
    assert "local" in result.stdout
    assert "dev" in result.stdout
    assert "docker" not in result.stdout


def test_unknown_command_returns_usage_error():
    result = _run("unknown")
    assert result.returncode == 2
    assert "Usage:" in result.stdout


def test_script_can_be_sourced_without_running_main():
    result = subprocess.run(
        ["bash", "-c", f'source "{START_SCRIPT}"; declare -F start_local main'],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "start_local" in result.stdout
    assert "main" in result.stdout


def test_health_checks_bypass_shell_proxy_settings():
    script = START_SCRIPT.read_text(encoding="utf-8")
    assert "curl --noproxy '*' -fsS" in script
