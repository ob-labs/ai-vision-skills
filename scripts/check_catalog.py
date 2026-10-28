#!/usr/bin/env python3
"""Check bundled resources; upstream ``skills`` owns YAML parsing/discovery.

The additional checkout rule is deliberately syntactic: shell examples and
scripts must not clone ob-labs/ai-vision-ob or execute through a named product
checkout (ai-vision-ob paths or AIV_REPO source-subdirectory paths). Provenance
URLs, release downloads, and prose about source access remain allowed.
"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[^)\n]*)?\)")
REFERENCE_LINK = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)", re.MULTILINE)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})([\w-]*)\s*$")
CHECKOUT_COMMAND = re.compile(
    r"\b(?:git\s+clone|gh\s+repo\s+clone)\b[^\n]*"
    r"(?:github\.com[:/])?ob-labs/ai-vision-ob(?:\.git)?(?:[\s\"']|$)"
    r"|\b(?:cd|pushd)\s+[^\n]*\bai-vision-ob(?:[/\s\"']|$)"
    r"|\$(?:AIV_REPO|\{AIV_REPO\})/(?:aivision-cli|deploy|ai-vision|agentlens|antcollector)(?:[/\s\"']|$)"
)


def _markdown_parts(text: str) -> tuple[str, str]:
    """Separate rendered links from shell blocks and inline command spans."""
    prose, commands = [], []
    fence, language = "", ""
    for line in text.splitlines():
        marker = FENCE.match(line)
        if marker:
            if not fence:
                fence, language = marker.group(1), marker.group(2)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence, language = "", ""
            continue
        if not fence:
            prose.append(line)
            commands.extend(re.findall(r"`([^`]+)`", line))
        elif language in {"", "sh", "bash", "shell", "zsh", "console"}:
            commands.append(line)
    return "\n".join(prose), "\n".join(commands)


def validate_catalog(root: Path) -> list[str]:
    """Return resource, duplicate-name, and private-checkout integrity errors.

    Only ordinary one-line ``name:`` scalars are read for duplicate detection.
    This is not a YAML validator: the pinned upstream CLI must also accept and
    independently install every discovered Skill (see check_installation.py).
    """
    root = root.resolve()
    errors: list[str] = []
    names: dict[str, Path] = {}
    for entry in sorted((root / "skills").glob("*/SKILL.md")):
        skill = entry.parent.resolve()
        text = entry.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
        if frontmatter:
            name_line = re.search(r"^name:\s*([\w-]+|'[\w-]+'|\"[\w-]+\")\s*$", frontmatter.group(1), re.MULTILINE)
            if name_line:
                name = name_line.group(1).strip("'\"")
                if name in names:
                    errors.append(f"{entry.relative_to(root)}: duplicate Skill name {name!r} (also {names[name].relative_to(root)})")
                names[name] = entry
        for resource in sorted(entry.parent.rglob("*")):
            label = resource.relative_to(root)
            if not resource.resolve().is_relative_to(skill):
                errors.append(f"{label}: resource escapes its Skill directory")
                continue
            if not resource.is_file():
                continue
            if resource.suffix.lower() == ".md":
                prose, commands = _markdown_parts(resource.read_text(encoding="utf-8"))
                targets = [match.group(1) for pattern in (INLINE_LINK, REFERENCE_LINK) for match in pattern.finditer(prose)]
                for target in targets:
                    target = target.strip("<>")
                    parsed = urlsplit(target)
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    resolved = (resource.parent / unquote(parsed.path)).resolve()
                    if not resolved.is_relative_to(skill):
                        errors.append(f"{label}: local resource {target!r} escapes its Skill directory")
                    elif not resolved.exists():
                        errors.append(f"{label}: missing local resource {target!r}")
            elif resource.suffix in {".sh", ".bash", ".zsh", ".py"}:
                commands = resource.read_text(encoding="utf-8")
            else:
                continue
            if CHECKOUT_COMMAND.search(commands):
                errors.append(f"{label}: executable prerequisite uses a private product checkout")
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate_catalog(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Skill catalog resource checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
