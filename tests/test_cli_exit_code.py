"""Test the CLI exit codes of the ``dir-content-diff`` package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2026 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import dir_content_diff.cli


class TestCliExitCode:
    """Tests of the CLI exit code, following the ``diff`` convention."""

    @staticmethod
    def _make_trees(tmp_path, ref_content, comp_content):
        """Create reference and compared directories with one text file each."""
        ref_tree = tmp_path / "ref"
        comp_tree = tmp_path / "comp"
        ref_tree.mkdir()
        comp_tree.mkdir()
        (ref_tree / "file.txt").write_text(ref_content, encoding="utf-8")
        (comp_tree / "file.txt").write_text(comp_content, encoding="utf-8")
        return ref_tree, comp_tree

    def test_equal_trees_exit_zero(self, tmp_path, cli_runner):
        """Test that the exit code is 0 when no difference is found."""
        ref_tree, comp_tree = self._make_trees(tmp_path, "same", "same")
        result = cli_runner.invoke(
            dir_content_diff.cli.main, [str(ref_tree), str(comp_tree)]
        )
        assert result.exit_code == 0

    def test_different_trees_exit_nonzero(self, tmp_path, cli_runner):
        """Test that the exit code is 1 when differences are found."""
        # NOTE: the contents must have different lengths: the default comparator
        # relies on ``filecmp.cmp`` with ``shallow=True``, so same-size files
        # created within the same mtime tick compare as equal.
        ref_tree, comp_tree = self._make_trees(tmp_path, "hello", "world!")
        result = cli_runner.invoke(
            dir_content_diff.cli.main, [str(ref_tree), str(comp_tree)]
        )
        assert result.exit_code == 1

    def test_different_files_exit_nonzero(self, tmp_path, cli_runner):
        """Test that the exit code is 1 when two files are different."""
        # NOTE: same as above, the contents must have different lengths.
        ref_tree, comp_tree = self._make_trees(tmp_path, "hello", "world!")
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [str(ref_tree / "file.txt"), str(comp_tree / "file.txt")],
        )
        assert result.exit_code == 1
