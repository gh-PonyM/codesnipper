from textwrap import dedent

import pytest

from cs_cli.charm_models import (
    CharmTemplate,
    extmarks_variable_rgx,
    transform_extmark_to_pycharm,
    transform_pycharm_to_extmark,
)


@pytest.mark.parametrize("text", ("${5:foo}", "$544"))
def test_extmark_rgx(text):
    assert extmarks_variable_rgx.match(text)


@pytest.mark.parametrize(
    "in_,expected",
    (
        ("$TARGET$", "${1:TARGET}"),
        ("$0$", "$0"),
        ("$10$", "$10"),
        ("$var$ $0$", "${1:var} $0"),
        ("$var$ $2$ $other$ $5$", "${1:var} $2 ${3:other} $5"),
    ),
)
def test_extmark_conversion(in_, expected):
    """Test conversion from pycharm format to vscode format and vice version. Also test the ordering and enumeration of
    replacements.

    References:
    - https://code.visualstudio.com/docs/editor/userdefinedsnippets#_create-your-own-snippets

    """
    assert expected == transform_pycharm_to_extmark(in_)
    assert in_ == transform_extmark_to_pycharm(expected)

@pytest.mark.parametrize(
    "content,vars",
    (
        ("t.Callable[[$IN$], $OUT$]", ["IN", "OUT"]),
        ("$var$ = 'TEMPLATE{$var$}'", ["var"]),
        ("for ${1:TARGET} in ${2:EXPR_LIST}:", ["TARGET", "EXPR_LIST"]),
        (
            dedent(
                """\
        import foo as bar
        
        for item in items:
            print(item)
        """
            ),
            None,
        ),
    ),
)
def test_variables_charm(content, vars):
    """Test parsing the variables from different snippets formats. Add an entry for each supported format"""

    template = CharmTemplate(name="testsnippet", value=content)
    if vars:
        assert (
            template.variables
        ), "The variables should be extract from the content if not set"
        assert sorted(vars) == [v.name for v in template.variables]
        print(list(template.variables)[0].xml())
        xml = template.xml()
        print(xml)
        assert "<variable" in xml
    else:
        assert not template.variables

    # Default using this context to add the template everywhere
    assert template.context.__root__[0].name == "OTHER"

    if "${1" in content:
        print(template.value)
        assert (
            f"${vars[0]}$" in template.value
        ), "The value must be adapted to fit the pycharm format"
