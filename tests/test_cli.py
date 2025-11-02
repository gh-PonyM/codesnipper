import json
from pathlib import Path

import pytest

from cs_cli.main import app
from tests.conftest import fixture_path


def test_cli_help(runner):
    assert "/tmp" in str(Path().resolve()), (
        "The runner fixture must be in context of a tempdir"
    )
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


@pytest.mark.parametrize("folder", ("n_snips",))
def test_pycharm(runner, temporary_directory, folder):
    result = runner.invoke(
        app,
        [
            "pycharm",
            "--folder",
            str(fixture_path / folder),
            "--out-dir",
            str(temporary_directory),
            "--dry-run",
        ],
    )
    out = result.stdout
    assert f"Group name: {folder}" in out
    assert '<option name="Python" value="true" />' in out
    assert '<option name="ECMAScript6" value="true" />' in out


@pytest.mark.parametrize("editor", ("vscode",))
def test_python(runner, temporary_directory, editor):
    result = runner.invoke(
        app,
        [
            editor,
            "--folder",
            str(fixture_path / "python"),
            "--out-dir",
            str(temporary_directory),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    out = result.stdout


def test_codium(runner, temporary_directory):
    # tests using env var CODE_SNIPPETS_PATH
    result = runner.invoke(
        app,
        [
            "vscode",
            "--out-dir",
            str(temporary_directory),
            "--dry-run",
        ],
    )
    out = result.stdout
    assert "Group name: n_snips" in out
    assert "n_snips.code-snippets" in out, (
        "Unknown folder to language key should result in global snippet filename"
    )
    assert '"css.json": {' in out, "css is a known language identifier"

    # codium_only folder
    assert "codium_only.code-snippets" not in out, "lang id from cs config not used"
    assert "r.json" in out
    assert "rust.json" in out
    result = runner.invoke(
        app,
        [
            "vscode",
            "--out-dir",
            str(temporary_directory),
        ],
    )
    assert result.exit_code == 0
    python_file_path = temporary_directory / "Python.json"
    python_json = json.loads(python_file_path.read_text())
    del python_json["python-name_eq_main"]
    python_file_path.write_text(json.dumps(python_json))
    result = runner.invoke(
        app,
        [
            "vscode",
            "--out-dir",
            str(temporary_directory),
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0
