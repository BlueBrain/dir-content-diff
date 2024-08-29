"""Test comparators with missing deps."""
import importlib
from subprocess import run

import pytest

import dir_content_diff.comparators


@pytest.mark.comparators_missing_deps
def test_missing_deps(tmp_path):
    """Test missing dependencies."""
    root_dir = importlib.resources.files("dir_content_diff")  # pylint: disable=no-member
    comparator_dir = root_dir / "comparators"
    imported_comparators = [
        f"import dir_content_diff.comparators.{i}\n"
        for i in dir(dir_content_diff.comparators)
        if "_" not in i and (comparator_dir / i).with_suffix(".py").exists()
    ]
    missing_deps_file = tmp_path / "test_missing_deps.py"
    with missing_deps_file.open(mode="w", encoding="utf8") as f:
        f.writelines(imported_comparators)
        f.flush()
    res = run(["python", str(missing_deps_file)], capture_output=True, check=True)
    assert res.stderr.decode() == (
        "Loading the morphio module without the required dependencies installed "
        "(requirements are the following: morphio>=3.3.6 and morph_tool>=2.9). "
        "Will crash at runtime if the related functionalities are used. "
        "These dependencies can be installed with 'pip install dir-content-diff[morphio]'."
        "\n"
        "Loading the voxcell module without the required dependencies installed "
        "(requirement is the following: voxcell>=3.1.1). "
        "Will crash at runtime if the related functionalities are used. "
        "These dependencies can be installed with 'pip install dir-content-diff[voxcell]'.\n"
    )
