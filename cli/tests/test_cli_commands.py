"""Tests for CLI commands."""

import os
from pathlib import Path

import pytest
import yaml
from pytest import MonkeyPatch

from speculate.cli.cli_commands import (
    _setup_cursor_rules,
    _update_speculate_settings,
    install,
    status,
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
        """Should read docs version from .copier-answers.yml."""
        copier_answers = tmp_path / ".copier-answers.yml"
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


class TestStatusCommand:
    """Tests for status command."""

    def test_fails_without_development_md(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should fail if development.md is missing."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            status()
        assert exc_info.value.code == 1

    def test_succeeds_with_development_md(self, tmp_path: Path, monkeypatch: MonkeyPatch):
        """Should succeed if development.md exists."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "development.md").write_text("# Development")

        monkeypatch.chdir(tmp_path)

        # Should not raise
        status()
