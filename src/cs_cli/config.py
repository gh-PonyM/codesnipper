import typing as t

from pydantic import BaseModel, Field

from cs_cli.charm_models import CharmContextNames
from cs_cli.codium_models import DefaultLangID


class SnippetsConfig(BaseModel):
    """Config to place in a snippet directory for the various editors"""

    pycharm_contexts: t.Sequence[CharmContextNames] = Field(
        ["OTHER"],
        description="PyCharm's limited list of contexts, where OTHER stands for a global template",
    )
    vscode_lang_ids: t.Sequence[str] = Field(
        [],
        description="Language identifiers used by VSCode. Will include all the snippets in a json file per identifier",
    )


class StrictSnippetsConfig(SnippetsConfig):
    vscode_lang_ids: t.Sequence[DefaultLangID] = Field(
        [],
        description="Language identifiers used by VSCode. Will include all the snippets in a json file per identifier",
    )
