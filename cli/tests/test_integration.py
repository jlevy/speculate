"""Integration tests for speculate CLI.

These tests use the local speculate repo as a template source and verify
the full workflow works correctly.
"""

import os
import subprocess
import sys
from pathlib import Path

import yaml

# Get the repo root (parent of cli/)
# test file is at cli/tests/test_integration.py
# cli/ is at cli/
# repo root is parent of cli/
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()


def run_speculate(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the speculate CLI command."""
    cmd = [sys.executable, "-m", "speculate.cli.cli_main", *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "cli" / "src")},
    )


class TestInitWithLocalTemplate:
    """Test init command with local template path."""

    def test_init_creates_docs_directory(self, tmp_path: Path):
        """Init with local template should create docs/ directory."""
        result = run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        # Should succeed
        assert result.returncode == 0, f"init failed: {result.stderr}"

        # docs/ should exist
        docs_dir = tmp_path / "docs"
        assert docs_dir.exists(), "docs/ directory not created"
        assert docs_dir.is_dir()

    def test_init_only_copies_docs_directory(self, tmp_path: Path):
        """Init should ONLY copy docs/, not other repo files.

        This is critical - copier must be configured to copy ONLY docs/.
        """
        result = run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)
        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Files/dirs that should NOT exist (they're in the repo but shouldn't be copied)
        # This list should catch common mistakes in copier.yml configuration
        excluded_items = [
            "cli",  # CLI source directory
            "Makefile",  # Root Makefile
            "LICENSE",  # License file
            "copier.yml",  # Copier config itself
            "README.md",  # Root README (if present)
            "CLAUDE.md",  # This is created by install(), not copied from template
            "AGENTS.md",  # This is created by install(), not copied from template
        ]

        for item in excluded_items:
            # Note: CLAUDE.md and AGENTS.md will be created by install() which runs
            # after init, so we check they weren't copied as template files
            # by verifying they contain our marker
            if item in ("CLAUDE.md", "AGENTS.md"):
                path = tmp_path / item
                if path.exists():
                    content = path.read_text()
                    # If it exists, it should have our speculate marker (created by install)
                    # not be a copy of the template's file
                    assert "Speculate project structure" in content, (
                        f"{item} was copied from template instead of being created by install"
                    )
            else:
                assert not (tmp_path / item).exists(), f"{item} should not be copied from template"

        # .cursor/ should not exist as a copied directory from template
        # (it gets created by install() with symlinks, not copied)
        cursor_dir = tmp_path / ".cursor"
        if cursor_dir.exists():
            # If .cursor exists, verify rules/ has .mdc symlinks, not .md copies
            cursor_rules = cursor_dir / "rules"
            if cursor_rules.exists():
                md_files = list(cursor_rules.glob("*.md"))
                assert len(md_files) == 0, (
                    f".cursor/rules/*.md should not be copied directly: {md_files}"
                )
                # Should have .mdc symlinks created by install()
                mdc_files = list(cursor_rules.glob("*.mdc"))
                assert len(mdc_files) > 0 or not cursor_rules.exists(), (
                    ".cursor/rules/ should have .mdc symlinks if it exists"
                )

    def test_init_copies_docs_overview(self, tmp_path: Path):
        """Init should copy docs/docs-overview.md."""
        result = run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # docs/docs-overview.md should exist
        docs_overview = tmp_path / "docs" / "docs-overview.md"
        assert docs_overview.exists(), "docs/docs-overview.md not created"

    def test_init_copies_agent_rules(self, tmp_path: Path):
        """Init should copy docs/general/agent-rules/."""
        result = run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # agent-rules/ should exist with md files
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        assert rules_dir.exists(), "docs/general/agent-rules/ not created"

        md_files = list(rules_dir.glob("*.md"))
        assert len(md_files) > 0, "No rule files copied"

    def test_init_auto_runs_install(self, tmp_path: Path):
        """Init should automatically run install and create tool configs."""
        result = run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Tool configs should be created by auto-install
        assert (tmp_path / "CLAUDE.md").exists(), "CLAUDE.md not created"
        assert (tmp_path / "AGENTS.md").exists(), "AGENTS.md not created"
        assert (tmp_path / ".cursor" / "rules").exists(), ".cursor/rules/ not created"
        assert (tmp_path / ".speculate" / "settings.yml").exists(), (
            ".speculate/settings.yml not created"
        )


class TestInstallCommand:
    """Test install command."""

    def test_install_creates_claude_md(self, tmp_path: Path):
        """Install should create CLAUDE.md with header."""
        # First init to get docs/
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        # Remove CLAUDE.md and run install again
        (tmp_path / "CLAUDE.md").unlink()

        result = run_speculate("install", cwd=tmp_path)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        # CLAUDE.md should be recreated
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists()

        content = claude_md.read_text()
        assert "Speculate project structure" in content
        assert "./docs/development.md" in content

    def test_install_creates_agents_md(self, tmp_path: Path):
        """Install should create AGENTS.md with header."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        # Remove AGENTS.md and run install again
        (tmp_path / "AGENTS.md").unlink()

        result = run_speculate("install", cwd=tmp_path)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        agents_md = tmp_path / "AGENTS.md"
        assert agents_md.exists()

        content = agents_md.read_text()
        assert "Speculate project structure" in content

    def test_install_creates_cursor_symlinks(self, tmp_path: Path):
        """Install should create .cursor/rules/ symlinks with .mdc extension."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        cursor_rules = tmp_path / ".cursor" / "rules"
        assert cursor_rules.exists()

        # Should have .mdc symlinks
        mdc_files = list(cursor_rules.glob("*.mdc"))
        assert len(mdc_files) > 0, "No .mdc symlinks created"

        # Each should be a symlink
        for mdc_file in mdc_files:
            assert mdc_file.is_symlink(), f"{mdc_file} is not a symlink"

        # Symlinks should be relative
        for mdc_file in mdc_files:
            target = os.readlink(mdc_file)
            assert not target.startswith("/"), f"Symlink {mdc_file} is not relative"

    def test_install_with_include_pattern(self, tmp_path: Path):
        """Install with --include should filter rules."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        # Clear cursor rules
        cursor_rules = tmp_path / ".cursor" / "rules"
        for f in cursor_rules.iterdir():
            f.unlink()

        # Install only general-* rules
        result = run_speculate("install", "--include", "general-*.md", cwd=tmp_path)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        # Should only have general-* files
        mdc_files = list(cursor_rules.glob("*.mdc"))
        for f in mdc_files:
            assert f.stem.startswith("general-"), f"Unexpected file: {f.name}"

    def test_install_with_exclude_pattern(self, tmp_path: Path):
        """Install with --exclude should filter out rules."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        # Clear cursor rules
        cursor_rules = tmp_path / ".cursor" / "rules"
        for f in cursor_rules.iterdir():
            f.unlink()

        # Install excluding convex rules
        result = run_speculate("install", "--exclude", "convex-*.md", cwd=tmp_path)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        # Should not have convex files
        mdc_files = list(cursor_rules.glob("*.mdc"))
        for f in mdc_files:
            assert not f.stem.startswith("convex-"), f"Convex file should be excluded: {f.name}"

    def test_install_updates_settings_yml(self, tmp_path: Path):
        """Install should create/update .speculate/settings.yml."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        settings_file = tmp_path / ".speculate" / "settings.yml"
        assert settings_file.exists()

        settings = yaml.safe_load(settings_file.read_text())
        assert "last_update" in settings
        assert "last_cli_version" in settings


class TestStatusCommand:
    """Test status command."""

    def test_status_shows_template_info(self, tmp_path: Path):
        """Status should show template version info."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        # Create development.md to avoid error
        (tmp_path / "docs" / "development.md").write_text("# Development")

        result = run_speculate("status", cwd=tmp_path)
        assert result.returncode == 0, f"status failed: {result.stderr}"

        # Output should contain status info
        assert "Template version" in result.stdout or "✔" in result.stdout

    def test_status_fails_without_development_md(self, tmp_path: Path):
        """Status should fail if development.md is missing."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)

        # development.md is created by init, remove it
        dev_md = tmp_path / "docs" / "development.md"
        if dev_md.exists():
            dev_md.unlink()

        result = run_speculate("status", cwd=tmp_path)

        # Should fail with exit code 1
        assert result.returncode == 1
        assert "development.md" in result.stdout or "missing" in result.stdout.lower()

    def test_status_shows_tool_configs(self, tmp_path: Path):
        """Status should show which tool configs exist."""
        run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)
        (tmp_path / "docs" / "development.md").write_text("# Development")

        result = run_speculate("status", cwd=tmp_path)
        assert result.returncode == 0, f"status failed: {result.stderr}"

        # Should mention tool configs
        output = result.stdout
        assert "CLAUDE.md" in output
        assert "AGENTS.md" in output
        assert ".cursor/rules" in output


class TestFullWorkflow:
    """Test complete workflow from init through status."""

    def test_complete_workflow(self, tmp_path: Path):
        """Test complete init -> install -> status workflow."""
        # Step 1: Initialize
        result = run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)
        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify docs structure
        assert (tmp_path / "docs" / "docs-overview.md").exists()
        assert (tmp_path / "docs" / "general" / "agent-rules").exists()
        assert (tmp_path / "docs" / "general" / "agent-shortcuts").exists()
        assert (tmp_path / "docs" / "project" / "specs").exists()

        # Verify tool configs created by auto-install
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / ".cursor" / "rules").is_dir()
        assert (tmp_path / ".speculate" / "settings.yml").exists()

        # Step 2: Create development.md (required by status)
        (tmp_path / "docs" / "development.md").write_text("# My Project Development\n")

        # Step 3: Run status
        result = run_speculate("status", cwd=tmp_path)
        assert result.returncode == 0, f"status failed: {result.stderr}"

        # Step 4: Run install again (should be idempotent)
        result = run_speculate("install", cwd=tmp_path)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        # Verify CLAUDE.md header is not duplicated
        claude_content = (tmp_path / "CLAUDE.md").read_text()
        marker_count = claude_content.count("Speculate project structure")
        assert marker_count == 1, f"Header duplicated: found {marker_count} markers"

    def test_workflow_with_existing_claude_md(self, tmp_path: Path):
        """Test workflow when CLAUDE.md already exists with content."""
        # Create existing CLAUDE.md
        existing_content = "# Existing Rules\n\nSome existing content.\n"
        (tmp_path / "CLAUDE.md").write_text(existing_content)

        # Initialize
        result = run_speculate("init", "--overwrite", "--template", str(REPO_ROOT), cwd=tmp_path)
        assert result.returncode == 0, f"init failed: {result.stderr}"

        # CLAUDE.md should have header prepended but keep original content
        claude_content = (tmp_path / "CLAUDE.md").read_text()
        assert "Speculate project structure" in claude_content
        assert "Existing Rules" in claude_content
        assert "Some existing content" in claude_content

        # Header should come before original content
        header_pos = claude_content.index("Speculate project structure")
        original_pos = claude_content.index("Existing Rules")
        assert header_pos < original_pos, "Header should be prepended"
