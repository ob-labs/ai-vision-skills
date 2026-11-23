#!/usr/bin/env python3
"""Check bundled resources and catalog indexes; upstream ``skills`` owns discovery.

The additional checkout rule is deliberately syntactic: shell examples and
scripts must not clone ob-labs/ai-vision-ob or execute through a named product
checkout (ai-vision-ob paths or AIV_REPO source-subdirectory paths). Provenance
URLs and prose about source access remain allowed. Product download recipes
use antgroup/ai-vision.
"""
from html import unescape
from pathlib import Path
import re
import sys
from unicodedata import category
from urllib.parse import unquote, urlsplit


INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[^)\n]*)?\)")
REFERENCE_LINK = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)", re.MULTILINE)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})([\w-]*)\s*$")
ATX_HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$", re.MULTILINE)
NAMED_ANCHOR = re.compile(r"""<a\b[^>]*?\sname\s*=\s*(['"])([^'"]+)\1""", re.IGNORECASE)
INDEXES = ("README.md", "README.zh-CN.md", "README.ja-JP.md", "skills/README.md")
CHECKOUT_COMMAND = re.compile(
    r"\b(?:git\s+clone|gh\s+repo\s+clone)\b[^\n]*"
    r"(?:github\.com[:/])?ob-labs/ai-vision-ob(?:\.git)?(?:[\s\"']|$)"
    r"|\b(?:cd|pushd)\s+[^\n]*\bai-vision-ob(?:[/\s\"']|$)"
    r"|\$(?:AIV_REPO|\{AIV_REPO\})/(?:aivision-cli|deploy|ai-vision|agentlens|antcollector)(?:[/\s\"']|$)"
)
RETIRED_REPOSITORY = r"ob-labs/ai-vision-(?:skills|ob)"
RETIRED_RELEASE_ENDPOINT = re.compile(
    rf"(?:github\.com/|repos/){RETIRED_REPOSITORY}/releases\b"
    rf"|\bgh\s+release\s+(?:download|list|view)\b[^\n]*{RETIRED_REPOSITORY}\b"
    rf"|\bghcr\.io/{RETIRED_REPOSITORY}/",
    re.IGNORECASE,
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
        elif language in {"", "sh", "bash", "shell", "zsh", "console", "powershell", "pwsh", "ps1"}:
            commands.append(line)
    return "\n".join(prose), "\n".join(commands)


def _markdown_links(prose: str):
    for pattern in (INLINE_LINK, REFERENCE_LINK):
        for match in pattern.finditer(prose):
            yield match.group(1).strip("<>")


def _markdown_sections(text: str) -> set[str]:
    """Resolve GitHub section IDs for ATX headings and named HTML anchors."""
    prose, _ = _markdown_parts(text)
    prose = re.sub(r"<!--.*?-->", "", prose, flags=re.DOTALL)
    headings: set[str] = set()
    suffixes: dict[str, int] = {}
    for match in ATX_HEADING.finditer(prose):
        heading = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", match[1])
        heading = re.sub(r"</?[A-Za-z][^>]*>", "", heading)
        heading = re.sub(r"(?<!\w)(_+)(\S(?:.*?\S)?)\1(?!\w)", r"\2", heading)
        slug = "".join(
            char for char in unescape(heading).strip().lower().replace(" ", "-")
            if char.isalnum() or char in "-_" or category(char).startswith("M")
        )
        if not slug:
            continue
        anchor = slug
        while anchor in headings:
            suffixes[slug] = suffixes.get(slug, 0) + 1
            anchor = f"{slug}-{suffixes[slug]}"
        headings.add(anchor)
    return headings | {unescape(match[2]) for match in NAMED_ANCHOR.finditer(prose)}


def _missing_section(destination: Path, fragment: str, sections: dict[Path, set[str]]) -> bool:
    if not fragment or destination.suffix.lower() != ".md" or not destination.is_file():
        return False
    if destination not in sections:
        sections[destination] = _markdown_sections(destination.read_text(encoding="utf-8"))
    return unquote(fragment) not in sections[destination]


def validate_catalog(root: Path) -> list[str]:
    """Return resource, section-link, duplicate-name, and checkout integrity errors.

    Only ordinary one-line ``name:`` scalars are read for duplicate detection.
    This is not a YAML validator: the pinned upstream CLI must also accept and
    independently install every discovered Skill (see check_installation.py).
    """
    root = root.resolve()
    errors: list[str] = []
    names: dict[str, Path] = {}
    sections: dict[Path, set[str]] = {}
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
                for target in _markdown_links(prose):
                    if RETIRED_RELEASE_ENDPOINT.search(target):
                        errors.append(f"{label}: retired product download link {target!r}")
                    parsed = urlsplit(target)
                    if parsed.scheme or parsed.netloc or not (parsed.path or parsed.fragment):
                        continue
                    resolved = (resource.parent / unquote(parsed.path)).resolve() if parsed.path else resource.resolve()
                    if not resolved.is_relative_to(skill):
                        errors.append(f"{label}: local resource {target!r} escapes its Skill directory")
                    elif not resolved.exists():
                        errors.append(f"{label}: missing local resource {target!r}")
                    elif _missing_section(resolved, parsed.fragment, sections):
                        errors.append(f"{label}: missing Markdown section {target!r}")
            elif resource.suffix in {".sh", ".bash", ".zsh", ".py", ".ps1", ".jq"}:
                commands = resource.read_text(encoding="utf-8")
            else:
                continue
            if CHECKOUT_COMMAND.search(commands):
                errors.append(f"{label}: executable prerequisite uses a private product checkout")
            if RETIRED_RELEASE_ENDPOINT.search(commands):
                errors.append(f"{label}: executable recipe uses a retired product download location")
    return errors


def validate_indexes(root: Path) -> list[str]:
    root = root.resolve()
    entries = {entry.relative_to(root) for entry in (root / "skills").glob("*/SKILL.md")}
    errors = []
    sections: dict[Path, set[str]] = {}
    for index in INDEXES:
        path = root / index
        if not path.is_file() or not path.resolve().is_relative_to(root):
            errors.append(f"{index}: missing catalog index in repository")
            continue
        prose, commands = _markdown_parts(path.read_text(encoding="utf-8"))
        linked_entries = set()
        for target in _markdown_links(prose):
            if RETIRED_RELEASE_ENDPOINT.search(target):
                errors.append(f"{index}: retired product download link {target!r}")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not (parsed.path or parsed.fragment):
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
            if not resolved.is_relative_to(root) or not resolved.exists():
                errors.append(f"{index}: missing local link target {target!r}")
                continue
            if _missing_section(resolved, parsed.fragment, sections):
                errors.append(f"{index}: missing Markdown section {target!r}")
            linked_entries.add(resolved.relative_to(root))
        for entry in sorted(entries - linked_entries):
            errors.append(f"{index}: missing link to {entry}")
        if RETIRED_RELEASE_ENDPOINT.search(commands):
            errors.append(f"{index}: executable recipe uses a retired product download location")
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate_catalog(root) + validate_indexes(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Skill resources and catalog indexes passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
