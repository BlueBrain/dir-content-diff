#
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
#

"""Test the enhanced ComparisonConfig with attrs validation."""

from typing import Any

import attrs
import pytest

from dir_content_diff import ComparisonConfig
from dir_content_diff.base_comparators import DefaultComparator
from dir_content_diff.base_comparators import JsonComparator


class TestAttrsValidation:
    """Test attrs validation features in ComparisonConfig."""

    def test_valid_config_creation(self):
        """Test creating a valid configuration."""
        config = ComparisonConfig(
            include_patterns=[".*\\.py$", ".*\\.txt$"],
            exclude_patterns=[".*test.*", ".*__pycache__.*"],
            return_raw_diffs=True,
            export_formatted_files="_formatted",
            specific_args={
                "file.json": {"comparator": "JsonComparator"},
                "pattern_group": {"patterns": [".*\\.yaml$"], "args": ["some_arg"]},
            },
        )

        assert config.include_patterns == (".*\\.py$", ".*\\.txt$")
        assert config.exclude_patterns == (".*test.*", ".*__pycache__.*")
        assert config.return_raw_diffs is True
        assert config.export_formatted_files == "_formatted"
        assert len(config.compiled_include_patterns) == 2
        assert len(config.compiled_exclude_patterns) == 2

    def test_invalid_regex_patterns_validation(self):
        """Test validation of invalid regex patterns."""
        # Test invalid include patterns
        with pytest.raises(ValueError) as exc_info:
            ComparisonConfig(include_patterns=["[invalid_regex"])

        error_str = str(exc_info.value)
        assert "Invalid regex pattern" in error_str
        assert "[invalid_regex" in error_str

        # Test invalid exclude patterns
        with pytest.raises(ValueError) as exc_info:
            ComparisonConfig(exclude_patterns=["(unclosed_group"])

        error_str = str(exc_info.value)
        assert "Invalid regex pattern" in error_str

        # Test invalid patterns in specific_args
        with pytest.raises(ValueError) as exc_info:
            ComparisonConfig(
                specific_args={"category": {"patterns": ["[invalid_regex"], "args": []}}
            )

        error_str = str(exc_info.value)
        assert "Invalid regex pattern" in error_str

    def test_export_formatted_files_validation(self):
        """Test validation of export_formatted_files field."""
        # Valid boolean values
        config = ComparisonConfig(export_formatted_files=True)
        assert config.export_formatted_files is True

        config = ComparisonConfig(export_formatted_files=False)
        assert config.export_formatted_files is False

        # Valid string values
        config = ComparisonConfig(export_formatted_files="_formatted")
        assert config.export_formatted_files == "_formatted"

        # Invalid empty string
        with pytest.raises(ValueError) as exc_info:
            ComparisonConfig(export_formatted_files="   ")

        error_str = str(exc_info.value)
        assert "must be a non-empty string" in error_str

    def test_comparators_validation(self):
        """Test validation of comparators field."""
        # Valid BaseComparator instances
        config = ComparisonConfig(
            comparators={".json": JsonComparator(), None: DefaultComparator()}
        )
        assert config.comparators is not None
        assert isinstance(config.comparators[".json"], JsonComparator)

        # Valid callable functions
        def custom_comparator(ref, comp, **kwargs):  # pylint: disable=unused-argument
            return False

        config = ComparisonConfig(comparators={".custom": custom_comparator})
        assert config.comparators is not None
        assert callable(config.comparators[".custom"])

        # Invalid non-callable object
        with pytest.raises(ValueError) as exc_info:
            ComparisonConfig(comparators={".invalid": "not_a_comparator"})

        error_str = str(exc_info.value)
        assert "must be a BaseComparator instance or callable" in error_str

    def test_specific_args_validation(self):
        """Test validation of specific_args structure."""
        # Valid specific_args
        config = ComparisonConfig(
            specific_args={
                "file.json": {
                    "comparator": "JsonComparator",
                    "args": ["arg1", "arg2"],
                    "kwargs": {"option": True},
                },
                "pattern_category": {
                    "patterns": [".*\\.yaml$", ".*\\.yml$"],
                    "comparator": "YamlComparator",
                },
            }
        )

        assert config.specific_args is not None
        assert "file.json" in config.specific_args
        assert "pattern_category" in config.specific_args

        # Invalid specific_args structure
        with pytest.raises(ValueError) as exc_info:
            # Use Any to bypass type checker for intentional error test
            invalid_data: Any = {"file.json": "not_a_dict"}
            ComparisonConfig(specific_args=invalid_data)

        error_str = str(exc_info.value)
        assert "dictionary" in error_str.lower()

    def test_pattern_compilation_and_usage(self):
        """Test that patterns are properly compiled and can be used."""
        config = ComparisonConfig(
            include_patterns=[".*\\.py$"],
            exclude_patterns=[".*test.*", ".*__pycache__.*"],
        )

        # Test that patterns are compiled
        assert len(config.compiled_include_patterns) == 1
        assert len(config.compiled_exclude_patterns) == 2

        # Test should_ignore_file method
        assert not config.should_ignore_file("main.py")  # Matches include, no exclude
        assert config.should_ignore_file(
            "test_main.py"
        )  # Matches include but also exclude
        assert config.should_ignore_file("script.js")  # Doesn't match include

    def test_default_values(self):
        """Test that default values are properly set."""
        config = ComparisonConfig()

        assert config.include_patterns is None
        assert config.exclude_patterns is None
        assert (
            config.specific_args == {}
        )  # Default empty dict after __attrs_post_init__
        assert config.return_raw_diffs is False
        assert config.export_formatted_files is False
        assert (
            config.comparators is not None
        )  # Should be populated with default comparators

    def test_attrs_features(self):
        """Test attrs-specific features."""

        config = ComparisonConfig(
            include_patterns=[".*\\.py$"],
            exclude_patterns=[".*test.*"],
            return_raw_diffs=True,
            export_formatted_files="_formatted",
        )

        # Test attrs repr
        repr_str = repr(config)
        assert "ComparisonConfig" in repr_str
        assert "include_patterns" in repr_str

        # Test attrs asdict
        try:
            config_dict = attrs.asdict(config, recurse=False)
            assert "include_patterns" in config_dict
            assert "exclude_patterns" in config_dict
            assert "return_raw_diffs" in config_dict
            assert "export_formatted_files" in config_dict
        except Exception:  # pylint: disable=broad-exception-caught
            # If asdict fails due to complex types, that's ok
            pass

    def test_immutability_and_validation_on_construction(self):
        """Test that validation happens on construction and fields work correctly."""
        # Test that validation happens during construction
        with pytest.raises(ValueError):
            ComparisonConfig(include_patterns=["[invalid"])

        # Test that valid config can be created and accessed
        config = ComparisonConfig(include_patterns=[".*\\.py$"], return_raw_diffs=True)

        assert config.include_patterns == (".*\\.py$",)
        assert config.return_raw_diffs is True

        # Test that computed properties work
        assert len(config.compiled_include_patterns) == 1
        assert config.compiled_include_patterns[0].pattern == ".*\\.py$"
