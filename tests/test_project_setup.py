from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_ci_workflow_exists():
    assert (ROOT / ".github" / "workflows" / "ci.yml").is_file()


def test_release_workflow_exists():
    assert (ROOT / ".github" / "workflows" / "release.yml").is_file()


def test_dockerfile_exists():
    assert (ROOT / "Dockerfile").is_file()


def test_compose_file_exists():
    assert (ROOT / "docker-compose.yml").is_file()


def test_requirements_pin_versions():
    lines = (ROOT / "requirements.txt").read_text().splitlines()
    packages = [line for line in lines if line.strip() and not line.startswith("#")]
    assert packages
    assert all("==" in line for line in packages)
