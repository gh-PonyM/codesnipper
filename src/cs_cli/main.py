import functools
import re
import sys
import typing as t
from functools import lru_cache, partial
from os import getenv
from pathlib import Path

import typer
from pydantic import BaseModel
from rich import print

from cs_cli.charm import config_dir as pycharm_config_dir
from cs_cli.charm_models import CharmTemplate, TemplateContext, TemplateSet
from cs_cli.codium import config_dir as codium_config_dir
from cs_cli.codium_models import (
    DefaultLangID,
    MergeStrategy,
    VSCodeOut,
    VSCodeSnippet,
    VSCodeSnippets,
)
from cs_cli.config import SnippetsConfig, StrictSnippetsConfig
from cs_cli.constants import DEFAULT_PREFIX, SNIPPET_CONFIG, SNIPPETS_ROOT_ENV
from cs_cli.py import remove_python_imports
from cs_cli.types import StringOrPath, TransformT
from cs_cli.utils import file_ending, snippet_folders, yield_lines

app = typer.Typer()


@functools.cache
def snippets_root():
    return Path(getenv(SNIPPETS_ROOT_ENV, "."))


def success(msg):
    print(f"[bold green]{msg}:party_popper:")


def on_fail(msg: StringOrPath):
    print(f"[red]Abort:[/red] {msg}")
    sys.exit(1)


def file_info(f: Path):
    print(f"[bold]File: [magenta]{f.parts[-1]}")


def auto_complete_snippets(ctx: typer.Context, search: str):
    """Autocompletion function for shell completion"""
    selected = ctx.params.get("folders") or []
    for f in snippet_folders(snippets_root()):
        name = f.parts[-1]
        if search in name and name not in selected:
            yield name


def get_snippets_folders():
    return tuple(snippet_folders(snippets_root()))


@lru_cache(typed=True)
def snippets_config(path: Path) -> SnippetsConfig:
    f = (path.parent if path.is_file() else path) / SNIPPET_CONFIG
    if f.is_file():
        return SnippetsConfig.parse_file(f)
    return SnippetsConfig()


def schema_info(model: t.Type[BaseModel], **kwargs):
    typer.echo(model.schema_json(indent=2, **kwargs))
    sys.exit()


def remove_imports(line: str, rm_imports: bool = False) -> str | None:
    return line if not rm_imports else remove_python_imports(line)


def handle_file(
    f: Path,
    line_transforms: t.Dict[str | None, t.Sequence[TransformT]],
) -> tuple[str, str, Path]:
    fn = f.parts[-1]
    ending = file_ending(fn)
    content = f.read_text()
    transformers = line_transforms[ending]

    file_info(f)
    lines = yield_lines(content, transformers)
    snippet_name = re.sub(rf"\.{ending}", "", fn)
    content = re.sub(r"^\n{2,}", "", "\n".join(lines))
    return snippet_name, content, f


def ensure_templates_dir(
    app_dir: Path, template_folder_name: str, out_dir: Path | None = None
):
    templates_dir = out_dir if out_dir else app_dir / template_folder_name
    if not templates_dir.is_dir():
        if not out_dir:
            print(f"{templates_dir.resolve()} does not exist")
            typer.Exit(1)
        templates_dir.mkdir()
    print(f"Snippets path: {templates_dir}")
    return templates_dir


def generate(
    rm_imports: bool,
    folders: t.Sequence[Path],
    templates_dir: Path,
    file_to_model: t.Callable[[str, str, Path], t.Any],
    models_callback: t.Callable,
    write_callback: t.Callable[[Path, t.Any, str], None] | None = None,
    get_fn: t.Callable[[Path], str] | None = None,
    exclude_rgx: str = "",
    dry_run: bool = False,
    print_on_dry_run: bool = True,
):
    transform_by_ending = {
        "py": (partial(remove_imports, rm_imports=rm_imports),),
        None: (lambda x: x,),
        "sh": (lambda x: x,),
    }

    def _file_to_model(folder: Path):
        for file in folder.iterdir():
            if file.is_dir():
                continue
            fn = file.parts[-1]
            if exclude_rgx and re.search(re.escape(exclude_rgx), fn):
                continue
            if fn.startswith("."):
                continue
            yield file_to_model(*handle_file(file, line_transforms=transform_by_ending))

    for folder in folders:
        fn = folder.parts[-1]
        print(f"---- Group name: {fn}")
        models = (te for te in _file_to_model(folder) if te)
        final_model, string_repr = models_callback(models, folder)

        if dry_run:
            if print_on_dry_run:
                print(string_repr)
            continue
        if get_fn and write_callback:
            target = templates_dir / get_fn(folder)
            write_callback(target, final_model, string_repr)


def charm_handle_file(snippet_name: str, content: str, file: Path):
    sn_cfg = snippets_config(file)
    ctx_opts: t.Sequence[str] = sn_cfg.pycharm_contexts
    ctx = TemplateContext.parse_obj([{"name": n} for n in ctx_opts])
    return CharmTemplate(name=snippet_name, value=content, context=ctx)


@app.command()
def config_schema(
    strict: bool = typer.Option(True, help="Show strict schema for VSCode language ids")
):
    """Prints the jsonschema for `cs-confg.json`."""
    cls = StrictSnippetsConfig if strict else SnippetsConfig
    typer.echo(cls.schema_json(indent=2))


@app.command()
def pycharm(
    folders: t.List[Path] = typer.Option(
        get_snippets_folders,
        "--folder",
        "-f",
        autocompletion=auto_complete_snippets,
        help="List of snippets folders that you want to parse",
    ),
    out_dir: t.Optional[Path] = typer.Option(
        None,
        help="Custom output directory. Defaults to the programs snippets directory",
    ),
    version: t.Optional[str] = typer.Option(None, help="Example:: CE2022.1, 2023.2"),
    rm_imports: bool = typer.Option(
        False, help="Remove python import statements in snippets"
    ),
    group_prefix: str = typer.Option(
        DEFAULT_PREFIX, help="Group prefix for pycharm Live Template group"
    ),
    exclude_rgx: str = typer.Option(
        "*.json", help="A regex expression to exclude file name in snippets folders"
    ),
    dry_run: bool = False,
    schema_json: bool = typer.Option(
        False, help="Only show the dataschema for the pycharm config"
    ),
):
    """Generates Live Templates for pycharm using a defined data schema."""

    if schema_json:
        schema_info(TemplateSet)

    cfg_dir = out_dir or pycharm_config_dir(on_fail=on_fail, version=version)
    templates_dir = ensure_templates_dir(cfg_dir, "templates", out_dir)

    def models_callback(models, folder: Path):
        template_set = TemplateSet(
            group=group_prefix + folder.parts[-1], templates=list(models)
        )
        xml_repr = template_set.xml()
        return template_set, xml_repr

    def get_fn(folder: Path):
        return f"{group_prefix}{folder.parts[-1]}.xml"

    def write_template(target: Path, model, string_repr):
        target.write_text(string_repr)

    generate(
        folders=folders,
        rm_imports=rm_imports,
        templates_dir=templates_dir,
        exclude_rgx=exclude_rgx,
        dry_run=dry_run,
        file_to_model=charm_handle_file,
        models_callback=models_callback,
        get_fn=get_fn,
        write_callback=write_template,
        print_on_dry_run=True,
    )


def vscode_handle_file(snippet_name: str, content: str, file: Path):
    return VSCodeSnippet(
        prefix=[snippet_name],
        body=content.splitlines(),
        description=f"from {file.parent.parts[-1]}/{snippet_name}",
    )


@app.command()
def vscode(
    folders: t.List[Path] = typer.Option(
        get_snippets_folders,
        "--folder",
        "-f",
        autocompletion=auto_complete_snippets,
        help="List of snippets folders that you want to parse",
    ),
    out_dir: t.Optional[Path] = typer.Option(
        None,
        help="Custom output directory. Defaults to the programs snippets directory",
    ),
    rm_imports: bool = typer.Option(
        False, help="Remove python import statements in snippets"
    ),
    exclude_rgx: str = typer.Option(
        "*.json", help="A regex expression to exclude file name in snippets folders"
    ),
    strategy: MergeStrategy = typer.Option(
        MergeStrategy.MERGE,
        help="Overwrite or merge existing json snippets. Will only work if comments have been removed",
    ),
    dry_run: bool = False,
    schema_json: bool = typer.Option(
        False, help="Only show the jsonschema for the vscode config"
    ),
):
    """Install snippets for VSCode/VSCodium."""
    if schema_json:
        schema_info(VSCodeSnippets)
    cfg_dir = out_dir or codium_config_dir(on_fail=on_fail)

    snippets_dir = ensure_templates_dir(cfg_dir, "snippets", out_dir)

    lang_ids = set(e.value for e in DefaultLangID)

    model_registry = {}

    def register_for_file(folder, models: VSCodeSnippets):
        sn_cfg = snippets_config(folder)
        lang_ids_ = sn_cfg.vscode_lang_ids
        folder_name = folder.parts[-1]

        if not lang_ids_:
            if folder_name in lang_ids:
                lang_ids_ = (folder_name,)
        if not lang_ids_:
            fn = f"{folder_name}.code-snippets"
            model_registry[fn] = models
            return

        for lang_id in lang_ids_:
            fn = f"{lang_id}.json"
            if fn in model_registry:
                model_registry[fn] += models
            else:
                model_registry[fn] = models

    def models_callback(models: t.Sequence[VSCodeSnippet], folder: Path):
        folder_name = folder.parts[-1]
        data = {f"{folder_name}-{m.prefix[0]}": m for m in models}
        snippets = VSCodeSnippets.parse_obj(data)
        register_for_file(folder, snippets)
        return snippets, snippets.json(indent=2)

    generate(
        folders=folders,
        rm_imports=rm_imports,
        templates_dir=snippets_dir,
        exclude_rgx=exclude_rgx,
        dry_run=dry_run,
        file_to_model=vscode_handle_file,
        models_callback=models_callback,
        print_on_dry_run=False,
    )
    final_model = VSCodeOut.parse_obj(model_registry)
    if dry_run:
        typer.echo(VSCodeOut.__doc__)
        typer.echo(final_model.json(indent=2))
    else:
        final_model.write_files(
            snippets_dir, overwrite=strategy == MergeStrategy.OVERWRITE
        )
