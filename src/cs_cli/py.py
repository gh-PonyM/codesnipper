import re

imports_rgx = re.compile(r"^(from |import )")


def remove_python_imports(line: str) -> str | None:
    return None if imports_rgx.search(line) else line
