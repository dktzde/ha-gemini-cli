#!/usr/bin/env python3
"""
Home Assistant Developer Docs updater.

Clones the HA developer docs repo, strips frontmatter (keeping title),
removes MDX components and raw HTML, generates a CLAUDE.md index,
and produces a changelog based on diff.

Usage:
    python update-docs.py <target_dir>

Example:
    python update-docs.py ./docs/hass-developer
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/home-assistant/developers.home-assistant.git"

# MDX component patterns to strip (multiline)
MDX_COMPONENT_PATTERNS = [
    # Self-closing MDX components: <Component ... />
    re.compile(r'<(?:ApiEndpoint|RelatedRules|TabItem|Tabs|CodeBlock|GRADLE_MODULE)[^>]*/>', re.IGNORECASE),
    # Opening+closing MDX components with content
    re.compile(r'<(ApiEndpoint|RelatedRules|TabItem|Tabs|CodeBlock|GRADLE_MODULE)\b[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE),
    # Opening MDX tags without closing (standalone)
    re.compile(r'<(?:ApiEndpoint|RelatedRules|TabItem|Tabs|CodeBlock|GRADLE_MODULE)\b[^>]*>', re.IGNORECASE),
]

# HTML elements to strip (keep content, remove tags)
HTML_TAG_STRIP = re.compile(r'</?(?:div|span|iframe|img|br|hr|sup|sub|a|p|ul|ol|li|table|thead|tbody|tr|td|th|details|summary)\b[^>]*/?>', re.IGNORECASE)

# Docusaurus import statements
IMPORT_PATTERN = re.compile(r'^import\s+.*?from\s+[\'"]@site/.*$', re.MULTILINE)

# Docusaurus admonitions (:::note, :::tip, etc.) — keep content, strip markers
ADMONITION_MARKER = re.compile(r'^:::\w*\s*$', re.MULTILINE)


def extract_title(content: str) -> str | None:
    """Extract title from YAML frontmatter."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    frontmatter = match.group(1)
    title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', frontmatter, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    return None


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter entirely."""
    return re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, count=1, flags=re.DOTALL)


def clean_content(content: str) -> str:
    """Strip MDX components, HTML elements, and Docusaurus-specific syntax."""
    # Remove import statements (Docusaurus MDX imports)
    content = IMPORT_PATTERN.sub('', content)

    # Remove MDX components
    for pattern in MDX_COMPONENT_PATTERNS:
        content = pattern.sub('', content)

    # Strip HTML tags (keep inner content)
    content = HTML_TAG_STRIP.sub('', content)

    # Strip admonition markers but keep content
    content = ADMONITION_MARKER.sub('', content)

    # Clean up excessive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip() + '\n'


def process_file(src: Path, dst: Path) -> str | None:
    """Process a single doc file. Returns title or None."""
    content = src.read_text(encoding='utf-8', errors='replace')
    title = extract_title(content)
    content = strip_frontmatter(content)
    content = clean_content(content)

    dst.parent.mkdir(parents=True, exist_ok=True)

    # Rename .mdx to .md
    if dst.suffix == '.mdx':
        dst = dst.with_suffix('.md')

    dst.write_text(content, encoding='utf-8')
    return title


def generate_index(target_dir: Path, file_titles: dict[str, str | None]) -> str:
    """Generate CLAUDE.md index content."""
    lines = [
        "# Home Assistant Developer Documentation",
        "",
        "Local mirror of the [Home Assistant Developer Docs](https://developers.home-assistant.io/).",
        "Use the `hass-docs-search` subagent to search these docs efficiently.",
        "",
        "## Index",
        "",
    ]

    # Group by directory
    groups: dict[str, list[tuple[str, str | None]]] = {}
    for rel_path, title in sorted(file_titles.items()):
        parts = Path(rel_path).parts
        group = parts[0] if len(parts) > 1 else "(root)"
        groups.setdefault(group, []).append((rel_path, title))

    for group, files in sorted(groups.items()):
        lines.append(f"### {group}")
        lines.append("")
        for rel_path, title in sorted(files):
            display = title if title else Path(rel_path).stem
            lines.append(f"- `{rel_path}` — {display}")
        lines.append("")

    return "\n".join(lines)


def generate_changelog(target_dir: Path, stage_dir: Path) -> str | None:
    """Generate changelog by diffing target vs stage. Returns changelog text or None."""
    if not target_dir.exists():
        return "Initial import of Home Assistant developer documentation."

    # Use diff --brief for a summary (avoids context blowup)
    result = subprocess.run(
        ["diff", "-rq", str(target_dir), str(stage_dir)],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        return None  # No changes

    # Parse diff --brief output into a readable changelog
    lines = result.stdout.strip().split('\n')
    added = []
    removed = []
    changed = []

    for line in lines:
        if not line.strip():
            continue
        # Skip CLAUDE.md and CHANGELOG.md from diff
        if 'CLAUDE.md' in line or 'CHANGELOG.md' in line:
            continue
        if line.startswith("Only in " + str(stage_dir)):
            # New file in stage
            path = line.split(": ", 1)
            if len(path) == 2:
                added.append(path[1])
        elif line.startswith("Only in " + str(target_dir)):
            # Removed file
            path = line.split(": ", 1)
            if len(path) == 2:
                removed.append(path[1])
        elif "differ" in line:
            # Changed file - extract relative path
            parts = line.split(" and ")
            if len(parts) == 2:
                file_path = parts[1].replace(" differ", "").strip()
                rel = os.path.relpath(file_path, str(stage_dir))
                changed.append(rel)

    if not added and not removed and not changed:
        return None

    changelog_parts = []
    if added:
        changelog_parts.append(f"Added ({len(added)}): " + ", ".join(added))
    if removed:
        changelog_parts.append(f"Removed ({len(removed)}): " + ", ".join(removed))
    if changed:
        changelog_parts.append(f"Updated ({len(changed)}): " + ", ".join(changed[:20]))
        if len(changed) > 20:
            changelog_parts.append(f"  ... and {len(changed) - 20} more")

    return "\n".join(changelog_parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python update-docs.py <target_dir>", file=sys.stderr)
        sys.exit(1)

    target_dir = Path(sys.argv[1]).resolve()

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_dir = Path(tmpdir) / "repo"
        stage_dir = Path(tmpdir) / "stage"

        # Clone repo (shallow)
        print(f"Cloning {REPO_URL}...")
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(clone_dir)],
            check=True, capture_output=True, text=True
        )

        docs_src = clone_dir / "docs"
        if not docs_src.exists():
            print("ERROR: docs/ directory not found in repo", file=sys.stderr)
            sys.exit(1)

        # Process all doc files into stage
        stage_dir.mkdir(parents=True, exist_ok=True)
        file_titles: dict[str, str | None] = {}
        doc_files = list(docs_src.rglob("*.md")) + list(docs_src.rglob("*.mdx"))

        for src_file in doc_files:
            rel = src_file.relative_to(docs_src)
            # Normalize .mdx → .md in the relative path
            if rel.suffix == '.mdx':
                rel = rel.with_suffix('.md')
            dst_file = stage_dir / rel

            title = process_file(src_file, dst_file)
            file_titles[str(rel)] = title

        print(f"Processed {len(file_titles)} files")

        # Generate index
        index_content = generate_index(target_dir, file_titles)
        (stage_dir / "CLAUDE.md").write_text(index_content, encoding='utf-8')

        # Generate changelog
        changelog = generate_changelog(target_dir, stage_dir)
        if changelog:
            print(f"Changes detected:\n{changelog}")
            # Append to changelog file in stage
            changelog_file = stage_dir / "CHANGELOG.md"
            existing = ""
            existing_target = target_dir / "CHANGELOG.md"
            if existing_target.exists():
                existing = existing_target.read_text(encoding='utf-8')

            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_entry = f"## {date_str}\n\n{changelog}\n\n"

            if existing:
                # Insert after the first heading line
                header_end = existing.find('\n\n')
                if header_end > 0:
                    updated = existing[:header_end + 2] + new_entry + existing[header_end + 2:]
                else:
                    updated = existing + "\n" + new_entry
            else:
                updated = "# Docs Changelog\n\n" + new_entry

            changelog_file.write_text(updated, encoding='utf-8')
        else:
            print("No changes detected.")
            # Still copy existing changelog if present
            existing_target = target_dir / "CHANGELOG.md"
            if existing_target.exists():
                shutil.copy2(existing_target, stage_dir / "CHANGELOG.md")

        # Deploy: purge target and replace with stage
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(stage_dir, target_dir)

        print(f"Docs deployed to {target_dir}")
        if changelog:
            print("CHANGELOG.md updated")
        else:
            print("No content changes")


if __name__ == "__main__":
    main()
