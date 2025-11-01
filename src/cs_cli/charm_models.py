import re
import typing as t
import xml.etree.ElementTree as ET
from io import BytesIO

from pydantic import BaseModel, Field, validator
from pydantic.typing import get_origin
from pydantic.utils import lenient_issubclass

BoolType = t.Literal["true", "false"]
CharmContextNames = t.Literal[
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
    "Handlebars",
]

charm_variable_rgx = re.compile(r"\$([a-z_A-Z\d]+)\$")
digits_rgx = re.compile(r"^\d+$")

# Todo: check out pydantic-xml package that allows also de-serializing an ElementTree


def create_element(key: str, parent=None, attribs: None | t.Dict[str, str] = None):
    attribs = attribs or {}
    if parent is None:
        return ET.Element(key, attribs)
    return ET.SubElement(parent, key, attribs)


class XmlMixin(BaseModel):
    """pydantic mixin to render a model as xml."""

    _xml_tag = "default"

    def to_ET(self, parent=None, exclude=None):
        exclude = exclude or set()

        def include(field_val):
            if isinstance(field_val, str):
                return True
            return False

        data = self.dict(exclude=exclude)
        elem_data = {k: v for k, v in data.items() if include(v)}
        elem = create_element(self._xml_tag, parent, elem_data)

        def register_field(key, model_field):
            origin = get_origin(model_field.outer_type_)
            if not lenient_issubclass(model_field.type_, XmlMixin):
                # print(f'Skipped (not a subclass): {key}')
                # print(f'origin: {origin}')
                # print(f'field type: {model_field.type_}')
                return

            if origin in (list, set, tuple):
                for model in getattr(self, key) or []:
                    try:
                        model.to_ET(elem)
                    except AttributeError:
                        return
            try:
                # print(f'field type: {model_field.type_}')
                getattr(self, key).to_ET(elem)
            except AttributeError:
                return

        for key, model_field in self.__fields__.items():
            if key in elem_data:
                continue
            register_field(key, model_field)

        return elem

    def xml(self, indent: int = 2, encoding: str = "utf-8"):
        """Renders the xml template"""
        et = ET.ElementTree(self.to_ET())
        ET.indent(et, indent * " ")
        d = BytesIO()
        et.write(d, encoding=encoding)
        d.seek(0)
        return d.getvalue().decode(encoding=encoding)


def charm_extract_vars(snippet_val: str):
    m = charm_variable_rgx.findall(snippet_val)
    return m


extmarks_variable_rgx = re.compile(r"\${?(\d*):?([a-z_A-Z\d]*)}?")


def extmark_extract_vars(snippet_val: str):
    tuples = extmarks_variable_rgx.findall(snippet_val)
    return tuple(m[1] for m in tuples)


def transform_extmark_to_pycharm(content: str):
    def replace(match):
        g = match.group(2) or match.group(1)
        return f"${g}$"

    return extmarks_variable_rgx.sub(replace, content)


def transform_pycharm_to_extmark(content):
    count = 0

    def replace(occ: re.Match):
        nonlocal count
        gmatch = occ.group(1)
        if gmatch == "0":
            return f"${gmatch}"
        if digits_rgx.match(gmatch):
            count += 1
            return f"${gmatch}"
        count += 1
        return f"${{{count}:{gmatch}}}"

    return charm_variable_rgx.sub(replace, content)


class CharmVariable(XmlMixin):
    _xml_tag = "variable"
    name: str
    expression: str = ""
    defaultValue: str = ""
    alwaysStopAt: BoolType = "true"


class TemplateContextOption(XmlMixin):
    _xml_tag = "option"
    name: CharmContextNames = "OTHER"
    value: BoolType = "true"


class TemplateContext(XmlMixin):
    """Describes in which context the snippets is active. If the snippets should be
    used everywhere, one context with option.name == 'OTHER' is used (the default)"""

    _xml_tag = "context"
    __root__: t.List[TemplateContextOption] = [TemplateContextOption()]


class CharmTemplate(XmlMixin):
    _xml_tag = "template"
    name: str
    value: str
    description: str = ""
    variables: t.Optional[t.Set[CharmVariable]] = None
    context: TemplateContext = Field(TemplateContext())
    toReformat: BoolType = "false"
    toShortenFQNames: BoolType = "true"

    @validator("variables", always=True)
    def validate_variables(cls, value, values):
        content = values.get("value")
        if not content:
            return value
        if value:
            return value
        vars_extracted = charm_extract_vars(content)
        if not vars_extracted:
            vars_extracted = extmark_extract_vars(content)
            if vars_extracted:
                values["value"] = transform_extmark_to_pycharm(content)
        return (
            list(CharmVariable(name=n) for n in sorted(set(vars_extracted)))
            if vars_extracted
            else None
        )

    @validator("context")
    def validate_context(cls, value):
        """Make sure the option with name 'OTHER' is the only
        one if chosen so since it includes all contexts"""
        if not value:
            return value
        new_val = value
        for option in value.__root__:
            if option.name == "OTHER":
                new_val.__root__ = [option]
                return new_val
        return new_val


class TemplateSet(XmlMixin):
    """A representation of a Pycharm Live Snippet Template file."""

    _xml_tag = "templateSet"
    group: str
    templates: t.List[CharmTemplate]
