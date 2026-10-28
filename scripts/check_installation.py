#!/usr/bin/env python3
"""Use skills@1.7.4 to discover and independently copy the full catalog.

Requires Node >=22.20.0, the published package's engine requirement. Each
project installation lives in a separate TemporaryDirectory; neither HOME nor
CODEX_HOME is reassigned, and no global installation is requested.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile


SKILLS_VERSION = "1.7.4"
INITIAL_NAMES = {"aivision-deploy", "aivision-metric", "aivision-quickstart", "aivision-trace"}


def check_discovered_names(discovered: set[str], directories: set[str]) -> None:
    if discovered != directories or not INITIAL_NAMES <= discovered:
        raise ValueError(
            f"CLI-discovered Skills {sorted(discovered)} must match catalog directories "
            f"{sorted(directories)} and include {sorted(INITIAL_NAMES)}"
        )


def check_copied_resources(source: Path, installed: Path) -> None:
    def files(directory):
        return {
            path.relative_to(directory): path
            for path in directory.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }

    expected, actual = files(source), files(installed)
    if expected.keys() != actual.keys():
        raise ValueError(f"Incomplete installation at {installed}: missing {sorted(expected.keys() - actual.keys())}; unexpected {sorted(actual.keys() - expected.keys())}")
    for relative, original in expected.items():
        copied = actual[relative]
        if copied.is_symlink() or copied.read_bytes() != original.read_bytes():
            raise ValueError(f"Installed resource differs from source: {copied}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    environment = {**os.environ, "DISABLE_TELEMETRY": "1", "DO_NOT_TRACK": "1", "NO_COLOR": "1", "CI": "1"}
    command = ["npx", "--yes", f"skills@{SKILLS_VERSION}", "add"]

    def run(arguments, cwd):
        result = subprocess.run(
            [*command, *arguments], cwd=cwd, env=environment,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120,
        )
        if result.returncode:
            raise RuntimeError(result.stdout)
        return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.stdout)

    listing = run([".", "--list"], root)
    print(listing, flush=True)
    # Consume the pinned CLI's actual listing; never parse frontmatter here.
    names = set(re.findall(r"^│    ([a-z0-9][a-z0-9-]*)\s*$", listing, re.MULTILINE))
    directories = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    check_discovered_names(names, directories)
    for name in sorted(names):
        with tempfile.TemporaryDirectory(prefix=f"aivision-{name}-") as temporary:
            project = Path(temporary)
            run([str(root), "--skill", name, "--agent", "codex", "--copy", "--yes"], project)
            location = project / ".agents" / "skills"
            if {path.name for path in location.iterdir()} != {name}:
                raise ValueError(f"Expected only {name} to be installed under {location}")
            check_copied_resources(root / "skills" / name, location / name)
            print(f"PASS {name}: independent complete copy at {location / name} (removed after check)", flush=True)


if __name__ == "__main__":
    main()
