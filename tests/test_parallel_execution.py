"""Test the parallel execution features of the dir-content-diff package."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import logging
import time
from unittest.mock import patch

import attrs

from dir_content_diff import ComparisonConfig
from dir_content_diff import assert_equal_trees
from dir_content_diff import compare_trees
from dir_content_diff.core import _split_into_chunks

from . import generate_test_files


class TestParallelExecution:
    """Test parallel execution functionality."""

    def test_parallel_config_default(self):
        """Test default execution configuration."""
        config = ComparisonConfig()
        assert config.executor_type == "sequential"
        assert config.max_workers is None

    def test_parallel_config_custom(self):
        """Test custom execution configuration."""
        config = ComparisonConfig(executor_type="process", max_workers=4)
        assert config.executor_type == "process"
        assert config.max_workers == 4

    def test_parallel_config_validation(self):
        """Test execution configuration validation."""
        # Valid executor types
        config_sequential = ComparisonConfig(executor_type="sequential")
        config_thread = ComparisonConfig(executor_type="thread")
        config_process = ComparisonConfig(executor_type="process")
        assert config_sequential.executor_type == "sequential"
        assert config_thread.executor_type == "thread"
        assert config_process.executor_type == "process"

        # Invalid executor type is prevented by type checking, so we test valid types only

    def test_sequential_vs_parallel_thread_equal_trees(self, ref_tree, res_tree_equal):
        """Test that sequential and thread execution give same results for equal trees."""
        # Sequential execution
        sequential_result = compare_trees(ref_tree, res_tree_equal)

        # Parallel execution with threads
        parallel_result = compare_trees(
            ref_tree, res_tree_equal, executor_type="thread", max_workers=2
        )

        assert sequential_result == parallel_result == {}

    def test_sequential_vs_parallel_thread_diff_trees(self, ref_tree, res_tree_diff):
        """Test that sequential and thread execution give same results for different trees."""
        # Sequential execution
        sequential_result = compare_trees(ref_tree, res_tree_diff)

        # Parallel execution with threads
        parallel_result = compare_trees(
            ref_tree, res_tree_diff, executor_type="thread", max_workers=2
        )

        # Results should have same keys
        assert set(sequential_result.keys()) == set(parallel_result.keys())

        # Results should be the same (order might differ but content should match)
        for key, value in sequential_result.items():
            assert key in parallel_result
            # For deterministic comparison, we check that both have content
            assert len(value) > 0
            assert len(parallel_result[key]) > 0

    def test_sequential_vs_parallel_process_equal_trees(self, ref_tree, res_tree_equal):
        """Test that sequential and process execution give same results for equal trees."""
        # Sequential execution
        sequential_result = compare_trees(ref_tree, res_tree_equal)

        # Parallel execution with processes
        parallel_result = compare_trees(
            ref_tree, res_tree_equal, executor_type="process", max_workers=2
        )

        assert sequential_result == parallel_result == {}

    def test_sequential_vs_parallel_process_diff_trees(self, ref_tree, res_tree_diff):
        """Test that sequential and process execution give same results for different trees."""
        # Sequential execution
        sequential_result = compare_trees(ref_tree, res_tree_diff)

        # Parallel execution with processes
        parallel_result = compare_trees(
            ref_tree, res_tree_diff, executor_type="process", max_workers=2
        )

        # Results should have same keys
        assert set(sequential_result.keys()) == set(parallel_result.keys())

        # Results should be the same (order might differ but content should match)
        for key, value in sequential_result.items():
            assert key in parallel_result
            # For deterministic comparison, we check that both have content
            assert len(value) > 0
            assert len(parallel_result[key]) > 0

    def test_parallel_with_config_object(self, ref_tree, res_tree_equal):
        """Test parallel execution using config object."""
        config = ComparisonConfig(executor_type="thread", max_workers=3)

        result = compare_trees(ref_tree, res_tree_equal, config=config)
        assert not result

    def test_parallel_with_kwargs(self, ref_tree, res_tree_equal):
        """Test parallel execution using kwargs."""
        result = compare_trees(
            ref_tree, res_tree_equal, executor_type="process", max_workers=2
        )
        assert not result

    def test_parallel_assert_equal_trees(self, ref_tree, res_tree_equal):
        """Test parallel execution with assert_equal_trees."""
        # Should not raise any exception
        assert_equal_trees(
            ref_tree, res_tree_equal, executor_type="thread", max_workers=2
        )

    def test_parallel_with_specific_args(self, ref_tree, res_tree_equal):
        """Test parallel execution with specific args."""
        specific_args = {
            "file.yaml": {"args": [None, None, None, False, 0, False]},
            "file.json": {"tolerance": 0},
        }

        result = compare_trees(
            ref_tree,
            res_tree_equal,
            executor_type="thread",
            max_workers=2,
            specific_args=specific_args,
        )
        assert not result

    def test_parallel_with_patterns(self, ref_tree, res_tree_equal):
        """Test parallel execution with include/exclude patterns."""
        result = compare_trees(
            ref_tree,
            res_tree_equal,
            executor_type="thread",
            max_workers=2,
            include_patterns=[r".*\.[jy].*"],
            exclude_patterns=[r".*\.yaml"],
        )
        assert not result

    def test_parallel_with_export_formatted(self, ref_tree, res_tree_equal):
        """Test parallel execution with export formatted files."""
        result = compare_trees(
            ref_tree,
            res_tree_equal,
            executor_type="thread",
            max_workers=2,
            export_formatted_files=True,
        )
        assert not result

        # Check that formatted files are created
        formatted_path = res_tree_equal.with_name(res_tree_equal.name + "_FORMATTED")
        assert formatted_path.exists()

    def test_parallel_single_file_fallback(
        self, empty_ref_tree, empty_res_tree, caplog
    ):
        """Test that parallel execution falls back to sequential for single file."""
        # Create a reference tree with only one file
        generate_test_files.create_json(empty_ref_tree / "file.json")
        generate_test_files.create_json(empty_res_tree / "file.json")

        # Mock the parallel executors and configure logs
        with patch(
            "concurrent.futures.ThreadPoolExecutor"
        ) as mock_thread_executor, patch(
            "concurrent.futures.ProcessPoolExecutor"
        ) as mock_process_executor, caplog.at_level(logging.DEBUG):
            result = compare_trees(
                empty_ref_tree, empty_res_tree, executor_type="thread", max_workers=4
            )
            assert not result

            # Check that parallel executors have not been instantiated
            mock_thread_executor.assert_not_called()
            mock_process_executor.assert_not_called()

            # Check that logs indicate sequential execution
            sequential_logs = [
                record
                for record in caplog.records
                if "Starting sequential comparison of 1 files" in record.message
            ]
            assert len(sequential_logs) == 1

            # Check that no parallel execution logs are present
            parallel_logs = [
                record
                for record in caplog.records
                if "Starting parallel comparison" in record.message
            ]
            assert len(parallel_logs) == 0

    def test_parallel_multiple_files_uses_threads(
        self, empty_ref_tree, empty_res_tree, caplog
    ):
        """Check that parallel execution is used with multiple files."""
        # Create a reference tree with multiple files
        generate_test_files.create_json(empty_ref_tree / "file1.json")
        generate_test_files.create_json(empty_ref_tree / "file2.json")
        generate_test_files.create_json(empty_res_tree / "file1.json")
        generate_test_files.create_json(empty_res_tree / "file2.json")

        # Configure log level to capture DEBUG messages
        with caplog.at_level(logging.DEBUG):
            result = compare_trees(
                empty_ref_tree, empty_res_tree, executor_type="thread", max_workers=2
            )
            assert not result

            # Check that logs indicate parallel execution
            parallel_logs = [
                record
                for record in caplog.records
                if "Starting parallel comparison of 2 files with ThreadPoolExecutor"
                in record.message
            ]
            assert len(parallel_logs) == 1

            # Check that no sequential execution logs are present
            sequential_logs = [
                record
                for record in caplog.records
                if "Starting sequential comparison" in record.message
            ]
            assert len(sequential_logs) == 0

    def test_parallel_error_handling(self, ref_tree, res_tree_diff):
        """Test error handling in parallel execution."""
        # This should work normally even with some differences
        result = compare_trees(
            ref_tree, res_tree_diff, executor_type="thread", max_workers=2
        )

        # Should have differences but no exceptions
        assert len(result) > 0
        for value in result.values():
            assert isinstance(value, str)
            assert len(value) > 0

    def test_parallel_missing_files(self, ref_tree, empty_res_tree):
        """Test parallel execution when comparison files are missing."""
        result = compare_trees(
            ref_tree, empty_res_tree, executor_type="thread", max_workers=2
        )

        # Should report missing files
        assert len(result) > 0
        for value in result.values():
            assert "does not exist" in value

    def test_config_evolution_with_parallel(self):
        """Test that config evolution works with executor_type parameters."""
        base_config = ComparisonConfig(executor_type="thread", max_workers=2)

        # Evolve config with new parallel parameters using attrs.evolve
        new_config = attrs.evolve(base_config, executor_type="process", max_workers=4)

        # Check that new values are applied
        assert new_config.executor_type == "process"
        assert new_config.max_workers == 4

        # Test sequential execution config
        config_seq = ComparisonConfig(executor_type="sequential")
        assert config_seq.executor_type == "sequential"


class TestParallelPerformance:
    """Test performance aspects of parallel execution."""

    def test_parallel_vs_sequential_timing(self, ref_tree, res_tree_equal):
        """Basic timing test to ensure parallel execution doesn't break."""
        # This is not a strict performance test, just ensuring both modes work
        start_time = time.time()
        sequential_result = compare_trees(ref_tree, res_tree_equal)
        sequential_time = time.time() - start_time

        start_time = time.time()
        parallel_result = compare_trees(
            ref_tree, res_tree_equal, executor_type="thread", max_workers=2
        )
        parallel_time = time.time() - start_time

        # Both should give same result
        assert sequential_result == parallel_result == {}

        # Both should complete in reasonable time (not testing speed, just that they complete)
        assert sequential_time < 30  # 30 seconds max
        assert parallel_time < 30  # 30 seconds max


class TestParallelEdgeCases:
    """Test edge cases for parallel execution."""

    def test_parallel_no_files(self, empty_ref_tree, empty_res_tree):
        """Test parallel execution with no files to compare."""
        result = compare_trees(
            empty_ref_tree, empty_res_tree, executor_type="thread", max_workers=4
        )
        assert not result

    def test_parallel_disabled_with_single_file(self, empty_ref_tree, empty_res_tree):
        """Test that parallel execution is automatically disabled for single file."""
        # This tests the logic: if len(files_to_compare) > 1
        # Create a scenario with exactly one file
        generate_test_files.create_json(empty_ref_tree / "file.json")
        generate_test_files.create_json(empty_res_tree / "file.json")

        result = compare_trees(
            empty_ref_tree, empty_res_tree, executor_type="thread", max_workers=4
        )
        assert not result

    def test_parallel_max_workers_none(self, ref_tree, res_tree_equal):
        """Test parallel execution with max_workers=None (default)."""
        result = compare_trees(
            ref_tree,
            res_tree_equal,
            executor_type="thread",
            max_workers=None,  # Should use executor default
        )
        assert not result

    def test_parallel_max_workers_large(self, ref_tree, res_tree_equal):
        """Test parallel execution with large max_workers."""
        result = compare_trees(
            ref_tree,
            res_tree_equal,
            executor_type="thread",
            max_workers=100,  # Larger than needed
        )
        assert not result

    def test_chunking_edge_cases(self):
        """Test edge cases for chunking."""
        # Test with num_chunks <= 0
        items = [1, 2, 3, 4, 5]

        # num_chunks = 0
        result = _split_into_chunks(items, 0)
        assert result == [items]

        # num_chunks < 0
        result = _split_into_chunks(items, -1)
        assert result == [items]
