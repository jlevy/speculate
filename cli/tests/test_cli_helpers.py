"""Tests for CLI helper functions."""

from pathlib import Path

from speculate.cli.cli_commands import (
    SPECULATE_MARKER,
    _ensure_speculate_header,
    _get_dir_stats,
    _matches_patterns,
)


class TestGetDirStats:
    """Tests for _get_dir_stats function."""

    def test_empty_directory(self, tmp_path: Path):
        """Empty directory should return 0 files and 0 bytes."""
        file_count, total_size = _get_dir_stats(tmp_path)
        assert file_count == 0
        assert total_size == 0

    def test_single_file(self, tmp_path: Path):
        """Single file should be counted correctly."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        file_count, total_size = _get_dir_stats(tmp_path)
        assert file_count == 1
        assert total_size == 5

    def test_nested_files(self, tmp_path: Path):
        """Nested files should be counted recursively."""
        (tmp_path / "file1.txt").write_text("abc")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("defgh")
        file_count, total_size = _get_dir_stats(tmp_path)
        assert file_count == 2
        assert total_size == 8


class TestMatchesPatterns:
    """Tests for _matches_patterns function."""

    def test_no_patterns_matches_all(self):
        """No patterns should match all files."""
        assert _matches_patterns("any-file.md", None, None) is True

    def test_include_pattern_matches(self):
        """Include pattern should match matching files."""
        assert _matches_patterns("general-rules.md", ["general-*.md"], None) is True
        assert _matches_patterns("python-rules.md", ["general-*.md"], None) is False

    def test_exclude_pattern_excludes(self):
        """Exclude pattern should exclude matching files."""
        assert _matches_patterns("convex-rules.md", None, ["convex-*.md"]) is False
        assert _matches_patterns("general-rules.md", None, ["convex-*.md"]) is True

    def test_include_and_exclude_together(self):
        """Include and exclude patterns should work together."""
        # Matches include but also matches exclude -> excluded
        assert _matches_patterns("general-convex.md", ["general-*.md"], ["*convex*"]) is False
        # Matches include and doesn't match exclude -> included
        assert _matches_patterns("general-python.md", ["general-*.md"], ["*convex*"]) is True

    def test_double_star_pattern(self):
        """Double star pattern should be normalized to single star."""
        # ** becomes * so **rules.md matches anything-rules.md
        assert _matches_patterns("general-rules.md", ["**rules.md"], None) is True
        assert _matches_patterns("python-rules.md", ["**rules.md"], None) is True


class TestEnsureSpeculateHeader:
    """Tests for _ensure_speculate_header function."""

    def test_creates_new_file(self, tmp_path: Path):
        """Should create new file with header if it doesn't exist."""
        test_file = tmp_path / "CLAUDE.md"
        _ensure_speculate_header(test_file)

        assert test_file.exists()
        content = test_file.read_text()
        assert SPECULATE_MARKER in content
        assert content.startswith("IMPORTANT:")

    def test_prepends_to_existing_file(self, tmp_path: Path):
        """Should prepend header to existing file without marker."""
        test_file = tmp_path / "CLAUDE.md"
        original_content = "# My existing content\n"
        test_file.write_text(original_content)

        _ensure_speculate_header(test_file)

        content = test_file.read_text()
        assert SPECULATE_MARKER in content
        assert "# My existing content" in content
        # Header should come before original content
        assert content.index(SPECULATE_MARKER) < content.index("# My existing content")

    def test_idempotent_with_marker(self, tmp_path: Path):
        """Should not modify file if marker already present."""
        test_file = tmp_path / "CLAUDE.md"
        original_content = f"IMPORTANT: (This project uses {SPECULATE_MARKER}.)\n\n# Other content"
        test_file.write_text(original_content)

        _ensure_speculate_header(test_file)

        content = test_file.read_text()
        assert content == original_content

    def test_header_format(self, tmp_path: Path):
        """Header should match expected format."""
        test_file = tmp_path / "TEST.md"
        _ensure_speculate_header(test_file)

        content = test_file.read_text()
        assert "./docs/development.md" in content
        assert "./docs/docs-overview.md" in content
