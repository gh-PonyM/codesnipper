import re
import typing as t
from pathlib import Path

from click import get_app_dir

from cs_cli.types import TransformT

fn_rgx = re.compile(r"([\w_])\.([a-z]+)$")


def snippet_folders(root: Path):
    exclude = {"tests", "__pycache__", "cs_cli"}
    for f in root.iterdir():
        if f.is_file():
            continue
        ending = f.parts[-1]
        if ending.startswith(".") or ending in exclude:
            continue
        yield f


def file_ending(fn: str, group: int = 2) -> str | None:
    m = fn_rgx.search(fn)
    return m.group(group) if m else None


def yield_lines(
    content: str, transformers: t.Sequence[TransformT]
) -> t.Generator[str, None, None]:
    """Processes a str line-wise using transform functions. If a transformer returns None, the line is excluded"""

    def process_transformers(li: str | None):
        for func in transformers:
            if li is None:
                break
            li = func(li)
        return li

    for line in content.splitlines():
        line = process_transformers(line)
        if line is not None:
            yield line


def application_dir(name: str):
    """Fixes click.get_app_dir lowercasing app name for unix"""
    p = Path(get_app_dir(name))
    return p.parent / name
