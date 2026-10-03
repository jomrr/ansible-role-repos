#!/usr/bin/env python3
"""Check role behavior against complete, supplied repository configurations."""

from __future__ import annotations

import argparse
import configparser
import json
import re
from pathlib import Path

SNAPSHOT = Path("/tmp/repos-original.json")
DIRECTORIES = {
    "apt": Path("/etc/apt"),
    "dnf": Path("/etc/yum.repos.d"),
    "dnf5": Path("/etc/yum.repos.d"),
    "zypper": Path("/etc/zypp/repos.d"),
}
PRESETS = {
    "AlmaLinux": ["epel"],
    "Fedora": [
        "rpmfusion-free",
        "rpmfusion-free-updates",
        "rpmfusion-nonfree",
        "rpmfusion-nonfree-updates",
    ],
    "openSUSE Leap": ["obs-devel-tools", "obs-filesystems"],
    "openSUSE Tumbleweed": ["obs-devel-tools", "obs-filesystems"],
}


def configurations(directory: Path) -> dict[str, str]:
    """Read all repository definitions, including ones the role does not own."""
    return {
        str(path): path.read_text(encoding="utf-8")
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".repo", ".list", ".sources"}
    }


def repository(path: Path, section: str) -> configparser.SectionProxy:
    """Parse native RPM repository data without expanding URL macros."""
    parser = configparser.ConfigParser(
        interpolation=None,
        defaults={"gpgcheck": "1"} if path.parent == DIRECTORIES["zypper"] else None,
    )
    parser.read(path, encoding="utf-8")
    return parser[section]


def toggle_only(original: str, current: str, section: str) -> bool:
    """Allow one enabled flag to change while retaining every other byte."""
    block = re.compile(r"(?ms)(^\[" + re.escape(section) + r"\]\n)(.*?)(?=^\[|\Z)")

    def normalize(match: re.Match[str]) -> str:
        return match[1] + re.sub(r"(?m)^enabled\s*=.*$", "enabled=<selected>", match[2])

    return block.sub(normalize, original) == block.sub(normalize, current)


def selected_toggles(
    directory: Path, distribution: str, initial: bool
) -> dict[Path, tuple[str, bool]]:
    """Describe the exercised public switches independently of role variables."""
    toggles = {directory / "molecule-supplied.repo": ("molecule-supplied", initial)}
    if distribution == "AlmaLinux":
        toggles[directory / "almalinux-crb.repo"] = ("crb", False)
    elif distribution == "Fedora":
        toggles[directory / "fedora.repo"] = ("fedora", initial)
        toggles[directory / "fedora-updates-testing.repo"] = (
            "updates-testing",
            initial,
        )
    return toggles


def verify_definition(directory: Path, backend: str, phase: str) -> Path:
    """Verify role dispatch, update and removal through the resulting definition."""
    name = "molecule-repository"
    if backend == "apt":
        path = directory / "sources.list.d" / f"{name}.sources"
    else:
        path = directory / f"{name}.repo"
    if phase == "absent":
        assert not path.exists(), f"Explicitly removed repository remains: {path}"
        return path
    expected_url = f"file:///tmp/repos-fixture-{'v1' if phase == 'initial' else 'v2'}"
    if backend == "apt":
        fields = dict(
            line.split(": ", 1)
            for line in path.read_text().splitlines()
            if ": " in line
        )
        assert fields["URIs"] == expected_url, fields
        assert fields["Enabled"] == "no", fields
        assert fields["Suites"] == "./", fields
    else:
        if backend == "zypper":
            expected_url = expected_url.replace("file:///", "file:/")
        data = repository(path, name)
        assert data["baseurl"].rstrip("/") == expected_url, dict(data)
        assert not data.getboolean("enabled"), dict(data)
        assert data.getboolean("gpgcheck"), dict(data)
    return path


def verify_presets(
    directory: Path, distribution: str, phase: str, version: str
) -> set[Path]:
    """Check every selected distribution preset, including its disabled state."""
    paths = set()
    for name in PRESETS.get(distribution, []):
        path = directory / f"{name}.repo"
        data = repository(path, name)
        assert data.getboolean("enabled") == (phase == "initial"), dict(data)
        assert data.getboolean("gpgcheck"), dict(data)
        if name.startswith("obs-"):
            assert data["baseurl"].startswith(
                "https://download.opensuse.org/repositories/"
            ), dict(data)
            target = (
                version if distribution == "openSUSE Leap" else "openSUSE_Tumbleweed"
            )
            assert data["baseurl"].rstrip("/").endswith("/" + target), dict(data)
        else:
            assert data["metalink"].startswith("https://mirrors."), dict(data)
            assert data["gpgkey"].startswith("https://"), dict(data)
        paths.add(path)
    return paths


def verify(backend: str, distribution: str, phase: str, version: str) -> None:
    """Assert only requested definitions and enabled flags changed."""
    directory = DIRECTORIES[backend]
    current = configurations(directory)
    if phase == "snapshot":
        SNAPSHOT.write_text(json.dumps(current), encoding="utf-8")
        return
    original = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if phase == "empty":
        assert original == current, "Empty role inputs changed repository configuration"
        return
    managed = {verify_definition(directory, backend, phase)} | verify_presets(
        directory, distribution, phase, version
    )
    toggles = (
        {}
        if backend == "apt"
        else selected_toggles(directory, distribution, phase == "initial")
    )
    for path, (section, enabled) in toggles.items():
        assert repository(path, section).getboolean("enabled") == enabled, str(path)
        assert toggle_only(original[str(path)], current[str(path)], section), str(path)
    for filename, content in original.items():
        if Path(filename) not in toggles and Path(filename) not in managed:
            assert current.get(filename) == content, (
                f"Unlisted configuration changed: {filename}"
            )
    added = set(current) - set(original)
    assert added <= {str(path) for path in managed}, (
        f"Unexpected repository files: {added}"
    )


def main() -> None:
    """Run a phase against the current managed host."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase", choices=["snapshot", "empty", "initial", "changed", "absent"]
    )
    parser.add_argument("backend", choices=list(DIRECTORIES))
    parser.add_argument("distribution")
    parser.add_argument("version")
    args = parser.parse_args()
    verify(args.backend, args.distribution, args.phase, args.version)
    print(
        f"Repository verification passed: {args.phase} on {args.distribution} ({args.backend})"
    )


if __name__ == "__main__":
    main()
