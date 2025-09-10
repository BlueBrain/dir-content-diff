"""Configuration file for the Sphinx documentation builder."""

# LICENSE HEADER MANAGED BY add-license-header
# Copyright (c) 2023-2025 Blue Brain Project, EPFL.
#
# This file is part of dir-content-diff.
# See https://github.com/BlueBrain/dir-content-diff for further info.
#
# SPDX-License-Identifier: Apache-2.0
# LICENSE HEADER MANAGED BY add-license-header

# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

from importlib import metadata
from pathlib import Path

# -- Project information -----------------------------------------------------

project_name = "Directory Content Difference"
package_name = "dir-content-diff"

# The short X.Y version
version = metadata.version(package_name)

# The full version, including alpha/beta/rc tags
release = version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
]

todo_include_todos = True

# Add any paths that contain templates here, relative to this directory.
# templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx-bluebrain-theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

html_theme_options = {
    "metadata_distribution": package_name,
}

html_title = project_name

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# autosummary settings
autosummary_generate = True

# autodoc settings
autodoc_typehints = "both"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "special-members": "__call__",
}

intersphinx_mapping = {
    "dictdiffer": ("https://dictdiffer.readthedocs.io/en/latest/", None),
    "morph_tool": ("https://morph-tool.readthedocs.io/en/latest/", None),
    "morphio": ("https://morphio.readthedocs.io/en/latest/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "python": ("https://docs.python.org/3", None),
    "voxcell": ("https://voxcell.readthedocs.io/en/latest/", None),
}

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
]
myst_heading_anchors = 5
myst_all_links_external = True
suppress_warnings = ["myst.header"]


def convert_github_admonitions(text):
    """Convert GitHub-style admonitions to MyST format."""
    lines = text.split("\n")
    github_to_myst = {
        "> [!NOTE]": ":::{note}",
        "> [!TIP]": ":::{tip}",
        "> [!IMPORTANT]": ":::{important}",
        "> [!WARNING]": ":::{warning}",
        "> [!CAUTION]": ":::{caution}",
    }

    converted_lines = []
    in_admonition = False

    for line in lines:
        # Check if this line starts a GitHub admonition
        admonition_found = False
        for github_style, myst_style in github_to_myst.items():
            if line.strip().startswith(github_style):
                # Start of admonition
                converted_lines.append(myst_style)
                in_admonition = True
                admonition_found = True
                break

        if not admonition_found:
            if in_admonition:
                strip_line = line.strip()
                if strip_line.startswith("> "):
                    # Content of admonition - remove the "> " prefix
                    content = strip_line[2:]
                    converted_lines.append(content)
                elif strip_line == ">":
                    # Empty line in admonition
                    converted_lines.append("")
                elif strip_line == "":
                    # Empty line - could be end of admonition or just spacing
                    converted_lines.append("")
                else:
                    # End of admonition
                    converted_lines.append(":::")
                    converted_lines.append("")
                    converted_lines.append(line)
                    in_admonition = False
            else:
                # Regular line
                converted_lines.append(line)

    # Close any remaining open admonition
    if in_admonition:
        converted_lines.append(":::")

    return "\n".join(converted_lines)


def preprocess_readme_for_sphinx(app, config):  # pylint: disable=unused-argument
    """Preprocess README.md to convert GitHub admonitions before Sphinx build."""
    # Calculate paths relative to the docs directory
    docs_dir = Path(app.srcdir)
    project_root = docs_dir.parent.parent
    readme_path = project_root / "README.md"
    docs_readme_path = docs_dir / "README_processed.md"

    # Remove existing processed README to ensure fresh generation
    if docs_readme_path.exists():
        docs_readme_path.unlink()
        print(f"[sphinx-hook] Removed existing {docs_readme_path}")

    # Check if README exists
    if not readme_path.exists():
        print(f"[sphinx-hook] README.md not found at {readme_path}")
        return

    # Read original README
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Convert admonitions
        converted_content = convert_github_admonitions(content)

        # Write processed README to docs directory
        with open(docs_readme_path, "w", encoding="utf-8") as f:
            f.write(converted_content)

        print(f"[sphinx-hook] Processed README saved to {docs_readme_path}")

    except Exception as e:
        print(f"[sphinx-hook] Error processing README: {e}")
        raise


def setup(app):
    """Setup Sphinx app with custom handlers."""
    # Connect the preprocessing function to config-inited event
    # This runs after configuration is loaded but before any documents are read
    app.connect("config-inited", preprocess_readme_for_sphinx)
