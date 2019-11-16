"""Parses definitions from YamlConfigDocument schema docstrings"""
from docutils.nodes import block_quote, definition_list, term, definition, system_message, paragraph

from docutils.examples import internals

SCHEMA_DOC_TEXT_FOR_LIST = "<<text>>"


def extract_from_schema(docstring) -> dict:
    """
    Converts a docstring containing a block qoute that contains a definition list
    into a dict of descriptions.

    Definition entries must contain paragraphs.
    Alternatively entries may also have definition list as children. If this is the case
    and they also have a paragraph, then this paragraph will be stored in <<text>>.
    """
    doc, _ = internals(docstring, settings_overrides={'report_level': 6})
    bq = next(d for d in doc.children if type(d) == block_quote)
    dl = next(d for d in bq.children if type(d) == definition_list)
    return _extract(dl)


def _extract(dl):
    items = {}
    for dli in dl.children:
        dli_term = next(d for d in dli.children if type(d) == term)
        name = str(dli_term.children[0]).split(' ')[0].rstrip(':]').lstrip('[')
        dli_definition = next(d for d in dli.children if type(d) == definition)
        inner_paragraphs = [d for d in dli_definition.children if type(d) == paragraph]
        inner_dls = [d for d in dli_definition.children if type(d) == definition_list]
        if len(inner_paragraphs) > 0 and len(inner_dls) > 0:
            # Contains both a description and sub-fields
            items[name] = _extract(inner_dls[0])
            items[name][SCHEMA_DOC_TEXT_FOR_LIST] = inner_paragraphs[0].children[0]
        elif len(inner_dls) > 0:
            # Contains sub-fields
            items[name] = _extract(inner_dls[0])
        elif len(inner_paragraphs) > 0:
            # Contains a description
            items[name] = str(inner_paragraphs[0].children[0])
        else:
            raise Exception(f"Invalid schema description for {name}. Field description must contain paragraph or definition list")
    return items
