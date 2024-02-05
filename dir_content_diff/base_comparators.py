"""Module containing the base comparators."""
import configparser
import filecmp
import json
import re
from abc import ABC
from abc import abstractmethod
from xml.etree import ElementTree

import dictdiffer
import jsonpath_ng
import yaml
from dicttoxml import dicttoxml
from diff_pdf_visually import pdf_similar

from dir_content_diff.util import diff_msg_formatter

_ACTION_MAPPING = {
    "add": "Added the value(s) '{value}' in the '{key}' key.",
    "change": "Changed the value of '{key}' from {value[0]} to {value[1]}.",
    "remove": "Removed the value(s) '{value}' from '{key}' key.",
}


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
                formatted_diffs = self.concatenate(
                    self.sort(
                        [self.format_diff(i, **format_diff_kwargs) for i in filtered_diffs.items()],
                        **sort_kwargs,
                    ),
                    **concat_kwargs,
                )
            else:
                formatted_diffs = self.concatenate(
                    self.sort(
                        [self.format_diff(i, **format_diff_kwargs) for i in filtered_diffs],
                        **sort_kwargs,
                    ),
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
        if type(self) is not type(other) or self.__dict__.keys() != other.__dict__.keys():
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

    _ACTION_MAPPING = {
        "add": "Added the value(s) '{value}' in the '{key}' key.",
        "change": "Changed the value of '{key}' from {value[0]} to {value[1]}.",
        "remove": "Removed the value(s) '{value}' from '{key}' key.",
        "missing_ref_entry": (
            "The path '{key}' is missing in the reference dictionary, please fix the "
            "'replace_pattern' argument."
        ),
        "missing_comp_entry": (
            "The path '{key}' is missing in the compared dictionary, please fix the "
            "'replace_pattern' argument."
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._format_mapping = {
            "add": self._format_add_value,
            "remove": self._format_remove_value,
            "change": self._format_change_value,
        }

    @staticmethod
    def _format_key(key):
        if isinstance(key, str):
            key = key.split(".")
        if key == [""]:
            key = []
        return "".join(f"[{k}]" for k in key)

    @staticmethod
    def _format_add_value(value):
        return json.dumps(dict(sorted(value)))

    @staticmethod
    def _format_remove_value(value):
        return json.dumps(dict(sorted(value)))

    @staticmethod
    def _format_change_value(value):
        value = list(value)
        for num, i in enumerate(value):
            if isinstance(i, str):
                value[num] = f"'{i}'"
            else:
                value[num] = str(i)
        return value

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
                                    data, re.sub(pattern, new_value, i.value, count, flags)
                                )
        return data

    def diff(self, ref, comp, *args, **kwargs):
        """Compare 2 dictionaries.

        This function calls :func:`dictdiffer.diff` to compare the dictionaries, read the doc of
        this function for details on args and kwargs.

        Keyword Args:
            tolerance (float): Relative threshold to consider when comparing two float numbers.
            absolute_tolerance (float): Absolute threshold to consider when comparing
                two float numbers.
            ignore (set[list]): Set of keys that should not be checked.
            path_limit (list[str]): List of path limit tuples or :class:`dictdiffer.utils.PathLimit`
                object to limit the diff recursion depth.
        """
        errors = self.current_state.get("format_errors", [])

        if len(args) > 5:
            dot_notation = args[5]
            args = args[:5] + args[6:]
        else:
            dot_notation = kwargs.pop("dot_notation", False)
        kwargs["dot_notation"] = dot_notation
        errors.extend(list(dictdiffer.diff(ref, comp, *args, **kwargs)))
        return errors

    def format_diff(self, difference):
        """Format one element difference."""
        action, key, value = difference
        return self._ACTION_MAPPING[action].format(
            key=self._format_key(key),
            value=self._format_mapping[action](value),
        )


class JsonComparator(DictComparator):
    """Comparator for JSON files.

    This comparator is based on the :class:`DictComparator` and uses the same parameters.
    """

    def load(self, path):
        """Open a JSON file."""
        with open(path) as file:  # pylint: disable=unspecified-encoding
            data = json.load(file)
        return data

    def save(self, data, path):
        """Save formatted data into a JSON file."""
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file)


class YamlComparator(DictComparator):
    """Comparator for YAML files.

    This comparator is based on the :class:`DictComparator` and uses the same parameters.
    """

    def load(self, path):
        """Open a YAML file."""
        with open(path) as file:  # pylint: disable=unspecified-encoding
            data = yaml.full_load(file)
        return data

    def save(self, data, path):
        """Save formatted data into a YAML file."""
        with open(path, "w", encoding="utf-8") as file:
            yaml.dump(data, file)


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

    def save(self, data, path):
        """Save formatted data into a XML file."""
        with open(path, "w", encoding="utf-8") as file:
            file.write(dicttoxml(data["root"]).decode())

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
                raise ValueError("Bool attributes expect 'true' or 'false'.")
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
            obj.update({child.tag: XmlComparator._cast_from_attribute(child.text, child.attrib)})
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

    def save(self, data, path):
        """Save formatted data into a INI file."""
        with open(path, "w", encoding="utf-8") as file:
            self.dict_to_configparser(data).write(file)

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
            tempdir (pathlib.Path): Empty directory where the temporary images will be exported.
            dpi (int): The resolution used to convert the PDF files into images.
            verbosity (int): The log verbosity.
            max_report_pagenos (int): Only this number of the different pages will be logged (only
                used if the verbosity is greater than 1).
            num_threads (int): If set to 2 (the default), the image conversion are processed in
                parallel. If set to 1 it is processed sequentially.
        """
        return not pdf_similar(ref, comp, *args, **kwargs)
