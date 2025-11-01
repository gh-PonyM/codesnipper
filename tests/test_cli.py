from pathlib import Path

import pytest

from cs_cli.main import app
from tests.conftest import fixture_path


def test_cli_help(runner):
    assert "/tmp" in str(
        Path().resolve()
    ), "The runner fixture must be in context of a tempdir"
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
    assert (
        "n_snips.code-snippets" in out
    ), "Unknown folder to language key should result in global snippet filename"
    assert '"css.json": {' in out, "css is a known language identifier"

    # codium_only folder
    assert "codium_only.code-snippets" not in out, "lang id from cs config not used"
    assert "r.json" in out
    assert "rust.json" in out
