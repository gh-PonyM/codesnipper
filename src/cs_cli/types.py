import typing as t
from pathlib import Path

StringOrPath = t.Union[str, Path]
TransformT = t.Callable[[str], str | None]
