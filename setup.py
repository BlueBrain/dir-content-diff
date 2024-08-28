"""Setup for the dir-content-diff package."""
import json
from pathlib import Path

from setuptools import find_namespace_packages
from setuptools import setup

reqs = [
    "dictdiffer>=0.8",
    "dicttoxml>=1.7.12",
    "diff_pdf_visually>=1.7",
    "jsonpath-ng>=1.5",
    "PyYaml>=6",
]

doc_reqs = [
    "docutils<0.21",  # Temporary fix for m2r2
    "m2r2",
    "sphinx",
    "sphinx-bluebrain-theme",
]

# Requirements for custom comparators
with (Path(__file__).parent / "dir_content_diff" / "comparators" / "dependencies.json").open() as f:
    all_comparators = json.load(f)

# Requirements for tests
test_reqs = [
    "coverage>=7.2",
    "dicttoxml>=1.7.16",
    "matplotlib>=3.4",
    "rst2pdf>=0.99",
    "packaging>=20",
    "pandas>=1.4",
    "pytest>=6.2",
    "pytest-html>=2,<4",
]

setup(
    name="dir-content-diff",
    author="Blue Brain Project, EPFL",
    description="Simple tool to compare directory contents.",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://dir-content-diff.readthedocs.io",
    project_urls={
        "Tracker": "https://github.com/BlueBrain/dir-content-diff/issues",
        "Source": "https://github.com/BlueBrain/dir-content-diff",
    },
    license="Apache License 2.0",
    packages=find_namespace_packages(include=["dir_content_diff*"]),
    python_requires=">=3.9",
    use_scm_version=True,
    setup_requires=[
        "setuptools_scm",
    ],
    install_requires=reqs,
    extras_require={
        "all_comparators": list(all_comparators.values()),
        "docs": doc_reqs,
        "test": test_reqs,
        **all_comparators,
    },
    entry_points={
        "pytest11": ["dir-content-diff = dir_content_diff.pytest_plugin"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
