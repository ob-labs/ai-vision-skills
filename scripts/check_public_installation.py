#!/usr/bin/env python3
"""Exercise the README's public installation path from a checkout of main with Python 3.12+."""

import io
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import tempfile

from check_installation import check_copied_resources, check_discovered_names


REPOSITORY = "ob-labs/ai-vision-skills"
MAIN_REF = "refs/heads/main"
INSTALL_NAMES = ("aivision-deploy", "aivision-quickstart")


def anonymous_environment(home: Path) -> dict[str, str]:
    # Start with an allowlist so credential, agent, proxy, and npm config
    # overrides from the runner cannot affect the public installation.
    (home / "tmp").mkdir(parents=True)
    return {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "TMPDIR": str(home / "tmp"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "NPM_CONFIG_CACHE": str(home / ".npm"),
        "NPM_CONFIG_USERCONFIG": str(home / ".npmrc"),
        "NPM_CONFIG_GLOBALCONFIG": str(home / "npm-global.rc"),
        "NPM_CONFIG_PREFIX": str(home / "npm-prefix"),
        "NPM_CONFIG_REGISTRY": "https://registry.npmjs.org/",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "CI": "1",
        "DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "NO_COLOR": "1",
    }


def run(arguments: list[str], cwd: Path, environment: dict[str, str], timeout: int = 90) -> str:
    result = subprocess.run(
        arguments, cwd=cwd, env=environment, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(
            f"{shlex.join(arguments)} exited with {result.returncode}\n{result.stdout}{result.stderr}"
        )
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.stdout)


def require_public_main(expected: str, directory: Path, environment: dict[str, str]) -> None:
    reference = run(
        ["git", "ls-remote", "--exit-code", f"https://github.com/{REPOSITORY}.git", MAIN_REF],
        directory, environment, timeout=30,
    ).split()
    if reference != [expected, MAIN_REF]:
        raise RuntimeError(
            f"Public main does not match checked-out {expected} (ls-remote: {reference!r}). "
            "Run this check against the current main."
        )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="aivision-public-install-") as temporary:
        workspace = Path(temporary).resolve()
        environment = anonymous_environment(workspace / "home")
        expected = run(["git", "rev-parse", "HEAD"], root, environment, timeout=15).strip()
        require_public_main(expected, workspace, environment)

        # Compare with a snapshot of the checked-out commit, independent of
        # working-tree edits or untracked files when the check runs locally.
        snapshot = workspace / "expected"
        snapshot.mkdir()
        packed = subprocess.check_output(
            ["git", "archive", expected, "skills"], cwd=root, env=environment, timeout=30,
        )
        with tarfile.open(fileobj=io.BytesIO(packed)) as archive:
            archive.extractall(snapshot, filter="data")
        skills = snapshot / "skills"

        command = ["npx", "--yes", "skills"]
        version = run([*command, "--version"], workspace, environment).strip()
        print(f"Checking public main {expected} with skills {version}", flush=True)
        add = [*command, "add", REPOSITORY]
        listing = run([*add, "--list"], workspace, environment)
        discovered = set(re.findall(r"^│    ([a-z0-9][a-z0-9-]*)\s*$", listing, re.MULTILINE))
        check_discovered_names(discovered, {entry.parent.name for entry in skills.glob("*/SKILL.md")})

        for name in INSTALL_NAMES:
            project = workspace / name
            project.mkdir()
            run([*add, "--skill", name, "--agent", "codex", "--yes"], project, environment)

        # A moving default branch can return different snapshots across the
        # discovery and install calls. Treat that as an outdated run.
        require_public_main(expected, workspace, environment)
        print(f"PASS public discovery: {', '.join(sorted(discovered))}", flush=True)
        for name in INSTALL_NAMES:
            skill_directory = workspace / name / ".agents" / "skills"
            if {entry.name for entry in skill_directory.glob("*")} != {name}:
                raise ValueError(f"Expected only {name} under {skill_directory}")
            installed = skill_directory / name
            if not installed.resolve().is_relative_to(workspace):
                raise ValueError(f"Installed skill escapes the disposable workspace: {installed}")
            check_copied_resources(skills / name, installed)
            print(f"PASS public installation: {name} matches {expected}", flush=True)


if __name__ == "__main__":
    main()
