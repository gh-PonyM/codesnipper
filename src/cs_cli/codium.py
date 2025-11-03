from cs_cli.utils import application_dir

codium_config_base = application_dir("VSCodium") / "User"
vscode_config_base = application_dir("VSCode") / "User"
vscode2_config_base = application_dir("Code") / "User"


def config_dirs():
    for maybe_dir in (codium_config_base, vscode_config_base, vscode2_config_base):
        if maybe_dir.is_dir():
            yield maybe_dir
