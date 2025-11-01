import typing as t
from pathlib import Path

from cs_cli.types import StringOrPath
from cs_cli.utils import application_dir

charm_config_base = application_dir("JetBrains")


def config_dir(
    on_fail: t.Callable[[StringOrPath], None],
    version: t.Optional[str] = None,
    cfg_dir_base: Path = charm_config_base,
):
    if not cfg_dir_base.is_dir():
        on_fail(f"{cfg_dir_base} does not exist")
        return

    patt = "PyCharm*"
    f = tuple(cfg_dir_base.glob(patt))
    if not f:
        on_fail("Pycharm template not found in")
        return
    if len(f) == 1:
        return f[0]
    if version:
        folder = cfg_dir_base / patt.replace("*", version)
        if not folder.is_dir():
            on_fail(f"Directory {folder} does not exist")
            return
        return folder
    installed = "\n".join(str(i) for i in f)
    on_fail(f"There are multiple pycharm directories: \n{installed}")
