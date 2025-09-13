"""Utilities for parallel execution of file comparisons.

This module contains utility functions for collecting files, chunking work,
and managing parallel execution of file comparisons.
"""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

from pathlib import Path
from typing import Any
from typing import List
from typing import Tuple
from typing import Union

from dir_content_diff.config import ComparisonConfig
from dir_content_diff.util import LOGGER


def _collect_files_to_compare(ref_path: Path, config: ComparisonConfig):
    """Collect all files that need to be compared.

    Args:
        ref_path: Path to the reference directory.
        config: Comparison configuration.

    Yields:
        Tuples of (ref_file, relative_path) for files to compare.
    """
    for ref_file in ref_path.glob("**/*"):
        if ref_file.is_dir():
            continue

        relative_path = ref_file.relative_to(ref_path).as_posix()

        if config.should_ignore_file(relative_path):
            LOGGER.debug("Ignore file: %s", relative_path)
            continue

        yield ref_file, relative_path


def _compare_file_chunk(
    file_chunk: List[Tuple[Path, str]],
    config: ComparisonConfig,
    comp_path: Path,
    formatted_data_path: Path,
    compare_single_file_func,
) -> List[Tuple[str, Union[str, bool]]]:  # pragma: no cover
    """Compare a chunk of files.

    Args:
        file_chunk: List of file tuples to compare.
        config: Comparison configuration.
        comp_path: Path to the comparison directory.
        formatted_data_path: Path where formatted files should be exported.
        compare_single_file_func: Function to compare a single file.

    Returns:
        List of comparison results for the chunk.
    """
    results = []
    for ref_file, relative_path in file_chunk:
        try:
            result = compare_single_file_func(
                ref_file, comp_path, relative_path, config, formatted_data_path
            )
            results.append(result)
        except Exception as e:  # pylint: disable=broad-except
            LOGGER.error("Error comparing file %s: %s", relative_path, e)
            results.append((relative_path, f"Error comparing file: {e}"))
    return results


def _split_into_chunks(items: List[Any], num_chunks: int) -> List[List[Any]]:
    """Split a list of items into approximately equal chunks.

    Args:
        items: List of items to split.
        num_chunks: Desired number of chunks.

    Returns:
        List of chunks.
    """
    if num_chunks <= 0:
        return [items]

    chunk_size = max(1, len(items) // num_chunks)
    chunks = []

    for i in range(0, len(items), chunk_size):
        chunks.append(items[i : i + chunk_size])

    return chunks
