"""Module containing the base comparators."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2026 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

import configparser
import filecmp
import json
import math
import re
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from xml.etree import ElementTree

import diff_pdf_visually
import jsonpath_ng
import yaml
from deepdiff import DeepDiff
from deepdiff.operator import BaseOperator
from dicttoxml import dicttoxml
from diff_pdf_visually import pdfdiff_pages

from dir_content_diff.util import diff_msg_formatter


class _NumericToleranceOperator(BaseOperator):
    """Numeric comparison operator implementing the existing tolerance kwargs."""

    def __init__(self, tolerance, absolute_tolerance):
        super().__init__()
        self.tolerance = tolerance
        self.absolute_tolerance = absolute_tolerance

    def match(self, level):
        """Return whether both compared values are numeric."""
        return (
            isinstance(level.t1, (int, float))
            and isinstance(level.t2, (int, float))
            and not isinstance(level.t1, bool)
            and not isinstance(level.t2, bool)
        )

    def give_up_diffing(self, level, diff_instance):
        """Return whether two numeric values should be treated as equal."""
        first_is_nan = bool(level.t1 != level.t1)
        second_is_nan = bool(level.t2 != level.t2)
        if first_is_nan or second_is_nan:
            return first_is_nan and second_is_nan
        return math.isclose(
            level.t1,
            level.t2,
            rel_tol=self.tolerance or 0,
            abs_tol=self.absolute_tolerance or 0,
        )

    def normalize_value_for_hashing(self, parent, obj):  # pylint: disable=unused-argument
        """Return unmodified values when set items are hashed."""
        return obj


class BaseComparator(ABC):
    """Base Comparator class."""

    def __init__(
        self,
        default_load_kwargs=None,
        default_format_data_kwargs=None,
        default_diff_kwargs=None,
        default_filter_kwargs=None,
        default_format_diff_kwargs=None,
        default_sort_kwargs=None,
        default_concat_kwargs=None,
        default_report_kwargs=None,
        default_save_kwargs=None,
    ):
        self._default_load_kwargs = default_load_kwargs or {}
        self._default_format_data_kwargs = default_format_data_kwargs or {}
        self._default_diff_kwargs = default_diff_kwargs or {}
        self._default_filter_kwargs = default_filter_kwargs or {}
        self._default_format_diff_kwargs = default_format_diff_kwargs or {}
        self._default_sort_kwargs = default_sort_kwargs or {}
        self._default_concat_kwargs = default_concat_kwargs or {}
        self._default_report_kwargs = default_report_kwargs or {}
        self._default_save_kwargs = default_save_kwargs or {}

        self.current_state = {}

    def load(self, path, **kwargs):
        """Load a file."""
        return path

    def format_data(self, data, ref=None, **kwargs):
        """Format the loaded data."""
        # pylint: disable=unused-argument
        return data

    def save(self, data, path, **kwargs):
        """Save formatted data into a file."""
        raise NotImplementedError  # pragma: no cover

    @property
    def save_capability(self):
        """Check that the current class has a ``save()`` capability."""
        return self.__class__.save != BaseComparator.save

    @abstractmethod
    def diff(self, ref, comp, *args, **kwargs):
        """Perform the comparison between the reference data and the compared data.

        .. note::
            This function must return either of the following:

            * an iterable of differences between each data element (the iterable can be empty).
            * a mapping of differences between each data element in which the keys can be an
              element ID or a column name (the mapping can be empty).
            * a boolean indicating whether the files are different (`True`) or not (`False`).
        """

    def filter(self, differences, **kwargs):
        """Define a filter to remove specific elements from the result differences."""
        return differences

    def format_diff(self, difference, **kwargs):
        """Format one element difference."""
        return difference

    def sort(self, differences, **kwargs):
        """Sort the element differences."""
        return sorted(differences)

    def concatenate(self, differences, **kwargs):
        """Concatenate the differences."""
        return "\n".join(differences)

    def report(
        self,
        ref_file,
        comp_file,
        formatted_differences,
        diff_args,
        diff_kwargs,
        load_kwargs=None,
        format_data_kwargs=None,
        filter_kwargs=None,
        format_diff_kwargs=None,
        sort_kwargs=None,
        concat_kwargs=None,
        **kwargs,
    ):  # pylint: disable=too-many-arguments
        """Create a report from the formatted differences.

        .. note::
            This function must return a formatted report of the differences (usually as a string
            but it can be any type). If the passed differences are ``None``, ``False`` or an empty
            collection, the report should return ``False`` to state that the files are not
            different.
        """
        return diff_msg_formatter(
            ref_file,
            comp_file,
            formatted_differences,
            diff_args,
            diff_kwargs,
            load_kwargs=load_kwargs,
            format_data_kwargs=format_data_kwargs,
            filter_kwargs=filter_kwargs,
            format_diff_kwargs=format_diff_kwargs,
            sort_kwargs=sort_kwargs,
            concat_kwargs=concat_kwargs,
            report_kwargs=kwargs,
        )

    def __call__(
        self,
        ref_file,
        comp_file,
        *diff_args,
        return_raw_diffs=False,
        load_kwargs=None,
        format_data_kwargs=None,
        filter_kwargs=None,
        format_diff_kwargs=None,
        sort_kwargs=None,
        concat_kwargs=None,
        report_kwargs=None,
        **diff_kwargs,
    ):
        """Perform the comparison between the reference file and the compared file.

        .. note::
            The workflow is the following:

            * call :meth:`dir_content_diff.base_comparators.BaseComparator.load()` to load the
              reference file.
            * call :meth:`dir_content_diff.base_comparators.BaseComparator.load()` to load the
              compared file.
            * call :meth:`dir_content_diff.base_comparators.BaseComparator.format_data()` to format
              the data from the compared file.
            * call :meth:`dir_content_diff.base_comparators.BaseComparator.diff()` to compute the
              differences.
            * if ``return_raw_diffs``, the diffs are returned at this step.
            * if the diffs are not just a boolean, the collection is:
                * filtered by calling
                  :meth:`dir_content_diff.base_comparators.BaseComparator.filter()`.
                * formatted by calling
                  :meth:`dir_content_diff.base_comparators.BaseComparator.format_diff()` on each
                  element.
                * sorted by calling
                  :meth:`dir_content_diff.base_comparators.BaseComparator.sort()`.
                * concatenated into one string by calling
                  :meth:`dir_content_diff.base_comparators.BaseComparator.concatenate()`.
            * a report is generated by calling
              :meth:`dir_content_diff.base_comparators.BaseComparator.report()`.
        """
        # pylint: disable=too-many-arguments
        if load_kwargs is None:
            load_kwargs = self._default_load_kwargs
        if format_data_kwargs is None:
            format_data_kwargs = self._default_format_data_kwargs
        if not diff_kwargs:
            diff_kwargs = self._default_diff_kwargs
        if filter_kwargs is None:
            filter_kwargs = self._default_filter_kwargs
        if format_diff_kwargs is None:
            format_diff_kwargs = self._default_format_diff_kwargs
        if sort_kwargs is None:
            sort_kwargs = self._default_sort_kwargs
        if concat_kwargs is None:
            concat_kwargs = self._default_concat_kwargs
        if report_kwargs is None:
            report_kwargs = self._default_report_kwargs

        # Reset current state
        self.current_state = {}

        # Load data
        ref = self.load(ref_file, **load_kwargs)
        comp = self.load(comp_file, **load_kwargs)

        # Format compared data
        formatted_comp = self.format_data(comp, ref=ref, **format_data_kwargs)

        # Compute the difference
        diffs = self.diff(ref, formatted_comp, *diff_args, **diff_kwargs)

        # Return raw differences if required
        if return_raw_diffs:
            return diffs

        # Format the difference elements
        if not diffs:
            formatted_diffs = False
        elif diffs is True:
            formatted_diffs = diffs
        else:
            filtered_diffs = self.filter(diffs, **filter_kwargs)
            if hasattr(filtered_diffs, "items"):
                sorted_diffs = self.sort(
                    [
                        self.format_diff(i, **format_diff_kwargs)
                        for i in filtered_diffs.items()
                    ],
                    **sort_kwargs,
                )
                formatted_diffs = self.concatenate(
                    sorted_diffs,
                    **concat_kwargs,
                )
            else:
                sorted_diffs = self.sort(
                    [self.format_diff(i, **format_diff_kwargs) for i in filtered_diffs],
                    **sort_kwargs,
                )
                formatted_diffs = self.concatenate(
                    sorted_diffs,
                    **concat_kwargs,
                )

        # Build the report
        return self.report(
            ref_file,
            comp_file,
            formatted_diffs,
            diff_args,
            diff_kwargs,
            load_kwargs=load_kwargs,
            format_data_kwargs=format_data_kwargs,
            filter_kwargs=filter_kwargs,
            format_diff_kwargs=format_diff_kwargs,
            sort_kwargs=sort_kwargs,
            concat_kwargs=concat_kwargs,
            **report_kwargs,
        )

    def __eq__(self, other):
        """Compare 2 :class:`dir_content_diff.base_comparators.BaseComparator` instances."""
        if (
            type(self) is not type(other)
            or self.__dict__.keys() != other.__dict__.keys()
        ):
            return False

        for k, v in self.__dict__.items():
            if other.__dict__[k] != v:
                return False

        return True


class DefaultComparator(BaseComparator):
    """The comparator used by default when none is registered for a given extension.

    This comparator only performs a binary comparison of the files.
    """

    def diff(self, ref, comp, *args, **kwargs):
        """Compare binary data.

        This function calls :func:`filecmp.cmp`, read the doc of this function for details on
        args and kwargs.
        """
        return not filecmp.cmp(ref, comp)


class DictComparator(BaseComparator):
    """Comparator for dictionaries."""

    _MISSING_VALUE = object()
    _DIFF_ACTION_CATEGORIES = {
        "dictionary_item_added": "add",
        "iterable_item_added": "add",
        "dictionary_item_removed": "remove",
        "iterable_item_removed": "remove",
        "type_changes": "change",
        "values_changed": "change",
    }

    _ACTION_MAPPING = {
        "add": "Added value at {key}: {value}.",
        "change": "Changed value at {key}: {value[0]} -> {value[1]}.",
        "remove": "Removed value at {key}: {value}.",
        "missing_ref_entry": (
            "The path '{key}' is missing in the reference dictionary, please fix the "
            "'replace_pattern' argument."
        ),
        "missing_comp_entry": (
            "The path '{key}' is missing in the compared dictionary, please fix the "
            "'replace_pattern' argument."
        ),
    }

    @staticmethod
    def _format_report_value(value):
        try:
            return json.dumps(value, default=str, sort_keys=True)
        except TypeError:
            return json.dumps(value, default=str)

    @staticmethod
    def _format_report_path(path):
        """Format a path for human-readable reports."""
        if isinstance(path, str) and path.startswith("root["):
            path = path[4:]
        return path

    @classmethod
    def _format_action(cls, action, path, value):
        """Format a normalized diff action."""
        formatted_path = cls._format_report_path(path)
        if action == "change":
            old_value, new_value = value
            if old_value is cls._MISSING_VALUE:
                return f"{formatted_path}: {cls._format_report_value(new_value)}"
            return (
                f"Changed value at {formatted_path}: "
                f"{cls._format_report_value(old_value)} -> "
                f"{cls._format_report_value(new_value)}."
            )
        if action == "add":
            return (
                f"Added value at {formatted_path}: {cls._format_report_value(value)}."
            )
        if action == "remove":
            return (
                f"Removed value at {formatted_path}: {cls._format_report_value(value)}."
            )
        raise ValueError(
            f"Unexpected dictionary diff action: {action!r}"
        )  # pragma: no cover

    @classmethod
    def _value_change_values(cls, values):
        """Return explicit old/new values from a DeepDiff value-change item."""
        if hasattr(values, "items") and "old_value" in values and "new_value" in values:
            return values["old_value"], values["new_value"]
        return cls._MISSING_VALUE, values

    @classmethod
    def _iter_deepdiff_actions(cls, category, value):
        """Yield normalized action tuples for known DeepDiff report categories."""
        action = cls._DIFF_ACTION_CATEGORIES.get(category)
        if action is None or not hasattr(value, "items"):
            return  # pragma: no cover

        for path, diff_value in value.items():
            if action == "change":
                diff_value = cls._value_change_values(diff_value)
            yield action, path, diff_value

    @classmethod
    def _format_deepdiff_category(cls, category, value):
        """Format a known grouped DeepDiff category."""
        return "\n".join(
            cls._format_action(action, path, diff_value)
            for action, path, diff_value in cls._iter_deepdiff_actions(category, value)
        )

    def filter(self, differences, **kwargs):
        """Expand grouped categories into formatted diff elements."""
        filtered_differences = super().filter(differences, **kwargs)
        expanded_differences = []
        for category, value in filtered_differences.items():
            if category == "format_errors":
                expanded_differences.extend(
                    (category, action, key, error_value)
                    for action, key, error_value in value
                )
            elif category in self._DIFF_ACTION_CATEGORIES and hasattr(value, "items"):
                expanded_differences.extend(
                    self._iter_deepdiff_actions(category, value)
                )
            else:
                expanded_differences.append((category, value))
        return expanded_differences

    def format_data(self, data, ref=None, replace_pattern=None, **kwargs):
        """Format the loaded data."""
        # pylint: disable=too-many-nested-blocks
        self.current_state["format_errors"] = errors = []

        if replace_pattern is not None:
            for pat, paths in replace_pattern.items():
                pattern = pat[0]
                new_value = pat[1]
                count = pat[2] if len(pat) > 2 else 0
                flags = pat[3] if len(pat) > 3 else 0
                for raw_path in paths:
                    path = jsonpath_ng.parse(raw_path)
                    if ref is not None and len(path.find(ref)) == 0:
                        errors.append(
                            (
                                "missing_ref_entry",
                                raw_path,
                                None,
                            )
                        )
                    elif len(path.find(data)) == 0:
                        errors.append(
                            (
                                "missing_comp_entry",
                                raw_path,
                                None,
                            )
                        )
                    else:
                        for i in path.find(data):
                            if isinstance(i.value, str):
                                i.full_path.update(
                                    data,
                                    re.sub(pattern, new_value, i.value, count, flags),
                                )
        return data

    def diff(
        self,
        ref,
        comp,
        *args,
        tolerance=None,
        absolute_tolerance=None,
        custom_operators=None,
        **kwargs,
    ):
        """Compare 2 dictionaries.

        This function compares dictionaries and returns a machine-readable diff report.

        Keyword Args:
            tolerance (float): Relative threshold to consider when comparing two float numbers.
            absolute_tolerance (float): Absolute threshold to consider when comparing
                two float numbers.
            custom_operators (list): Additional custom operators passed to DeepDiff.
            **kwargs: Additional keyword arguments are passed to :class:`deepdiff.diff.DeepDiff`.
        """
        if args:
            raise TypeError(
                "DictComparator.diff does not accept positional comparison "
                "arguments. Use keyword arguments instead, for example "
                "'tolerance', 'absolute_tolerance', 'exclude_paths', "
                "'exclude_regex_paths', 'include_paths', or 'ignore_order'."
            )
        errors = self.current_state.get("format_errors", [])
        custom_operators = list(custom_operators or [])
        custom_operators.insert(
            0, _NumericToleranceOperator(tolerance, absolute_tolerance)
        )

        kwargs.setdefault("verbose_level", 2)
        kwargs.setdefault(
            "threshold_to_diff_deeper", 0
        )  # Expand all differences, even if they are small
        kwargs.setdefault("zip_ordered_iterables", True)
        kwargs.setdefault("ignore_nan_inequality", True)
        kwargs.setdefault("ignore_private_variables", False)

        report = DeepDiff(
            ref,
            comp,
            custom_operators=custom_operators,
            **kwargs,
        ).to_dict()
        if errors:
            report["format_errors"] = errors
        return report

    def format_diff(self, difference):
        """Format one element difference."""
        if len(difference) == 4 and difference[0] == "format_errors":
            _, action, key, error_value = difference
            return self._ACTION_MAPPING[action].format(key=key, value=error_value)

        if len(difference) == 3 and difference[0] in {"add", "change", "remove"}:
            action, path, value = difference
            return self._format_action(action, path, value)

        category, value = difference
        if category == "format_errors":
            return "\n".join(
                self._ACTION_MAPPING[action].format(key=key, value=error_value)
                for action, key, error_value in value
            )
        if category in self._DIFF_ACTION_CATEGORIES and hasattr(value, "items"):
            return self._format_deepdiff_category(category, value)
        return f"{category}: {self._format_report_value(value)}"


class JsonComparator(DictComparator):
    """Comparator for JSON files.

    This comparator is based on the :class:`DictComparator` and uses the same parameters.
    """

    def load(self, path, **kwargs):
        """Open a JSON file."""
        with open(path) as file:  # pylint: disable=unspecified-encoding
            data = json.load(file, **kwargs)
        return data

    def save(self, data, path, **kwargs):
        """Save formatted data into a JSON file."""
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, **kwargs)


class YamlComparator(DictComparator):
    """Comparator for YAML files.

    This comparator is based on the :class:`DictComparator` and uses the same parameters.
    """

    def load(self, path, **kwargs):
        """Open a YAML file."""
        with open(path) as file:  # pylint: disable=unspecified-encoding
            data = yaml.full_load(file, **kwargs)
        return data

    def save(self, data, path, **kwargs):
        """Save formatted data into a YAML file."""
        with open(path, "w", encoding="utf-8") as file:
            yaml.dump(data, file, **kwargs)


class XmlComparator(DictComparator):
    """Comparator for XML files.

    This comparator is based on the :class:`DictComparator` and uses the same parameters.

    .. warning:: The XML files must have only one root.

    .. note::

        If the type attributes are given in the XML file, the values will be automatically casted
        to Python types. For the lists, each item must be in an separated entry.
        Here is an example of such XML data:

        .. code-block:: xml

            <?xml version="1.0" encoding="UTF-8" ?>
            <root>
                <int_value type="int">1</int_value>
                <simple_list type="list">
                    <item type="int">1</item>
                    <item type="float">2.5</item>
                    <item type="str">str_val</item>
                </simple_list>
            </root>
    """

    def load(self, path):  # pylint: disable=arguments-differ
        """Open a XML file."""
        with open(path, encoding="utf-8") as file:
            data = self.xmltodict(file.read())
        return data

    def save(self, data, path, root=False, **kwargs):
        """Save formatted data into a XML file."""
        with open(path, "w", encoding="utf-8") as file:
            file.write(dicttoxml(data, root=root, **kwargs).decode())

    @staticmethod
    def _cast_from_attribute(text, attr):
        """Convert XML text into a Python data format based on the tag attribute."""
        if "type" not in attr:
            return text
        value_type = attr.get("type", "").lower()
        if value_type == "str":
            res = str(text)
        elif value_type == "int":
            res = int(text)
        elif value_type == "float":
            res = float(text)
        elif value_type == "bool":
            if str(text).lower() == "true":
                res = True
            elif str(text).lower() == "false":
                res = False
            else:
                raise ValueError("Boolean attributes expect 'true' or 'false'.")
        elif value_type == "list":
            res = []
        elif value_type == "dict":
            res = {}
        elif value_type == "null":
            res = None
        else:
            raise TypeError(
                "Unsupported type. "
                "Only 'str', 'int', 'float', 'bool', 'list', 'dict', and 'null' are supported."
            )
        return res

    @staticmethod
    def add_to_output(obj, child):
        """Add entry from :class:`xml.etree.ElementTree.Element` object into the given object."""
        if isinstance(obj, dict):
            obj.update(
                {
                    child.tag: XmlComparator._cast_from_attribute(
                        child.text, child.attrib
                    )
                }
            )
            for sub in child:
                XmlComparator.add_to_output(obj[child.tag], sub)
        elif isinstance(obj, list):
            obj.append(XmlComparator._cast_from_attribute(child.text, child.attrib))
            for sub in child:
                XmlComparator.add_to_output(obj[-1], sub)

    @staticmethod
    def xmltodict(obj):
        """Convert an XML string into a Python object based on each tag's attribute."""
        root = ElementTree.fromstring(obj)
        output = {}

        for child in root:
            XmlComparator.add_to_output(output, child)
        return {root.tag: output}


class IniComparator(DictComparator):
    """Comparator for INI files.

    This comparator is based on the :class:`DictComparator` and uses the same parameters.

    .. note::

        The ``load_kwargs`` are passed to the ``configparser.ConfigParser``.
    """

    def load(self, path, **kwargs):  # pylint: disable=arguments-differ
        """Open a INI file."""
        data = configparser.ConfigParser(**kwargs)
        data.read(path)
        return self.configparser_to_dict(data)

    def save(self, data, path, **kwargs):
        """Save formatted data into a INI file."""
        with open(path, "w", encoding="utf-8") as file:
            self.dict_to_configparser(data, **kwargs).write(file)

    @staticmethod
    def configparser_to_dict(config):
        """Transform a ConfigParser object into a dict."""
        dict_config = {}
        for section in config.sections():
            dict_config[section] = {}
            for option in config.options(section):
                val = config.get(section, option)
                try:
                    # Try to load JSON strings if possible
                    val = json.loads(val)
                except json.JSONDecodeError:
                    pass
                dict_config[section][option] = val
        return dict_config

    @staticmethod
    def dict_to_configparser(data, **kwargs):
        """Transform a dict object into a ConfigParser."""
        config = configparser.ConfigParser(**kwargs)
        for k, v in data.items():
            config.add_section(k)
            for opt, val in v.items():
                config[k][opt] = json.dumps(val)
        return config


class PdfComparator(BaseComparator):
    """Comparator for PDF files."""

    def diff(self, ref, comp, *args, **kwargs):
        """Compare data from two PDF files.

        This function calls the `diff_pdf_visually.pdf_similar() <https://github.com/bgeron/diff-
        pdf-visually/blob/b5298cfaa6d74a3bf1c043817d1239678519ed71/diff_pdf_visually/diff.py#L85>`_
        function, read the doc of this function for details on args and kwargs.
        It compares the visual aspects of the PDF files, ignoring the invisible content (e.g. file
        header or invisible things like white font on white background). The PDF files are converted
        into images using ``ImageMagick`` and then these images are compared.

        Keyword Args:
            threshold (int): The threshold used to compare the images.
            tempdir (pathlib.Path): Directory in which a new ``dir-diff`` directory will be created
                to export the debug images.
            dpi (int): The resolution used to convert the PDF files into images.
            verbosity (int): The log verbosity.
            max_report_pagenos (int): Only this number of the different pages will be logged (only
                used if the verbosity is greater than 1).
            num_threads (int): If set to 2 (the default), the image conversion are processed in
                parallel. If set to 1 it is processed sequentially.
        """
        res = pdfdiff_pages(ref, comp, *args, **kwargs)
        if not res:
            return False
        return res

    def __call__(self, ref_file, comp_file, *args, **kwargs):
        """Process arguments before calling the diff method."""
        tempdir = kwargs.pop("tempdir", None)
        if tempdir is not None:
            relative_parts = []
            for i, j in zip(
                ref_file.parts[::-1], comp_file.parts[::-1]
            ):  # pragma: no branch
                if i != j:
                    break
                relative_parts.append(i)
            if relative_parts and relative_parts[-1] == Path(tempdir).root:
                relative_parts.pop()
            if not relative_parts:
                relative_parts.append(comp_file.name)
            relative_parts.append("diff-pdf")
            new_tempdir = Path(tempdir) / Path(*relative_parts[::-1])

            # Deduplicate name if needed
            last_part = str(relative_parts[-1])
            num = 1
            while True:
                root = Path(tempdir) / relative_parts[-1]
                if not root.exists():
                    new_tempdir.mkdir(parents=True, exist_ok=False)
                    break
                relative_parts[-1] = last_part + f"_{num}"
                new_tempdir = Path(tempdir) / Path(*relative_parts[::-1])
                num += 1

            kwargs["tempdir"] = new_tempdir

        # Update default verbosity
        current_default_verbosity = diff_pdf_visually.constants.DEFAULT_VERBOSITY
        try:
            if "verbosity" not in kwargs:  # pragma: no branch
                if (
                    diff_pdf_visually.diff.pdfdiff_pages.__defaults__[1] is None
                ):  # pragma: no cover
                    diff_pdf_visually.constants.DEFAULT_VERBOSITY = 0
                else:
                    kwargs["verbosity"] = 0  # pragma: no cover
            return super().__call__(ref_file, comp_file, *args, **kwargs)
        finally:
            diff_pdf_visually.constants.DEFAULT_VERBOSITY = current_default_verbosity

    def report(
        self,
        ref_file,
        comp_file,
        formatted_differences,
        diff_args,
        diff_kwargs,
        load_kwargs=None,
        format_data_kwargs=None,
        filter_kwargs=None,
        format_diff_kwargs=None,
        sort_kwargs=None,
        concat_kwargs=None,
        **kwargs,
    ):  # pylint: disable=too-many-arguments
        """Add specific information before calling the default method."""
        if formatted_differences and isinstance(formatted_differences, str):
            formatted_differences = (
                "The following pages are the most different: "
                + formatted_differences.replace("\n", ", ")
            )
            if "tempdir" in diff_kwargs:
                formatted_differences += (
                    "\nThe visual differences can be found here: "
                    + str(diff_kwargs["tempdir"])
                )
        return super().report(
            ref_file,
            comp_file,
            formatted_differences,
            diff_args,
            diff_kwargs,
            load_kwargs=load_kwargs,
            format_data_kwargs=format_data_kwargs,
            filter_kwargs=filter_kwargs,
            format_diff_kwargs=format_diff_kwargs,
            sort_kwargs=sort_kwargs,
            concat_kwargs=concat_kwargs,
            **kwargs,
        )

    def format_diff(self, difference, **kwargs):
        """Format one element difference."""
        return str(difference)
