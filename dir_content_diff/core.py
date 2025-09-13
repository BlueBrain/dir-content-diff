"""Core comparison functionality.

This module contains the main comparison functions and configuration classes.
"""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import copy
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from typing import Tuple
from typing import Union

import attrs

from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.config import ComparisonConfig
from dir_content_diff.parallel_utils import _collect_files_to_compare
from dir_content_diff.parallel_utils import _compare_file_chunk
from dir_content_diff.parallel_utils import _split_into_chunks
from dir_content_diff.registry import _COMPARATORS
from dir_content_diff.registry import get_comparators
from dir_content_diff.util import LOGGER
from dir_content_diff.util import diff_msg_formatter

# Type alias for comparators
ComparatorType = Union[BaseComparator, Callable]

_DEFAULT_EXPORT_SUFFIX = "_FORMATTED"


def compare_files(
    ref_file: Union[str, Path],
    comp_file: Union[str, Path],
    comparator: ComparatorType,
    *args,
    return_raw_diffs: bool = False,
    **kwargs,
) -> Union[bool, str]:
    """Compare 2 files and return the difference.

    Args:
        ref_file: Path to the reference file.
        comp_file: Path to the compared file.
        comparator: The comparator to use (see in :func:`register_comparator` for the
            comparator signature).
        return_raw_diffs: If set to ``True``, only the raw differences are returned instead
            of a formatted report.
        *args: passed to the comparator.
        **kwargs: passed to the comparator.

    Returns:
        ``False`` if the files are equal or a string with a message explaining the
        differences if they are different.
    """
    # Get the compared file
    LOGGER.debug("Compare: %s and %s", ref_file, comp_file)

    try:
        return comparator(
            Path(ref_file),
            Path(comp_file),
            *args,
            return_raw_diffs=return_raw_diffs,
            **kwargs,
        )
    except Exception as exception:  # pylint: disable=broad-except
        load_kwargs = kwargs.pop("load_kwargs", None)
        format_data_kwargs = kwargs.pop("format_data_kwargs", None)
        filter_kwargs = kwargs.pop("filter_kwargs", None)
        format_diff_kwargs = kwargs.pop("format_diff_kwargs", None)
        sort_kwargs = kwargs.pop("sort_kwargs", None)
        concat_kwargs = kwargs.pop("concat_kwargs", None)
        report_kwargs = kwargs.pop("report_kwargs", None)
        try:
            exception_args = "\n".join(str(i) for i in exception.args)
        except Exception:  # pylint: disable=broad-exception-caught
            exception_args = (
                "UNKNOWN ERROR: Could not get information from the exception"
            )
        exc_type = type(exception).__name__
        return diff_msg_formatter(
            ref_file,
            comp_file,
            reason=f"Exception raised: ({exc_type}) {exception_args}",
            diff_args=args,
            diff_kwargs=kwargs,
            load_kwargs=load_kwargs,
            format_data_kwargs=format_data_kwargs,
            filter_kwargs=filter_kwargs,
            format_diff_kwargs=format_diff_kwargs,
            sort_kwargs=sort_kwargs,
            concat_kwargs=concat_kwargs,
            report_kwargs=report_kwargs,
        )


def export_formatted_file(
    file: Union[str, Path],
    formatted_file: Union[str, Path],
    comparator: ComparatorType,
    **kwargs,
) -> None:
    """Format a data file and export it.

    .. note:: A new file is created only if the corresponding comparator has saving capability.

    Args:
        file: Path to the compared file.
        formatted_file: Path to the formatted file.
        comparator: The comparator to use (see in :func:`register_comparator` for the
            comparator signature).
        **kwargs: Can contain the following dictionaries: 'load_kwargs', 'format_data_kwargs' and
            'save_kwargs'.
    """
    if hasattr(comparator, "save_capability") and comparator.save_capability:
        # pylint: disable=protected-access
        LOGGER.debug("Format: %s into %s", file, formatted_file)
        data = comparator.load(
            file,
            **kwargs.get(
                "load_kwargs",
                (
                    comparator._default_load_kwargs
                    if hasattr(comparator, "_default_load_kwargs")
                    else {}
                ),
            ),
        )
        formatted_data = comparator.format_data(
            data,
            **kwargs.get(
                "format_data_kwargs",
                (
                    comparator._default_format_data_kwargs
                    if hasattr(comparator, "_default_format_data_kwargs")
                    else {}
                ),
            ),
        )
        Path(formatted_file).parent.mkdir(parents=True, exist_ok=True)
        comparator.save(
            formatted_data,
            formatted_file,
            **kwargs.get(
                "save_kwargs",
                (
                    comparator._default_save_kwargs
                    if hasattr(comparator, "_default_save_kwargs")
                    else {}
                ),
            ),
        )
    else:
        LOGGER.debug(
            "Skip formatting for '%s' because the comparator has no saving capability.",
            file,
        )


def pick_comparator(comparator=None, suffix=None, comparators=None):
    """Pick a comparator based on its name or a file suffix."""
    if isinstance(comparator, BaseComparator):
        return comparator
    if comparators is None:
        comparators = get_comparators()
    if comparator is not None:
        for i in comparators.values():  # pragma: no branch
            if i.__class__.__name__ == comparator:
                return i
        LOGGER.debug(
            "Could not find the comparator named '%s' in the given comparators",
            comparator,
        )
    if suffix is not None:
        if suffix in comparators:
            suffix_comparator = comparators.get(suffix)
            if suffix_comparator is not None:
                return suffix_comparator
        LOGGER.debug("Could not find the comparator for the '%s' suffix", suffix)
    LOGGER.debug("Returning the default comparator")
    # Use the global registry directly for the default comparator
    # to ensure tests that modify _COMPARATORS work correctly
    default_comparator = _COMPARATORS.get(None)
    if default_comparator is None:
        raise RuntimeError("No default comparator available")
    return default_comparator


def _check_config(config=None, **kwargs):
    """Process configuration."""
    if config is not None:
        if kwargs:
            # Override config attributes with kwargs
            config = attrs.evolve(config, **kwargs)
    else:
        config = ComparisonConfig(**kwargs)

    return config


def _compare_single_file(
    ref_file: Path,
    comp_path: Path,
    relative_path: str,
    config: ComparisonConfig,
    formatted_data_path: Path,
) -> Tuple[str, Union[str, bool]]:
    """Compare a single file and optionally export formatted version.

    Args:
        ref_file: Path to the reference file.
        comp_file: Path to the comparison file.
        relative_path: Relative path of the file from the reference directory.
        config: Comparison configuration.
        formatted_data_path: Path where formatted files should be exported.

    Returns:
        A tuple containing the relative path and the comparison result.
        The result is False if files are equal, or a string describing differences.
    """
    comp_file = comp_path / relative_path
    if not comp_file.exists():
        msg = f"The file '{relative_path}' does not exist in '{comp_path}'."
        return relative_path, msg

    # Get specific arguments for this file
    specific_file_args = (config.specific_args or {}).get(relative_path, None)
    if specific_file_args is None:
        for pattern, pattern_args in config.pattern_specific_args.items():
            if pattern.match(relative_path):
                specific_file_args = copy.deepcopy(pattern_args)
                break
    if specific_file_args is None:
        specific_file_args = {}

    # Pick the appropriate comparator
    comparator = pick_comparator(
        comparator=specific_file_args.pop("comparator", None),
        suffix=ref_file.suffix,
        comparators=config.comparators,
    )

    # Get comparator arguments
    comparator_args = specific_file_args.pop("args", [])

    # Compare files
    comparison_result = compare_files(
        ref_file,
        comp_file,
        comparator,
        *comparator_args,
        return_raw_diffs=config.return_raw_diffs,
        **specific_file_args,
    )

    # Export formatted file if requested
    if config.export_formatted_files is not False:
        export_formatted_file(
            comp_file,
            formatted_data_path / relative_path,
            comparator,
            **specific_file_args,
        )

    return relative_path, comparison_result


def compare_trees(
    ref_path: Union[str, Path],
    comp_path: Union[str, Path],
    *,
    config: Optional[ComparisonConfig] = None,
    **kwargs,
):
    """Compare all files from 2 different directory trees and return the differences.

    .. note::

        The comparison only considers the files found in the reference directory. So if there are
        files in the compared directory that do not exist in the reference directory, they are just
        ignored.

    Args:
        ref_path: Path to the reference directory.
        comp_path: Path to the directory that must be compared against the reference.
        config (ComparisonConfig): A config object. If given, all other configuration parameters
            should be set to default values.

    Keyword Args:
        **kwargs (dict): Additional keyword arguments are used to build a ComparisonConfig object
            and will override the values of the given `config` argument.

    Returns:
        dict: A ``dict`` in which the keys are the relative file paths and the values are the
        difference messages. If the directories are considered as equal, an empty ``dict`` is
        returned.
    """
    config = _check_config(config, **kwargs)

    ref_path = Path(ref_path)
    comp_path = Path(comp_path)
    formatted_data_path = comp_path.with_name(
        comp_path.name
        + (
            config.export_formatted_files
            if (
                config.export_formatted_files is not True
                and config.export_formatted_files
            )
            else _DEFAULT_EXPORT_SUFFIX
        )
    )

    # Collect all files to compare
    files_to_compare = list(_collect_files_to_compare(ref_path, config))

    different_files = {}

    if config.executor_type != "sequential" and len(files_to_compare) > 1:
        # Parallel execution
        executor_class = (
            ThreadPoolExecutor
            if config.executor_type == "thread"
            else ProcessPoolExecutor
        )
        LOGGER.debug(
            "Starting parallel comparison of %d files with %s(max_workers=%s)",
            len(files_to_compare),
            executor_class.__name__,
            config.max_workers,
        )

        # Determine max_workers with default fallback
        actual_max_workers = config.max_workers
        if actual_max_workers is None:
            actual_max_workers = min(32, (os.cpu_count() or 1) + 4)

        with executor_class(max_workers=actual_max_workers) as executor:
            if config.executor_type == "process":
                # For ProcessPoolExecutor, use chunk-based approach for better performance
                file_chunks = _split_into_chunks(files_to_compare, actual_max_workers)

                future_to_chunk = {
                    executor.submit(
                        _compare_file_chunk,
                        chunk,
                        config,
                        comp_path,
                        formatted_data_path,
                        _compare_single_file,
                    ): chunk
                    for chunk in file_chunks
                    if chunk  # Skip empty chunks
                }

                # Collect results from chunks
                for future in future_to_chunk:
                    try:
                        chunk_results = future.result()
                        for relative_path, result in chunk_results:
                            if result:
                                different_files[relative_path] = result
                    except Exception as e:  # pragma: no cover
                        LOGGER.error("Error in chunk processing: %s", e)
                        raise

            else:
                # For ThreadPoolExecutor, submit individual files (better load balancing)
                future_to_file = {
                    executor.submit(
                        _compare_single_file,
                        ref_file,
                        comp_path,
                        relative_path,
                        config,
                        formatted_data_path,
                    ): relative_path
                    for ref_file, relative_path in files_to_compare
                }

                # Collect results as they complete
                for future in future_to_file:
                    try:
                        relative_path, result = future.result()
                        if result:
                            different_files[relative_path] = result
                    except Exception as e:  # pragma: no cover
                        LOGGER.error(
                            "Error comparing file %s: %s", future_to_file[future], e
                        )
                        raise
    else:
        # Sequential execution (original behavior)
        LOGGER.debug(
            "Starting sequential comparison of %d files", len(files_to_compare)
        )

        for ref_file, relative_path in files_to_compare:
            try:
                _, result = _compare_single_file(
                    ref_file, comp_path, relative_path, config, formatted_data_path
                )
                if result is not False:
                    different_files[relative_path] = result
            except Exception as exc:  # pragma: no cover
                LOGGER.error("File comparison failed for %s: %s", relative_path, exc)
                raise

    return different_files


def assert_equal_trees(*args, export_formatted_files=False, **kwargs):
    """Raise an :class:`AssertionError` if differences are found in the two directory trees.

    .. note::
        This function has a specific behavior when run with pytest. See the doc of the
        :mod:`dir_content_diff.pytest_plugin`.

    Args:
        *args: passed to the :func:`compare_trees` function.
        export_formatted_files (bool, or str): If set to ``True``, the formatted files are exported
            to the directory with the default suffix. If set to a string, it is used as suffix for
            the new directory.
        **kwargs: passed to the :func:`compare_trees` function.

    Returns:
        (bool) ``True`` if the trees are equal. If they are not, an :class:`AssertionError` is
        raised.
    """
    # If run with pytest, get the trigger to export formatted data from it
    if export_formatted_files is False and hasattr(
        assert_equal_trees, "_pytest_export_formatted_data"
    ):
        # pylint: disable=no-member
        # pylint: disable=protected-access
        export_formatted_files = assert_equal_trees._pytest_export_formatted_data
        if export_formatted_files is True and assert_equal_trees._pytest_export_suffix:
            export_formatted_files = assert_equal_trees._pytest_export_suffix

    different_files = compare_trees(
        *args, export_formatted_files=export_formatted_files, **kwargs
    )

    # Sort the files according to their relative paths
    sorted_items = sorted(different_files.items(), key=lambda x: x[0])
    # Test that all files are equal and raise the formatted messages if there are differences
    if len(sorted_items) > 0:
        raise AssertionError("\n\n\n".join([i[1] for i in sorted_items]))

    # Return True if the trees are equal
    return True
