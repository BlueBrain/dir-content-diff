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
import re
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Literal
from typing import Optional
from typing import Pattern
from typing import Tuple
from typing import Union

import attrs

from dir_content_diff.base_comparators import BaseComparator
from dir_content_diff.registry import _COMPARATORS
from dir_content_diff.registry import get_comparators
from dir_content_diff.util import LOGGER
from dir_content_diff.util import diff_msg_formatter

# Type alias for comparators
ComparatorType = Union[BaseComparator, Callable]

_DEFAULT_EXPORT_SUFFIX = "_FORMATTED"


def _convert_iterable_to_tuple(
    x: Optional[Iterable[str]],
) -> Optional[Tuple[str, ...]]:
    """Convert an iterable to a tuple, or return None."""
    if x is None:
        return None
    return tuple(x)


def _validate_specific_args(instance, attribute, value):  # pylint: disable=unused-argument
    """Validate specific_args structure."""
    for file_path, args in value.items():
        if not isinstance(args, dict):
            raise ValueError(f"specific_args['{file_path}'] must be a dictionary")
        # Note: regex patterns in specific_args will be validated during compilation
        # in __attrs_post_init__, so no need to validate them here


def _validate_export_formatted_files(instance, attribute, value):  # pylint: disable=unused-argument
    """Validate export_formatted_files is either bool or non-empty string."""
    if isinstance(value, str) and len(value.strip()) == 0:
        raise ValueError(
            "export_formatted_files must be a non-empty string when provided as string"
        )


def _validate_comparators(instance, attribute, value):  # pylint: disable=unused-argument
    """Validate comparators are either BaseComparator instances or callable."""
    for ext, comparator in value.items():
        if not (isinstance(comparator, BaseComparator) or callable(comparator)):
            raise ValueError(
                f"Comparator for extension '{ext}' must be a BaseComparator instance "
                "or callable"
            )


@attrs.frozen
class ComparisonConfig:
    """Configuration class to store comparison settings.

    Attributes:
        include_patterns: A list of regular expression patterns. If the relative path of a
            file does not match any of these patterns, it is ignored during the comparison. Note
            that this means that any specific arguments for that file will also be ignored.
        exclude_patterns: A list of regular expression patterns. If the relative path of a
            file matches any of these patterns, it is ignored during the comparison. Note that
            this means that any specific arguments for that file will also be ignored.
        comparators: A ``dict`` to override the registered comparators.
        specific_args: A ``dict`` with the args/kwargs that should be given to the
            comparator for a given file. This ``dict`` should be like the following:

            .. code-block:: Python

                {
                    <relative_file_path>: {
                        comparator: ComparatorInstance,
                        args: [arg1, arg2, ...],
                        kwargs: {
                            kwarg_name_1: kwarg_value_1,
                            kwarg_name_2: kwarg_value_2,
                        }
                    },
                    <another_file_path>: {...},
                    <a name for this category>: {
                        "patterns": ["regex1", "regex2", ...],
                        ... (other arguments)
                    }
                }

            If the "patterns" entry is present, then the name is not considered and is only used as
            a helper for the user. When a "patterns" entry is detected, the other arguments are
            applied to all files whose relative name matches one of the given regular expression
            patterns. If a file could match multiple patterns of different groups, only the first
            one is considered.

            Note that all entries in this ``dict`` are optional.
        return_raw_diffs: If set to ``True``, only the raw differences are returned instead
            of a formatted report.
        export_formatted_files: If set to ``True`` or a not empty string, create a
            new directory with formatted compared data files. If a string is passed, this string is
            used as suffix for the new directory. If `True` is passed, the suffix is
            ``_FORMATTED``.
        max_workers: Maximum number of worker threads/processes for parallel execution. If None,
            defaults to min(32, (os.cpu_count() or 1) + 4) as per executor default.
        executor_type: Type of executor to use for parallel execution. 'thread' uses
            ThreadPoolExecutor (better for I/O-bound tasks), 'process' uses ProcessPoolExecutor
            (better for CPU-bound tasks), 'sequential' disables parallel execution.
    """

    include_patterns: Optional[Iterable[str]] = attrs.field(
        default=None, converter=_convert_iterable_to_tuple
    )
    exclude_patterns: Optional[Iterable[str]] = attrs.field(
        default=None, converter=_convert_iterable_to_tuple
    )
    comparators: Optional[Dict[Optional[str], ComparatorType]] = attrs.field(
        default=None, validator=attrs.validators.optional(_validate_comparators)
    )
    specific_args: Optional[Dict[str, Dict[str, Any]]] = attrs.field(
        default=None, validator=attrs.validators.optional(_validate_specific_args)
    )
    return_raw_diffs: bool = attrs.field(default=False)
    export_formatted_files: Union[bool, str] = attrs.field(
        default=False, validator=_validate_export_formatted_files
    )
    executor_type: Literal["sequential", "thread", "process"] = attrs.field(
        default="sequential"
    )
    max_workers: Optional[int] = attrs.field(default=None)

    # Compiled patterns - computed once, no caching complexity needed
    compiled_include_patterns: Tuple[Pattern[str], ...] = attrs.field(init=False)
    compiled_exclude_patterns: Tuple[Pattern[str], ...] = attrs.field(init=False)
    pattern_specific_args: Dict[Pattern[str], Dict[str, Any]] = attrs.field(
        init=False, repr=False
    )

    def __attrs_post_init__(self):
        """Initialize computed fields after attrs initialization."""
        # Validate and compile patterns - with frozen, we compile once and store directly
        try:
            compiled_include = self._compile_patterns(self.include_patterns)
            object.__setattr__(self, "compiled_include_patterns", compiled_include)
        except ValueError as e:
            raise ValueError(f"Error in include_patterns: {e}") from e

        try:
            compiled_exclude = self._compile_patterns(self.exclude_patterns)
            object.__setattr__(self, "compiled_exclude_patterns", compiled_exclude)
        except ValueError as e:
            raise ValueError(f"Error in exclude_patterns: {e}") from e

        # Setup specific args and pattern specific args
        if self.specific_args is None:
            # Use object.__setattr__ to modify the field even if it's frozen
            object.__setattr__(self, "specific_args", {})

        # Setup pattern specific args
        pattern_specific_args = {}
        if self.specific_args:  # Check if it's not None
            for file_path, v in self.specific_args.items():
                if "patterns" in v:
                    patterns = v.pop("patterns", [])
                    for pattern in patterns:
                        try:
                            compiled_pattern = self._compile_pattern(pattern)
                            pattern_specific_args[compiled_pattern] = v
                        except ValueError as e:
                            raise ValueError(
                                f"Error in specific_args['{file_path}']['patterns']: {e}"
                            ) from e

        object.__setattr__(self, "pattern_specific_args", pattern_specific_args)

        # Setup comparators
        if self.comparators is None:
            object.__setattr__(self, "comparators", get_comparators())

    def _compile_pattern(self, pattern: str) -> Pattern[str]:
        """Compile a regex pattern."""
        try:
            return re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: '{pattern}'") from e

    def _compile_patterns(
        self, patterns: Optional[Iterable[str]]
    ) -> Tuple[Pattern[str], ...]:
        """Compile regex patterns from any iterable to tuple."""
        if patterns is None:
            return ()
        return tuple(self._compile_pattern(pattern) for pattern in patterns)

    # Note: compiled_include_patterns, compiled_exclude_patterns, and pattern_specific_args
    # are now direct attributes set in __attrs_post_init__, no properties needed!

    def should_ignore_file(self, relative_path: str) -> bool:
        """Check if a file should be ignored."""
        # Check inclusion patterns first
        if self.compiled_include_patterns:
            included = any(
                pattern.match(relative_path)
                for pattern in self.compiled_include_patterns
            )
            if not included:
                return True

        # Check exclusion patterns
        return any(
            pattern.match(relative_path) for pattern in self.compiled_exclude_patterns
        )


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
) -> List[Tuple[str, Union[str, bool]]]:  # pragma: no cover
    """Compare a chunk of files.

    Args:
        file_chunk: List of file tuples to compare.
        config: Comparison configuration.
        comp_path: Path to the comparison directory.
        formatted_data_path: Path where formatted files should be exported.

    Returns:
        List of comparison results for the chunk.
    """
    results = []
    for ref_file, relative_path in file_chunk:
        try:
            result = _compare_single_file(
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
