"""Test the CLI of the ``dir-content-diff`` package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import json
import logging
import re

import pytest
import yaml

import dir_content_diff
import dir_content_diff.cli


class TestCli:
    """Tests of the CLI."""

    @pytest.fixture
    def config(self, tmp_path):
        """The config as a dict."""
        return {"file.pdf": {"tempdir": str(tmp_path)}}

    @pytest.fixture
    def config_tree_json(self, config):
        """The config as a JSON string."""
        return json.dumps(config)

    @pytest.fixture
    def config_file_json(self, config):
        """The config as a JSON string."""
        return json.dumps(config["file.pdf"])

    @pytest.fixture
    def config_tree_yaml(self, config, tmp_path):
        """The config as a YAML file."""
        filepath = tmp_path / "config_tree.yaml"
        with filepath.open("w", encoding="utf-8") as f:
            yaml.dump(config, f)
        return filepath

    @pytest.fixture
    def config_file_yaml(self, config, tmp_path):
        """The config as a YAML file."""
        filepath = tmp_path / "config_file.yaml"
        with filepath.open("w", encoding="utf-8") as f:
            yaml.dump(config["file.pdf"], f)
        return filepath

    @pytest.fixture
    def config_tree_str(self, request):
        """The string given to the CLI to pass the config."""
        return request.getfixturevalue(request.param)

    @pytest.fixture
    def config_file_str(self, request):
        """The string given to the CLI to pass the config."""
        return request.getfixturevalue(request.param)

    def test_help(self, cli_runner):
        """Test the --help option."""
        result = cli_runner.invoke(dir_content_diff.cli.main, ["--help"])
        assert "A command line tool for directory or file comparison." in result.stdout

    @pytest.mark.parametrize(
        "config_tree_str,config_file_str",
        [
            ["config_tree_json", "config_file_json"],
            ["config_tree_yaml", "config_file_yaml"],
        ],
        indirect=True,
    )
    def test_equal_tree(
        self,
        tmp_path,
        ref_tree,
        res_tree_equal,
        config_tree_str,
        config_file_str,
        cli_runner,
        caplog,
    ):
        """Test with equal trees."""
        caplog.set_level(logging.INFO, logger="dir-content-diff")

        # Test with trees
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [str(ref_tree), str(res_tree_equal), "--config", config_tree_str],
            catch_exceptions=False,
        )
        assert result.stdout == ""
        assert caplog.messages == [
            f"No difference found between '{ref_tree}' and '{res_tree_equal}'"
        ]
        assert (tmp_path / "diff-pdf" / "file.pdf" / "diff-1.png").exists()

        # Test with files
        caplog.clear()
        ref_file = ref_tree / "file.pdf"
        res_file = res_tree_equal / "file.pdf"
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [str(ref_file), str(res_file), "--config", config_file_str],
            catch_exceptions=False,
        )
        assert result.stdout == ""
        assert caplog.messages == [
            f"No difference found between '{ref_file}' and '{res_file}'"
        ]
        assert (tmp_path / "diff-pdf" / "file.pdf" / "diff-1.png").exists()

    @pytest.mark.parametrize(
        "config_tree_str,config_file_str",
        [
            ["config_tree_json", "config_file_json"],
            ["config_tree_yaml", "config_file_yaml"],
        ],
        indirect=True,
    )
    def test_diff_tree(
        self,
        tmp_path,
        ref_tree,
        res_tree_diff,
        config_tree_str,
        config_file_str,
        cli_runner,
        caplog,
    ):
        """Test with different trees."""
        caplog.set_level(logging.INFO, logger="dir-content-diff")

        # Test with trees
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [
                str(ref_tree),
                str(res_tree_diff),
                "--config",
                config_tree_str,
                "--sort-diffs",
                "--export-formatted-files",
            ],
        )
        assert result.stdout == ""
        assert len(caplog.messages) == 1
        assert (
            f"Differences found between '{ref_tree}' and '{res_tree_diff}':"
            in caplog.messages[0]
        )
        for i in ref_tree.iterdir():
            ref_file = (ref_tree / "file").with_suffix(i.suffix)
            res_file = (res_tree_diff / "file").with_suffix(i.suffix)
            assert (
                f"The files '{ref_file}' and '{res_file}' are different:"
                in caplog.messages[0]
            )
        assert (tmp_path / "diff-pdf" / "file.pdf" / "diff-1.png").exists()

        # Test with files
        caplog.clear()
        ref_file = ref_tree / "file.pdf"
        res_file = res_tree_diff / "file.pdf"
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [str(ref_file), str(res_file), "--config", config_file_str],
            catch_exceptions=False,
        )
        assert result.stdout == ""
        assert len(caplog.messages) == 1
        assert (
            f"Differences found between '{ref_file}' and '{res_file}':"
            in caplog.messages[0]
        )
        assert (tmp_path / "diff-pdf" / "file.pdf" / "diff-1.png").exists()

        # Test with files and formatted files
        caplog.set_level(logging.DEBUG, logger="dir-content-diff")
        caplog.clear()
        ref_file = ref_tree / "file.json"
        res_file = res_tree_diff / "file.json"
        result = cli_runner.invoke(
            dir_content_diff.cli.main,
            [str(ref_file), str(res_file), "--config", config_file_str, "-f"],
            catch_exceptions=False,
        )
        assert result.stdout == ""
        nb_format_msg = 0
        for i in caplog.messages:
            if not i.startswith("Format:"):
                continue
            match = re.match(r"Format: \S+ into \S+", i)
            assert match is not None
            nb_format_msg += 1
        assert nb_format_msg == 2
        assert (tmp_path / "ref" / "file_FORMATTED.json").exists()
        assert (tmp_path / "res" / "file_FORMATTED.json").exists()

    class TestFailures:
        """Test that the proper exceptions are raised."""

        def test_dir_file(self, cli_runner, ref_tree, res_tree_diff):
            """Test exception when comparing a directory with a file."""
            ref_file = ref_tree / "file.pdf"
            res_file = res_tree_diff / "file.pdf"
            with pytest.raises(
                ValueError,
                match=(
                    r"The reference and compared inputs must both be either two directories or two"
                    r" files\."
                ),
            ):
                cli_runner.invoke(
                    dir_content_diff.cli.main,
                    [str(ref_tree), str(res_file)],
                    catch_exceptions=False,
                )
            with pytest.raises(
                ValueError,
                match=(
                    r"The reference and compared inputs must both be either two directories or two"
                    r" files\."
                ),
            ):
                cli_runner.invoke(
                    dir_content_diff.cli.main,
                    [str(ref_file), str(res_tree_diff)],
                    catch_exceptions=False,
                )

        def test_not_existing_config(self, cli_runner):
            """Test exception when the config file does not exist."""
            with pytest.raises(
                FileNotFoundError,
                match=r"The file '/NOT/EXISTING/FILE' does not exist\.",
            ):
                cli_runner.invoke(
                    dir_content_diff.cli.main,
                    ["/A/FILE", "/ANOTHER/FILE", "--config", "/NOT/EXISTING/FILE"],
                    catch_exceptions=False,
                )

        def test_bad_yaml_config(self, tmp_path, cli_runner):
            """Test exception when the config file does not exist."""
            filepath = tmp_path / "config_file.yaml"
            with filepath.open("w", encoding="utf-8") as f:
                f.write("entry: &A !!!")

            with pytest.raises(
                SyntaxError,
                match=(
                    r"Could not load the configuration because it could not be parsed as a JSON "
                    r"string nor as a YAML file\."
                ),
            ):
                cli_runner.invoke(
                    dir_content_diff.cli.main,
                    ["/A/FILE", "/ANOTHER/FILE", "--config", str(filepath)],
                    catch_exceptions=False,
                )


def test_entry_point(script_runner):
    """Test the entry point."""
    ret = script_runner.run("dir-content-diff", "--version")
    assert ret.success
    assert "dir-content-diff, version " in ret.stdout
    assert ret.stderr == ""
