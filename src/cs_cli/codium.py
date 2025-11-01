import typing as t

from cs_cli.types import StringOrPath
from cs_cli.utils import application_dir

codium_config_base = application_dir("VSCodium") / "User"
vscode_config_base = application_dir("VSCode") / "User"


def config_dir(
    on_fail: t.Callable[[StringOrPath], None],
):
    config_base = None
    for maybe_dir in (codium_config_base, vscode_config_base):
        if maybe_dir.is_dir():
            config_base = maybe_dir

    if not config_base:
        on_fail("vscodium/vscode not installed.")
        return
    return config_base
