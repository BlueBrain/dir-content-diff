[![Version](https://img.shields.io/pypi/v/dir-content-diff)](https://github.com/BlueBrain/dir-content-diff/releases)
[![Build status](https://github.com/BlueBrain/dir-content-diff/actions/workflows/run-tox.yml/badge.svg?branch=main)](https://github.com/BlueBrain/dir-content-diff/actions)
[![Coverage](https://codecov.io/github/BlueBrain/dir-content-diff/coverage.svg?branch=main)](https://codecov.io/github/BlueBrain/dir-content-diff?branch=main)
[![License](https://img.shields.io/badge/License-Apache%202-blue)](https://github.com/BlueBrain/dir-content-diff/blob/main/LICENSE.txt)
[![Documentation status](https://readthedocs.org/projects/dir-content-diff/badge/?version=latest)](https://dir-content-diff.readthedocs.io/)


# Directory Content Difference

This project provides simple tools to compare the content of a directory against a reference
directory.

This is useful to check the results of a process that generate several files, like a luigi
workflow for example.


## Installation

This package should be installed using pip:

```bash
pip install dir-content-diff
```


## Usage

The ``dir-content-diff`` package introduces a framework to compare two directories. A comparator
is associated to each file extension and then each file in the reference directory is compared to
the file with the same relative path in the compared directory. By default, a few comparators are
provided for usual files but others can be associated to new file extensions or can even replace
the default ones. The comparators should be able to report the differences between two files
accurately, reporting which elements are different among the data. When an extension has no
comparator associated, a default comparator is used which just compares the whole binary data of
the files, so it is not able to report which values are different.

### Compare two directories

If one wants to compare two directories with the following structures:

```bash
└── reference_dir
    ├── sub_dir_1
    |   ├── sub_file_1.a
    |   └── sub_file_2.b
    └── file_1.c
```

```bash
└── compared_dir
    ├── sub_dir_1
    |   ├── sub_file_1.a
    |   └── sub_file_2.b
    |   └── sub_file_3.b
    └── file_1.c
```

These two directories can be compared with the following code:

```python
import dir_content_diff

dir_content_diff.compare_trees("reference_dir", "compared_dir")
```

This code will return an empty dictionary because no difference was detected.

If ``reference_dir/file_1.c`` is the following JSON-like file:

```json
{
    "a": 1,
    "b": [1, 2]
}
```

And ``compared_dir/file_1.c`` is the following JSON-like file:

```json
{
    "a": 2,
    "b": [10, 2, 0]
}
```

The following code registers the ``JsonComparator`` for the file extension ``.c`` and compares the
two directories:

```python
import dir_content_diff

dir_content_diff.register_comparator(".c", dir_content_diff.JsonComparator())
dir_content_diff.compare_trees("reference_dir", "compared_dir")
```

The previous code will output the following dictionary:

```python
{
    'file_1.c': (
        'The files \'reference_dir/file_1.c\' and \'compared_dir/file_1.c\' are different:\n'
        'Added the value(s) \'{"2": 0}\' in the \'[b]\' key.\n'
        'Changed the value of \'[a]\' from 1 to 2.\n'
        'Changed the value of \'[b][0]\' from 1 to 10.'
    )
}
```

It is also possible to check whether the two directories are equal or not with the following code:

```python
import dir_content_diff

dir_content_diff.register_comparator(".c", dir_content_diff.JsonComparator())
dir_content_diff.assert_equal_trees("reference_dir", "compared_dir")
```

Which will output the following ``AssertionError``:

```bash
AssertionError: The files 'reference_dir/file_1.c' and 'compared_dir/file_1.c' are different:
Added the value(s) '{"2": 0}' in the '[b]' key.
Changed the value of '[a]' from 1 to 2.
Changed the value of '[b][0]' from 1 to 10.
```

Finally, the comparators have parameters that can be passed either to be used for all files of a
given extension or only for a specific file:

```python
import dir_content_diff

# Get the default comparators
comparators = dir_content_diff.get_comparators()

# Replace the comparators for JSON files to perform the comparison with a given tolerance
comparators[".json"] = dir_content_diff.JsonComparator(default_diff_kwargs={"tolerance": 0.1})

# Use a specific tolerance for the file ``sub_dir_1/sub_file_1.a``
# In this case, the kwargs are used to compute the difference by default, except the following
# specific kwargs: ``return_raw_diffs``, ``load_kwargs``, ``format_data_kwargs``, ``filter_kwargs``,
# ``format_diff_kwargs``, ``sort_kwargs``, ``concat_kwargs`` and ``report_kwargs``.
specific_args = {"sub_dir_1/sub_file_1.a": {"tolerance": 0.5}}

dir_content_diff.assert_equal_trees(
    "reference_dir",
    "compared_dir",
    comparators=comparators,
    specific_args=specific_args,
)
```

Each comparator has different arguments that are detailed in the documentation.

It's also possible to specify a arbitrary comparator for a specific file:

```python
specific_args = {
    "sub_dir_1/sub_file_1.a": {
        "comparator": dir_content_diff.JsonComparator(),
        "tolerance": 0.5,
    }
}
```

And last but not least, it's possible to use regular expressions to associate specific arguments to
a set of files:

```python
specific_args = {
    "all files with *.a of *.b extensions": {
        "patterns": [r".*\.[a,b]$"],
        "comparator": dir_content_diff.BaseComparator(),
    }
}
```


### Export formatted data

Some comparators have to format the data before comparing them. For example, if one wants to
compare data with file paths inside, it's likely that only a relative part of these paths are
relevant, not the entire absolute paths. To do this, a specific comparator can be defined with a
custom ``format_data()`` method which is automatically called after the data are loaded but before
the data are compared. It is then possible to export the data just after they have been formatted
for check purpose for example. To do this, the ``export_formatted_files`` argument of the
``dir_content_diff.compare_trees`` and ``dir_content_diff.assert_equal_trees`` functions can be set
to ``True``. Thus all the files processed by a comparator with a ``save()`` method will be exported
to a new directory. This new directory is the same as the compared directory to which a suffix is
added. By default, the suffix is `` _FORMATTED ``, but it can be overridden by passing a non-empty
string to the ``export_formatted_files`` argument.

## Pytest plugin

This package can be used as a pytest plugin. When ``pytest`` is run and ``dir-content-diff`` is
installed, it is automatically detected and registered as a plugin. It is then possible to trigger
the export of formatted data with the following ``pytest`` option: ``--dcd-export-formatted-data``.
It is also possible to define a custom suffix for the new directory with the following option:
``--dcd-export-suffix``.


## Funding & Acknowledgment

The development of this software was supported by funding to the Blue Brain Project, a research
center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government’s ETH
Board of the Swiss Federal Institutes of Technology.

For license and authors, see `LICENSE.txt` and `AUTHORS.md` respectively.

Copyright © 2021-2023 Blue Brain Project/EPFL
