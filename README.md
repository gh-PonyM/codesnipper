# Codesnipper

Manage your collection of code snippets for use in different editors. `cs-cli` helps you generate the correct format for snippets (or LiveTemplates in Pycharm speak) across 
editors using the same source files:

- [PyCharm](https://www.jetbrains.com/help/pycharm/using-live-templates.html)
- [VSCode/VSCodium](https://code.visualstudio.com/docs/editor/userdefinedsnippets)

**Dotfiles** are nice, but why not have a repository with your favorite snippets, that 
you can install for each editor and keep them in sync. Furthermore, there are other benefits:

- **Sharing** snippets is **more easy**
- Test your snippets more easily in a repository (e.g. shellcheck)
- Like dotfiles, you have **version control** (if needed)
- You can **distribute snippets** across a company to users, and merge them with their custom ones (VSCode)


## Installation

I would recommend to use [pipx](https://pypa.github.io/pipx/) to install the tool globally in a separate environment:

    pipx install git+https://github.com/DadaDaMotha/codesnipper.git#main
    pipx install git+ssh://github.com/DadaDaMotha/codesnipper.git#main

Or if you want to install it with user scope:

    pip install --user git+https://github.com/DadaDaMotha/codesnipper.git#main

**Install shell completion**

You can get autocomplete for your snippets folders (`-f` flag), which can be handy

    cs-cli --install-completion


**Tipp**: For users that have their `.bashrc` tracked in a dotfiles repo, I recommend to fix the `.bashrc`:

    # Replace this line
    source /home/<user>/.bash_completions/cs-cli.sh"
    # with one compatible for all your workstations
    source "$HOME/.bash_completions/cs-cli.sh"

### Currently missing features

- Reading json with comments (results in an error)
- Importing Pycharm XML Templates (--> `pydantic-xml` library) and VSCode templates
- Full set of mapping language_ids of VSCode to Pycharm
- Full set of Pycharm Template contexts

### Updating the cli

Since the cli is in development still (but functions fully), use the most up-to-date version:

    pipx reinstall git+https://github.com/DadaDaMotha/codesnipper.git#main
    pipx reinstall git+ssh://github.com/DadaDaMotha/codesnipper.git#main

**How does `cs-cli` know where to look for snippets?**

It's best to **set the environment variable `CODE_SNIPPETS_PATH`** in your `.bashrc`. If set, it will look for snippets 
folder in this directory. Otherwise it will **default to the current working directory** `$PWD`.

**Note**: hidden files `.*` in your snippetes folders (such as `.cs-config.json`) are skipped by default. Otherwise you can still use `--exclude-rgx` option to exclude certain file name patterns.

## Supported snippets formats

**extmark**:

    for ${1:TARGET} in ${2:EXPR_LIST}:
        $0

**pycharm**:

    t.Callable[[$IN$], $OUT$]

**default**

    import typing as t
    import numpy as np

## General transformations

### Python

- Import statements can be stripped out as an option (files with ending `.py`)

## Conversion for PyCharm

- the **filename** is used as the **snippets name**
- the folder name is used as the group, using an additional prefix.

## The `.cs-config.json` file

Each snippet directory can have this config file in order to tell `cs-cli` to which group or 
language it should attribute the snippets. Find the jsonschema with `cs-cli config-schema`:

```json
{
  "title": "StrictSnippetsConfig",
  "description": "Config to place in a snippet directory for the various editors",
  "type": "object",
  "properties": {
    "pycharm_contexts": {
      "title": "Pycharm Contexts",
      "description": "PyCharm's limited list of contexts, where OTHER stands for a global template",
      "default": [
        "OTHER"
      ],
      "type": "array",
      "items": {
        "enum": [
          "OTHER",
          "SHELL_SCRIPT",
          "Python",
          "XML",
          "JSON",
          "CSS",
          "Django",
          "ECMAScript6",
          "HTML",
          "JAVA_SCRIPT",
          "Properties",
          "SQL",
          "TypeScript",
          "Vue",
          "CUCUMBER_FEATURE_FILE",
          "REQUEST",
          "PUPPET_FILE",
          "Handlebars"
        ],
        "type": "string"
      }
    },
    "vscode_lang_ids": {
      "description": "Language identifiers used by VSCode. Will include all the snippets in a json file per identifier",
      "default": [],
      "type": "array",
      "items": {
        "$ref": "#/definitions/DefaultLangID"
      }
    }
  },
  "definitions": {
    "DefaultLangID": {
      "title": "DefaultLangID",
      "description": "Most of the VSCode supported language ids",
      "enum": [
        "bibtex",
        "clozure",
        "c",
        "cpp",
        "csharp",
        "dockercompose",
        "css",
        "dockerfile",
        "go",
        "handlebars",
        "html",
        "java",
        "init",
        "javascript",
        "javascriptreact",
        "latex",
        "less",
        "lua",
        "makefile",
        "markdown",
        "plaintext",
        "powershell",
        "python",
        "r",
        "ruby",
        "rust",
        "scss",
        "shellscript",
        "sql",
        "stylus",
        "swift",
        "typescript",
        "typescriptreact",
        "tex",
        "vue",
        "xml",
        "xsl",
        "yaml"
      ],
      "type": "string"
    }
  }
}
```

The cli determines which language it should attribute a folders snippets to in the following order:

- `.cs-config.json`
- **VSCode**: Uses the folder name if it matches one of the builtin language identifiers
- Assumes a global template

## Examples

Your code-snippets repository might look like this:

```
$ cd my-snippets
$ tree .
.
├── jinja2
│   └── block
├── python
│   ├── dataclass_new
│   └── yield_lines
├── README.md
├── shell
│   ├── forfileincurrdir.sh
└── toml
    ├── poetry_black_cfg
    └── poetry_pytest_cfg
```

### .bashrc entry

Why not use an alias to facility the work further:

```shell
export CODE_SNIPPETS_PATH=$HOME/myrepos/code-snippets

function update-snippets() {
  cd "$CODE_SNIPPETS_PATH" || exit 1
  git stash && git pull --rebase && git stash pop
  which codium && cs-cli vscode
  which code && cs-cli vscode
  which charm && cs-cli pycharm
}
```

Then you can simply call `update-snippets` to update your snippets on your machine 🎉.