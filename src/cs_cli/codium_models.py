import json
import typing as t
from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class MergeStrategy(str, Enum):
    OVERWRITE = "overwrite"
    MERGE = "merge"


class DefaultLangID(str, Enum):
    """Most of the VSCode supported language ids"""

    BIBTEXT = "bibtex"
    CLOZURE = "clozure"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    COMPOSE = "dockercompose"
    CSS = "css"
    DOCKERFILE = "dockerfile"
    GO = "go"
    HANDLEBARS = "handlebars"
    HTML = "html"
    JAVA = "java"
    INI = "init"
    JS = "javascript"
    JSX = "javascriptreact"
    LATEX = "latex"
    LESS = "less"
    LUA = "lua"
    MAKEFILE = "makefile"
    MARKDOWN = "markdown"
    PLAINTEXT = "plaintext"
    POWER_SHELL = "powershell"
    PYTHON = "python"
    R = "r"
    RUBY = "ruby"
    RUST = "rust"
    SCSS = "scss"
    SHELL = "shellscript"
    SQL = "sql"
    STYLUS = "stylus"
    SWIFT = "swift"
    TYPESCRIPT = "typescript"
    TYPESCRIPT_REACT = "typescriptreact"
    TEX = "tex"
    VUE = "vue"
    XML = "xml"
    XSL = "xsl"
    YAML = "yaml"


class VSCodeSnippet(BaseModel):
    """Represents a single snippet entry without the parent key"""

    prefix: list[str]
    body: list[str]
    description: str = ""


class VSCodeSnippets(BaseModel):
    """Represents a valid VSCode snippets json"""

    __root__: t.Dict[str, VSCodeSnippet]

    def __add__(self, other):
        d = self.__root__.copy()
        d.update(other.__root__)
        return VSCodeSnippets(__root__=d)


class VSCodeOut(BaseModel):
    """Represents the mapping of filenames to accumulated snippets.
    The filename is the language identifier grouping key"""

    __root__: t.Dict[str, VSCodeSnippets]

    def write_files(self, path: Path, overwrite: bool = True):
        for fn, items in self.__root__.items():
            file = path / fn
            if not file.is_file() or overwrite:
                file.write_text(items.json(indent=2))
                continue
            data = json.loads(file.read_text())
            data.update(items.dict()["__root__"])
            new_items = items.__class__.parse_obj(data)
            file.write_text(new_items.json(indent=2))
