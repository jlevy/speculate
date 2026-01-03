"""Tests for CLI commands."""

import os
from pathlib import Path

import pytest
import yaml
from pytest import MonkeyPatch

from speculate.cli.cli_commands import (
    CLAUDE_PLUGIN_DIR,
    CLAUDE_PLUGIN_NAME,
    SPECULATE_HEADER,
    SPECULATE_MARKER,
    _ensure_speculate_header,
    _generate_plugin_json,
    _generate_skill_md,
    _remove_claude_plugin,
    _remove_cursor_rules,
    _remove_speculate_header,
    _setup_claude_plugin,
    _setup_cursor_rules,
    _update_speculate_settings,
    install,
    status,
    uninstall,
)


class TestUpdateSpeculateSettings:
    """Tests for _update_speculate_settings function."""

    def test_creates_settings_file(self, tmp_path: Path):
        """Should create .speculate/settings.yml if it doesn't exist."""
        _update_speculate_settings(tmp_path)

        settings_file = tmp_path / ".speculate" / "settings.yml"
        assert settings_file.exists()

        settings = yaml.safe_load(settings_file.read_text())
        assert "last_update" in settings
        assert "last_cli_version" in settings

    def test_updates_existing_settings(self, tmp_path: Path):
        """Should update existing settings file."""
        settings_dir = tmp_path / ".speculate"
        settings_dir.mkdir()
        settings_file = settings_dir / "settings.yml"
        settings_file.write_text(yaml.dump({"custom_key": "custom_value"}))

        _update_speculate_settings(tmp_path)

        settings = yaml.safe_load(settings_file.read_text())
        # Existing keys should be preserved
        assert settings.get("custom_key") == "custom_value"
        # New keys should be added
        assert "last_update" in settings

    def test_reads_docs_version_from_copier_answers(self, tmp_path: Path):
        """Should read docs version from .speculate/copier-answers.yml."""
        speculate_dir = tmp_path / ".speculate"
        speculate_dir.mkdir()
        copier_answers = speculate_dir / "copier-answers.yml"
        copier_answers.write_text(yaml.dump({"_commit": "v1.2.3", "_src_path": "gh:test/repo"}))

        _update_speculate_settings(tmp_path)

        settings_file = tmp_path / ".speculate" / "settings.yml"
        settings = yaml.safe_load(settings_file.read_text())
        assert settings.get("last_docs_version") == "v1.2.3"


class TestSetupCursorRules:
    """Tests for _setup_cursor_rules function."""

    def test_creates_cursor_rules_directory(self, tmp_path: Path):
        """Should create .cursor/rules/ directory."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)

        _setup_cursor_rules(tmp_path)

        cursor_dir = tmp_path / ".cursor" / "rules"
        assert cursor_dir.exists()

    def test_creates_symlinks_for_md_files(self, tmp_path: Path):
        """Should create symlinks with .mdc extension."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "general-rules.md").write_text("# General Rules")
        (rules_dir / "python-rules.md").write_text("# Python Rules")

        _setup_cursor_rules(tmp_path)

        cursor_dir = tmp_path / ".cursor" / "rules"
        assert (cursor_dir / "general-rules.mdc").is_symlink()
        assert (cursor_dir / "python-rules.mdc").is_symlink()

    def test_symlinks_are_relative(self, tmp_path: Path):
        """Symlinks should be relative paths."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test.md").write_text("# Test")

        _setup_cursor_rules(tmp_path)

        link = tmp_path / ".cursor" / "rules" / "test.mdc"
        target = os.readlink(link)
        assert not target.startswith("/")
        assert "docs/general/agent-rules/test.md" in target

    def test_include_pattern_filters_rules(self, tmp_path: Path):
        """Include pattern should filter which rules are linked."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "general-rules.md").write_text("# General Rules")
        (rules_dir / "python-rules.md").write_text("# Python Rules")

        _setup_cursor_rules(tmp_path, include=["general-*.md"])

        cursor_dir = tmp_path / ".cursor" / "rules"
        assert (cursor_dir / "general-rules.mdc").exists()
        assert not (cursor_dir / "python-rules.mdc").exists()

    def test_exclude_pattern_filters_rules(self, tmp_path: Path):
        """Exclude pattern should filter out matching rules."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "general-rules.md").write_text("# General Rules")
        (rules_dir / "convex-rules.md").write_text("# Convex Rules")

        _setup_cursor_rules(tmp_path, exclude=["convex-*.md"])

        cursor_dir = tmp_path / ".cursor" / "rules"
        assert (cursor_dir / "general-rules.mdc").exists()
        assert not (cursor_dir / "convex-rules.mdc").exists()

    def test_warns_when_rules_dir_missing(self, tmp_path: Path):
        """Should warn when docs/general/agent-rules/ doesn't exist."""
        _setup_cursor_rules(tmp_path)
        # The function prints a warning via rich - we just verify it doesn't raise

    def test_skips_existing_symlinks_without_force(self, tmp_path: Path):
        """Should skip existing symlinks unless force=True."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test.md").write_text("# Test")

        # First run creates the symlink
        _setup_cursor_rules(tmp_path)
        cursor_dir = tmp_path / ".cursor" / "rules"
        link = cursor_dir / "test.mdc"
        assert link.is_symlink()

        # Second run without force should skip
        _setup_cursor_rules(tmp_path)
        assert link.is_symlink()

    def test_overwrites_existing_symlinks_with_force(self, tmp_path: Path):
        """Should overwrite existing symlinks when force=True."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test.md").write_text("# Test")

        # First run creates the symlink
        _setup_cursor_rules(tmp_path)
        cursor_dir = tmp_path / ".cursor" / "rules"
        link = cursor_dir / "test.mdc"
        assert link.is_symlink()

        # Second run with force should overwrite
        _setup_cursor_rules(tmp_path, force=True)
        assert link.is_symlink()

    def test_merges_general_and_project_rules(self, tmp_path: Path):
        """Should merge rules from general and project directories."""
        # Create general rules
        general_rules = tmp_path / "docs" / "general" / "agent-rules"
        general_rules.mkdir(parents=True)
        (general_rules / "general-rules.md").write_text("# General")
        (general_rules / "shared-rules.md").write_text("# General Shared")

        # Create project rules
        project_rules = tmp_path / "docs" / "project" / "agent-rules"
        project_rules.mkdir(parents=True)
        (project_rules / "project-rules.md").write_text("# Project")

        _setup_cursor_rules(tmp_path)

        cursor_dir = tmp_path / ".cursor" / "rules"
        assert (cursor_dir / "general-rules.mdc").is_symlink()
        assert (cursor_dir / "shared-rules.mdc").is_symlink()
        assert (cursor_dir / "project-rules.mdc").is_symlink()

        # Verify project-rules points to project directory
        target = os.readlink(cursor_dir / "project-rules.mdc")
        assert "docs/project/agent-rules" in target

    def test_project_rules_override_general(self, tmp_path: Path):
        """Project rules should take precedence over general rules of same name."""
        # Create general rules
        general_rules = tmp_path / "docs" / "general" / "agent-rules"
        general_rules.mkdir(parents=True)
        (general_rules / "python-rules.md").write_text("# General Python")

        # Create project rules with same name
        project_rules = tmp_path / "docs" / "project" / "agent-rules"
        project_rules.mkdir(parents=True)
        (project_rules / "python-rules.md").write_text("# Project Python")

        _setup_cursor_rules(tmp_path)

        cursor_dir = tmp_path / ".cursor" / "rules"
        link = cursor_dir / "python-rules.mdc"
        assert link.is_symlink()

        # Should point to project version, not general
        target = os.readlink(link)
        assert "docs/project/agent-rules" in target
        assert "docs/general/agent-rules" not in target


class TestInstallCommand:
    """Tests for install command."""

    def test_fails_without_docs_directory(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should fail if docs/ directory doesn't exist."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            install()
        assert exc_info.value.code == 1

    def test_creates_all_configs(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should create all tool configurations."""
        # Setup minimal docs structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test-rule.md").write_text("# Test")

        monkeypatch.chdir(tmp_path)
        install()

        # Check all configs exist
        assert (tmp_path / ".speculate" / "settings.yml").exists()
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / ".cursor" / "rules").exists()

    def test_creates_claude_md_as_symlink_when_not_exists(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ):
        """Should create CLAUDE.md as symlink to AGENTS.md when CLAUDE.md doesn't exist."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        monkeypatch.chdir(tmp_path)
        install()

        claude_md = tmp_path / "CLAUDE.md"
        agents_md = tmp_path / "AGENTS.md"

        # CLAUDE.md should be a symlink
        assert claude_md.is_symlink()
        # AGENTS.md should be a regular file
        assert agents_md.exists()
        assert not agents_md.is_symlink()
        # CLAUDE.md should point to AGENTS.md
        assert os.readlink(claude_md) == "AGENTS.md"
        # AGENTS.md should have the speculate header
        assert SPECULATE_MARKER in agents_md.read_text()

    def test_preserves_existing_claude_md_file(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should preserve existing CLAUDE.md as a file (not convert to symlink)."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create CLAUDE.md as a regular file
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# My custom CLAUDE instructions")

        monkeypatch.chdir(tmp_path)
        install()

        # CLAUDE.md should still be a regular file, not a symlink
        assert not claude_md.is_symlink()
        assert claude_md.exists()
        # Should have speculate header prepended
        content = claude_md.read_text()
        assert SPECULATE_MARKER in content
        assert "My custom CLAUDE instructions" in content

    def test_idempotent_with_claude_symlink(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Running install twice should be idempotent when CLAUDE.md is a symlink."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        monkeypatch.chdir(tmp_path)

        # First install
        install()

        claude_md = tmp_path / "CLAUDE.md"
        agents_md = tmp_path / "AGENTS.md"
        agents_content_after_first = agents_md.read_text()

        # Second install
        install()

        # CLAUDE.md should still be a symlink
        assert claude_md.is_symlink()
        # AGENTS.md content should be unchanged (idempotent)
        assert agents_md.read_text() == agents_content_after_first


class TestStatusCommand:
    """Tests for status command."""

    def test_fails_without_development_md(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should fail if development.md is missing."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        # Create copier-answers so it doesn't fail on that first
        speculate_dir = tmp_path / ".speculate"
        speculate_dir.mkdir()
        (speculate_dir / "copier-answers.yml").write_text(
            yaml.dump({"_commit": "abc123", "_src_path": "test"})
        )

        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            status()
        assert exc_info.value.code == 1

    def test_fails_without_copier_answers(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should fail if .speculate/copier-answers.yml is missing."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "development.md").write_text("# Development")

        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            status()
        assert exc_info.value.code == 1

    def test_succeeds_with_all_required_files(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should succeed if development.md and .speculate/copier-answers.yml exist."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "development.md").write_text("# Development")
        speculate_dir = tmp_path / ".speculate"
        speculate_dir.mkdir()
        (speculate_dir / "copier-answers.yml").write_text(
            yaml.dump({"_commit": "abc123", "_src_path": "test"})
        )

        monkeypatch.chdir(tmp_path)

        # Should not raise
        status()


class TestEnsureSpeculateHeader:
    """Tests for _ensure_speculate_header function."""

    def test_creates_new_file_with_header(self, tmp_path: Path):
        """Should create file with header if it doesn't exist."""
        test_file = tmp_path / "CLAUDE.md"

        _ensure_speculate_header(test_file)

        assert test_file.exists()
        content = test_file.read_text()
        assert SPECULATE_MARKER in content

    def test_prepends_header_to_existing_content(self, tmp_path: Path):
        """Should prepend header to existing file content."""
        test_file = tmp_path / "CLAUDE.md"
        existing_content = "# My Custom Instructions\n\nDo this and that."
        test_file.write_text(existing_content)

        _ensure_speculate_header(test_file)

        content = test_file.read_text()
        assert content.startswith(SPECULATE_HEADER)
        assert existing_content in content

    def test_idempotent_when_header_present(self, tmp_path: Path):
        """Should not modify file if header already present."""
        test_file = tmp_path / "CLAUDE.md"
        original_content = SPECULATE_HEADER + "\n\n# Custom stuff"
        test_file.write_text(original_content)

        _ensure_speculate_header(test_file)

        assert test_file.read_text() == original_content

    def test_skips_symlink(self, tmp_path: Path):
        """Should skip symlinks and not modify them."""
        # Create AGENTS.md as the real file
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Original content")

        # Create CLAUDE.md as a symlink to AGENTS.md
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.symlink_to("AGENTS.md")

        # Calling on the symlink should skip it
        _ensure_speculate_header(claude_md)

        # AGENTS.md should not be modified
        assert agents_md.read_text() == "# Original content"
        # CLAUDE.md should still be a symlink
        assert claude_md.is_symlink()


class TestRemoveSpeculateHeader:
    """Tests for _remove_speculate_header function."""

    def test_removes_header_preserves_content(self, tmp_path: Path):
        """Should remove header but preserve other content."""
        test_file = tmp_path / "CLAUDE.md"
        custom_content = "# My Custom Instructions\n\nDo this and that."
        test_file.write_text(SPECULATE_HEADER + "\n\n" + custom_content)

        _remove_speculate_header(test_file)

        assert test_file.exists()
        content = test_file.read_text()
        assert SPECULATE_MARKER not in content
        assert "My Custom Instructions" in content

    def test_removes_header_when_not_at_top(self, tmp_path: Path):
        """Should remove header even when user added content above it."""
        test_file = tmp_path / "CLAUDE.md"
        prefix = "# My prefix content\n\n"
        suffix = "\n\n# My suffix content"
        test_file.write_text(prefix + SPECULATE_HEADER + suffix)

        _remove_speculate_header(test_file)

        content = test_file.read_text()
        assert SPECULATE_MARKER not in content
        assert "My prefix content" in content
        assert "My suffix content" in content

    def test_deletes_file_if_empty_after_removal(self, tmp_path: Path):
        """Should delete file if it becomes empty after header removal."""
        test_file = tmp_path / "CLAUDE.md"
        test_file.write_text(SPECULATE_HEADER + "\n")

        _remove_speculate_header(test_file)

        assert not test_file.exists()

    def test_no_op_if_no_marker(self, tmp_path: Path):
        """Should not modify file if marker is not present."""
        test_file = tmp_path / "CLAUDE.md"
        original_content = "# My custom content\n\nNothing speculate here."
        test_file.write_text(original_content)

        _remove_speculate_header(test_file)

        assert test_file.read_text() == original_content

    def test_no_error_if_file_missing(self, tmp_path: Path):
        """Should not raise error if file doesn't exist."""
        test_file = tmp_path / "CLAUDE.md"

        # Should not raise
        _remove_speculate_header(test_file)

        assert not test_file.exists()


class TestRemoveCursorRules:
    """Tests for _remove_cursor_rules function."""

    def test_removes_symlinks(self, tmp_path: Path):
        """Should remove symlinks from .cursor/rules/."""
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test.md").write_text("# Test")

        cursor_dir = tmp_path / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True)
        link = cursor_dir / "test.mdc"
        link.symlink_to(Path("..") / ".." / "docs" / "general" / "agent-rules" / "test.md")

        _remove_cursor_rules(tmp_path)

        assert not link.exists()

    def test_preserves_non_symlinks(self, tmp_path: Path):
        """Should not remove regular files."""
        cursor_dir = tmp_path / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True)
        regular_file = cursor_dir / "custom.mdc"
        regular_file.write_text("# Custom rules")

        _remove_cursor_rules(tmp_path)

        assert regular_file.exists()

    def test_no_error_if_cursor_dir_missing(self, tmp_path: Path):
        """Should not raise error if .cursor/rules/ doesn't exist."""
        # Should not raise
        _remove_cursor_rules(tmp_path)


class TestUninstallCommand:
    """Tests for uninstall command."""

    def test_removes_all_tool_configs(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should remove all tool configurations."""
        # Setup: create docs and run install
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        rules_dir = tmp_path / "docs" / "general" / "agent-rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test-rule.md").write_text("# Test")

        monkeypatch.chdir(tmp_path)
        install()

        # Verify configs exist
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / ".speculate" / "settings.yml").exists()
        assert (tmp_path / ".cursor" / "rules" / "test-rule.mdc").is_symlink()

        # Run uninstall with force
        uninstall(force=True)

        # Verify headers removed (files may be deleted if empty)
        claude_md = tmp_path / "CLAUDE.md"
        if claude_md.exists():
            assert SPECULATE_MARKER not in claude_md.read_text()

        agents_md = tmp_path / "AGENTS.md"
        if agents_md.exists():
            assert SPECULATE_MARKER not in agents_md.read_text()

        # Settings should be removed
        assert not (tmp_path / ".speculate" / "settings.yml").exists()

        # Symlinks should be removed
        assert not (tmp_path / ".cursor" / "rules" / "test-rule.mdc").exists()

    def test_preserves_docs_directory(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should not remove docs/ directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("# Test")

        monkeypatch.chdir(tmp_path)

        # Create a marker file to test with
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(SPECULATE_HEADER + "\n")

        uninstall(force=True)

        assert docs_dir.exists()
        assert (docs_dir / "test.md").exists()

    def test_preserves_copier_answers(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should not remove .speculate/copier-answers.yml."""
        speculate_dir = tmp_path / ".speculate"
        speculate_dir.mkdir()
        copier_answers = speculate_dir / "copier-answers.yml"
        copier_answers.write_text(yaml.dump({"_commit": "abc123"}))

        # Create a marker file to test with
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(SPECULATE_HEADER + "\n")

        monkeypatch.chdir(tmp_path)
        uninstall(force=True)

        assert copier_answers.exists()

    def test_nothing_to_uninstall(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should handle case when nothing is installed."""
        monkeypatch.chdir(tmp_path)

        # Should not raise
        uninstall(force=True)

    def test_preserves_custom_content_in_claude_md(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should preserve custom content in CLAUDE.md after removing header."""
        custom_content = "# My Custom Instructions\n\nThese are my rules."
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(SPECULATE_HEADER + "\n\n" + custom_content)

        monkeypatch.chdir(tmp_path)
        uninstall(force=True)

        assert claude_md.exists()
        content = claude_md.read_text()
        assert SPECULATE_MARKER not in content
        assert "My Custom Instructions" in content


class TestGeneratePluginJson:
    """Tests for _generate_plugin_json function."""

    def test_generates_valid_json(self):
        """Should generate valid JSON with required fields."""
        import json

        result = _generate_plugin_json()
        data = json.loads(result)

        assert data["name"] == CLAUDE_PLUGIN_NAME
        assert "version" in data
        assert "description" in data
        assert data["author"]["name"] == "Speculate"


class TestGenerateSkillMd:
    """Tests for _generate_skill_md function."""

    def test_generates_skill_with_frontmatter(self):
        """Should generate SKILL.md with YAML frontmatter."""
        shortcuts = ["new-plan-spec.md", "commit-code.md"]
        result = _generate_skill_md(shortcuts)

        assert result.startswith("---")
        assert "name: speculate-workflow" in result
        assert "description:" in result
        assert "---" in result[3:]  # Second --- marker

    def test_generates_trigger_table(self):
        """Should generate trigger table for shortcuts."""
        shortcuts = ["new-plan-spec.md", "commit-code.md"]
        result = _generate_skill_md(shortcuts)

        assert "| If user request involves..." in result
        assert "/speculate:new-plan-spec" in result
        assert "/speculate:commit-code" in result

    def test_includes_workflow_chains(self):
        """Should include common workflow chains."""
        shortcuts = ["new-plan-spec.md"]
        result = _generate_skill_md(shortcuts)

        assert "## Common Workflow Chains" in result
        assert "Full Feature Flow" in result
        assert "Commit Flow" in result


class TestSetupClaudePlugin:
    """Tests for _setup_claude_plugin function."""

    def test_creates_plugin_directory_structure(self, tmp_path: Path):
        """Should create the plugin directory structure."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test-command.md").write_text("# Test Command")

        _setup_claude_plugin(tmp_path)

        plugin_dir = tmp_path / CLAUDE_PLUGIN_DIR
        assert plugin_dir.exists()
        assert (plugin_dir / "commands").exists()
        assert (plugin_dir / "skills" / "speculate-workflow").exists()
        assert (plugin_dir / ".claude-plugin").exists()

    def test_generates_plugin_json(self, tmp_path: Path):
        """Should generate plugin.json manifest."""
        import json

        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test-command.md").write_text("# Test Command")

        _setup_claude_plugin(tmp_path)

        plugin_json = tmp_path / CLAUDE_PLUGIN_DIR / ".claude-plugin" / "plugin.json"
        assert plugin_json.exists()
        data = json.loads(plugin_json.read_text())
        assert data["name"] == CLAUDE_PLUGIN_NAME

    def test_creates_symlinks_for_shortcuts(self, tmp_path: Path):
        """Should create symlinks with shortcut: prefix stripped."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:new-plan-spec.md").write_text("# Plan Spec")
        (shortcuts_dir / "shortcut:commit-code.md").write_text("# Commit")

        _setup_claude_plugin(tmp_path)

        commands_dir = tmp_path / CLAUDE_PLUGIN_DIR / "commands"
        # Should have clean names without shortcut: prefix
        assert (commands_dir / "new-plan-spec.md").is_symlink()
        assert (commands_dir / "commit-code.md").is_symlink()
        # Should not have the prefixed names
        assert not (commands_dir / "shortcut:new-plan-spec.md").exists()

    def test_symlinks_are_relative(self, tmp_path: Path):
        """Symlinks should be relative paths pointing to source."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        _setup_claude_plugin(tmp_path)

        link = tmp_path / CLAUDE_PLUGIN_DIR / "commands" / "test.md"
        target = os.readlink(link)
        assert not target.startswith("/")
        assert "docs/general/agent-shortcuts/shortcut:test.md" in target

    def test_generates_skill_md(self, tmp_path: Path):
        """Should generate SKILL.md routing skill."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        _setup_claude_plugin(tmp_path)

        skill_md = tmp_path / CLAUDE_PLUGIN_DIR / "skills" / "speculate-workflow" / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text()
        assert "speculate-workflow" in content
        assert "/speculate:test" in content

    def test_include_pattern_filters_shortcuts(self, tmp_path: Path):
        """Include pattern should filter which shortcuts are linked."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:new-plan-spec.md").write_text("# Plan")
        (shortcuts_dir / "shortcut:commit-code.md").write_text("# Commit")

        _setup_claude_plugin(tmp_path, include=["shortcut:new-*.md"])

        commands_dir = tmp_path / CLAUDE_PLUGIN_DIR / "commands"
        assert (commands_dir / "new-plan-spec.md").exists()
        assert not (commands_dir / "commit-code.md").exists()

    def test_exclude_pattern_filters_shortcuts(self, tmp_path: Path):
        """Exclude pattern should filter out matching shortcuts."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:new-plan-spec.md").write_text("# Plan")
        (shortcuts_dir / "shortcut:commit-code.md").write_text("# Commit")

        _setup_claude_plugin(tmp_path, exclude=["shortcut:commit-*.md"])

        commands_dir = tmp_path / CLAUDE_PLUGIN_DIR / "commands"
        assert (commands_dir / "new-plan-spec.md").exists()
        assert not (commands_dir / "commit-code.md").exists()

    def test_skips_existing_symlinks_without_force(self, tmp_path: Path):
        """Should skip existing symlinks unless force=True."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        # First run creates the symlink
        _setup_claude_plugin(tmp_path)
        link = tmp_path / CLAUDE_PLUGIN_DIR / "commands" / "test.md"
        assert link.is_symlink()

        # Second run should skip
        _setup_claude_plugin(tmp_path)
        assert link.is_symlink()

    def test_overwrites_with_force(self, tmp_path: Path):
        """Should overwrite existing symlinks when force=True."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        # First run
        _setup_claude_plugin(tmp_path)

        # Second run with force
        _setup_claude_plugin(tmp_path, force=True)
        link = tmp_path / CLAUDE_PLUGIN_DIR / "commands" / "test.md"
        assert link.is_symlink()

    def test_collects_from_agent_setup(self, tmp_path: Path):
        """Should also collect shortcuts from agent-setup directory."""
        setup_dir = tmp_path / "docs" / "general" / "agent-setup"
        setup_dir.mkdir(parents=True)
        (setup_dir / "shortcut:setup-beads.md").write_text("# Setup")

        _setup_claude_plugin(tmp_path)

        commands_dir = tmp_path / CLAUDE_PLUGIN_DIR / "commands"
        assert (commands_dir / "setup-beads.md").is_symlink()

    def test_project_shortcuts_override_general(self, tmp_path: Path):
        """Project shortcuts should take precedence over general shortcuts."""
        general_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        general_dir.mkdir(parents=True)
        (general_dir / "shortcut:test.md").write_text("# General")

        project_dir = tmp_path / "docs" / "project" / "agent-shortcuts"
        project_dir.mkdir(parents=True)
        (project_dir / "shortcut:test.md").write_text("# Project")

        _setup_claude_plugin(tmp_path)

        link = tmp_path / CLAUDE_PLUGIN_DIR / "commands" / "test.md"
        target = os.readlink(link)
        assert "docs/project/agent-shortcuts" in target

    def test_warns_when_no_shortcuts(self, tmp_path: Path):
        """Should warn and skip when no shortcuts are found."""
        # No shortcuts exist
        _setup_claude_plugin(tmp_path)

        # Plugin directory should not be created
        assert not (tmp_path / CLAUDE_PLUGIN_DIR).exists()


class TestRemoveClaudePlugin:
    """Tests for _remove_claude_plugin function."""

    def test_removes_plugin_directory(self, tmp_path: Path):
        """Should remove the plugin directory."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        _setup_claude_plugin(tmp_path)
        assert (tmp_path / CLAUDE_PLUGIN_DIR).exists()

        _remove_claude_plugin(tmp_path)
        assert not (tmp_path / CLAUDE_PLUGIN_DIR).exists()

    def test_cleans_up_empty_parent_directories(self, tmp_path: Path):
        """Should clean up empty .claude/plugins/ if no other plugins."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        _setup_claude_plugin(tmp_path)
        _remove_claude_plugin(tmp_path)

        # .claude/plugins/ should be removed if empty
        plugins_dir = tmp_path / ".claude" / "plugins"
        assert not plugins_dir.exists()

    def test_preserves_other_plugins(self, tmp_path: Path):
        """Should not remove other plugins in .claude/plugins/."""
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        _setup_claude_plugin(tmp_path)

        # Create another plugin
        other_plugin = tmp_path / ".claude" / "plugins" / "other-plugin"
        other_plugin.mkdir(parents=True)
        (other_plugin / "plugin.json").write_text("{}")

        _remove_claude_plugin(tmp_path)

        # Other plugin should still exist
        assert other_plugin.exists()
        # .claude/plugins/ should still exist
        assert (tmp_path / ".claude" / "plugins").exists()

    def test_no_error_if_plugin_missing(self, tmp_path: Path):
        """Should not raise error if plugin doesn't exist."""
        # Should not raise
        _remove_claude_plugin(tmp_path)


class TestInstallWithClaudePlugin:
    """Tests for install command including Claude plugin."""

    def test_creates_claude_plugin(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should create Claude Code plugin during install."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        monkeypatch.chdir(tmp_path)
        install()

        assert (tmp_path / CLAUDE_PLUGIN_DIR).exists()
        assert (tmp_path / CLAUDE_PLUGIN_DIR / "commands" / "test.md").is_symlink()


class TestUninstallWithClaudePlugin:
    """Tests for uninstall command including Claude plugin."""

    def test_removes_claude_plugin(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should remove Claude Code plugin during uninstall."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        shortcuts_dir = tmp_path / "docs" / "general" / "agent-shortcuts"
        shortcuts_dir.mkdir(parents=True)
        (shortcuts_dir / "shortcut:test.md").write_text("# Test")

        monkeypatch.chdir(tmp_path)
        install()

        assert (tmp_path / CLAUDE_PLUGIN_DIR).exists()

        uninstall(force=True)

        assert not (tmp_path / CLAUDE_PLUGIN_DIR).exists()
