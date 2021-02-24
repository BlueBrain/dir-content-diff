import imp
import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 6):
    sys.exit("Sorry, Python < 3.6 is not supported")

# Read the contents of the README file
with open("README.rst", encoding="utf-8") as f:
    README = f.read()

reqs = [
    "dictdiffer",
    "diff_pdf_visually>=1.5.1",
    "PyYaml",
]
doc_reqs = [
    "sphinx",
    "sphinx-bluebrain-theme",
]
pandas_reqs = ["pandas"]
voxcell_reqs = ["voxcell"]
test_reqs = [
    "rst2pdf",
    "pytest",
    "pytest-cov",
    "pytest-html",
]

VERSION = imp.load_source("", "dir_content_diff/version.py").VERSION

setup(
    name="dir-content-diff",
    author="bbp-ou-cells",
    author_email="bbp-ou-cells@groupes.epfl.ch",
    description="Simple tool to compare directory contents.",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://bbpteam.epfl.ch/documentation/projects/dir-content-diff",
    project_urls={
        "Tracker": "https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
        "Source": "ssh://bbpcode.epfl.ch/common/dir-content-diff",
    },
    license="BBP-internal-confidential",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.6",
    install_requires=reqs,
    extras_require={
        "pandas": pandas_reqs,
        "voxcell": voxcell_reqs,
        "docs": doc_reqs + pandas_reqs + voxcell_reqs,
        "test": test_reqs + pandas_reqs + voxcell_reqs,
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
