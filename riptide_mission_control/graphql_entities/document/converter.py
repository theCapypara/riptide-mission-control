"""Module for converting YamlConfigDocument classes of Riptide into graphene schema classes."""
import graphene
import logging
import re
from graphene import Schema
from graphene.types.generic import GenericScalar
from graphql import GraphQLList
from schema import Schema, Optional, Or
from typing import Type, Dict, Union, List

from configcrunch import DocReference, YamlConfigDocument
from riptide.config.document.config import Config
from riptide.config.document.project import Project
from riptide.config.document.app import App
from riptide.config.document.service import Service
from riptide.config.document.command import Command
from riptide_mission_control import LOGGER_NAME
from riptide_mission_control.schema_docstring_parser import extract_from_schema, SCHEMA_DOC_TEXT_FOR_LIST


logger = logging.getLogger(LOGGER_NAME)
_already_generated_types = {}
_generate_entry_already_generated = {}


class SchemaConversionError(Exception):

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return "Schema conversion: " + self.message


def create_graphl_document(
        ycd: Type[YamlConfigDocument],
        name: str,
        descr: str,
        schema_function=None,
        skip_keys: List[str]=None
) -> Type[graphene.ObjectType]:
    """
    Generate a graphene ObjectType from a YamlConfigDocument schema

    :param ycd:             Input document
    :param name:            The name of the document
    :param descr:           Text describing the document
    :param schema_function: A function that returns the schema.
                            The docstring must contain a definition list, describing the schema.
    :param skip_keys:       List of keys to not include in the GraphQL schema
    :return: The graphene ObjectType representing the YamlConfigDocument
    """
    logger.info(f"Generating GraphQL schema for {name}...")
    if not schema_function:
        schema_function = ycd.schema
    if name not in _already_generated_types:
        _already_generated_types[name] = generate_object_type(
                                            generate_fields_from_schema(
                                                name,
                                                schema_function(),
                                                schema_function.__doc__,
                                                skip_keys=skip_keys
                                            ),
                                            name,
                                            descr
                                        )
    return _already_generated_types[name]


def generate_fields_from_schema(
        name: str,
        schema: Schema,
        schema_doc: Union[str, dict],
        skip_keys: List[str]=None
) -> Dict[str, graphene.Field]:
    """
    Convert a schema Schema to a graphene Schema.
    For this some code/logic for processing the Schema is borrowed from schema.
    :param name:        The name of the document
    :param schema:      The schema describing the document
    :param schema_doc:  docstring of the schema must contain a definition list, describing the schema
                        or be a dict returned by schema_docstring_parser
    :param skip_keys:
    :return:
    """
    if skip_keys is None:
        skip_keys = []

    doc_entries = schema_doc
    if type(schema_doc) == str:
        try:
            doc_entries = extract_from_schema(schema_doc)
        except Exception as err:
            raise SchemaConversionError(f"Error reading the docstring of field {name}") from err

    # Sadly schema doesn't have an API to inspect, so we have to use protected fields :(
    # noinspection PyProtectedMember
    schema_obj = schema._schema
    if not type(schema_obj) == dict:
        raise SchemaConversionError(
            "Only dicts are allowed as top-level types for Riptide document schemas"
        )

    d = {}
    for k, v in schema_obj.items():
        required = True
        if type(k) is Optional:
            required = False
            # noinspection PyProtectedMember
            k = k._schema
        # noinspection PyProtectedMember
        kcc = _snake_to_camel(k)
        if not k in doc_entries:
            # Skip undocumented entries
            logger.debug(SchemaConversionError(f"Skipped {k}, it was not documented."))
        elif not kcc.startswith('$') and k not in skip_keys:
            # else: system key. Skip!
            field = _schema_field_to_graphene_field(name + _first_upper(kcc), v, required, doc_entries[k])
            if field is not None:
                d[kcc] = field

    return d


def _generate_union_type(key: str, field: Or):
    """
    Generate a graphene union type from a schema.Or.
    If any but not all of the input types is a scalar, fails.
    If all of the input types are scalars, returns appropriate scalar instead.

    :param key:
    :param field:
    :return:
    """
    # noinspection PyProtectedMember
    args = field._args
    typess = [_schema_field_to_graphene_type(key + str(type(field)).capitalize(), a, True, "") for a in args]
    # Scalars are not supported for Unions. If only scalars, try to return scalar type instead
    if all([issubclass(t, graphene.types.scalars.Scalar) for t in typess]):
        if typess.count(typess[0]) == len(typess):
            # All scalars have the same type
            return typess[0]
        logger.debug(
            SchemaConversionError(f"{key} can be multiple different scalars. This is not recommended.")
        )
        return GenericScalar
    elif any([issubclass(t, graphene.types.scalars.Scalar) for t in typess]):
        raise SchemaConversionError(f"Union with scalar not supported.")

    class Meta:
        types = tuple(typess)

    attrs = {
        'Meta': Meta
    }

    return type(key, (graphene.Union,), attrs)


def _generate_entry(for_type: type):
    """
    Generates a special EntryXyz type
    for for_type with the fields 'key' and 'value', where value has the type for_type
    """

    if for_type not in _generate_entry_already_generated:
        cls = generate_object_type(
            {
                "key": graphene.Field(graphene.String, required=True),
                "value": graphene.Field(for_type, required=True)
            },
            "Entry" + str(for_type),
            f"An named entry in a list of {for_type}"
        )
        _generate_entry_already_generated[for_type] = cls
    return _generate_entry_already_generated[for_type]


def _schema_field_to_graphene_field(
        key: str, field: any, required: bool, field_doc: Union[dict, str]
) -> Union[graphene.List, graphene.Field, None]:
    """
    Generates a graphene field from a schema field
    :param key: Name of the field
    :param field: Input field object
    :param required: Whether or not this field is required
    :param field_doc: Documentation for this field. If field is a dict, a dict describing the field.
                      Dict format specified by schema_docstring_parser
    :return:
    """

    field = _schema_field_to_graphene_type(key, field, required, field_doc)
    if type(field) != graphene.List and field is not None:
        doc = field_doc
        if type(field_doc) is dict:
            doc = field_doc[SCHEMA_DOC_TEXT_FOR_LIST] if SCHEMA_DOC_TEXT_FOR_LIST in field_doc else None
        return graphene.Field(field, required=required, description=doc)
    else:
        return field


def _schema_field_to_graphene_type(key: str, field: any, required: bool, field_doc: Union[dict, str, None]) -> any:
    """
    Converts a schema field into a graphene type
    :param key: Name of the field
    :param field: Input field object
    :param required: Whether or not this field is required
    :param field_doc: Documentation for this field. If field is a dict, a dict describing the field.
                      Dict format specified by schema_docstring_parser
    :return:
    """
    flavour = _priority(field)
    if flavour == ITERABLE:
        # TODO: We assume that the schema type of the list is only one
        if type(field_doc) is not str:
            raise SchemaConversionError(f"Invalid doc {field_doc} for field {key}")
        return graphene.List(
            _schema_field_to_graphene_type(
                key, field[0], False, None
            ), required=required, description=field_doc
        )
    elif flavour == DICT:
        keys = list(field.keys())
        if len(keys) == 1 and keys[0] == str:
            # Schema is {str: ...} -> dynamic keys! Work with a list with the special key id + value instead in GraphQL!
            doc_text = None
            if type(field_doc) == str:
                doc = field_doc
            elif type(field_doc) == dict and "{key}" in field_doc:
                doc = field_doc["{key}"]
                if SCHEMA_DOC_TEXT_FOR_LIST in field_doc:
                    doc_text = field_doc[SCHEMA_DOC_TEXT_FOR_LIST]
            else:
                raise SchemaConversionError(f"Invalid doc {field_doc} for field {key}")
            return graphene.List(_generate_entry(
                _schema_field_to_graphene_type(key, list(field.values())[0], False, doc)
            ), required=required, description=doc_text)
        else:
            # Schema is regular dict
            # Nested ObjectType
            if type(field_doc) is not dict:
                raise SchemaConversionError(f"Invalid doc {field_doc} for field {key}")
            return generate_object_type(
                generate_fields_from_schema(key, Schema(field), field_doc),
                key,
                field_doc[SCHEMA_DOC_TEXT_FOR_LIST] if SCHEMA_DOC_TEXT_FOR_LIST in field_doc else None
            )
    elif field == str or type(field) == str:
        return graphene.String
    elif field == int or type(field) == int:
        return graphene.Int
    elif field == float or type(field) == float:
        return graphene.Float
    elif field == bool or type(field) == bool:
        return graphene.Boolean
    elif flavour == TYPE:
        # Imports would be circular, so we have to do it here.
        if field == Config:
            from riptide_mission_control.graphql_entities.document.config import create_config_document
            return create_config_document()
        if field == Project:
            from riptide_mission_control.graphql_entities.document.project import ProjectGraphqlDocument
            return ProjectGraphqlDocument
        if field == App:
            from riptide_mission_control.graphql_entities.document.app import AppGraphqlDocument
            return AppGraphqlDocument
        if field == Service:
            from riptide_mission_control.graphql_entities.document.service import ServiceGraphqlDocument
            return ServiceGraphqlDocument
        if field == Command:
            from riptide_mission_control.graphql_entities.document.command import CommandGraphqlDocument
            return CommandGraphqlDocument
        else:
            raise SchemaConversionError(f"Don't know how to deal with type {field}")
    elif flavour == VALIDATOR:
        if isinstance(field, DocReference):
            return _schema_field_to_graphene_type(key, field.referenced_doc_type, required, field_doc)
        elif isinstance(field, Or):
            return _generate_union_type(key, field)
        else:
            raise SchemaConversionError(f"Don't know how to deal with validator {type(field)}")
        pass
    elif field == any:
        logger.debug(SchemaConversionError(f"{key} was any. This field will be available as JSON only."))
        return graphene.JSONString
    elif flavour == CALLABLE:
        raise SchemaConversionError(f"Don't know how to deal with callable {key} / {field}")
    else:
        raise SchemaConversionError(f"Don't know how to deal with {field} of type {type(field)}")


def generate_object_type(
        attributes: Dict[str, any],
        namee: str,
        descr: str
) -> Type[graphene.ObjectType]:
    """
    Generate an ObjectType class.
    Contains a default resolver that deals with the structures generated by this conversion module.

    :param attributes: List of class attribues
    :param namee: Name of the meta class
    :param descr: Description of the meta class
    """
    # noinspection PyMethodParameters
    class Meta:
        name = namee
        description = descr

        def default_resolver(attname: str, default_value, root, info, **args):
            return_value = None
            if isinstance(root, dict):
                return_value = root.get(_camel_to_snake(attname), default_value)
            elif hasattr(root, 'data') and isinstance(root.data, dict):
                return_value = root.data.get(_camel_to_snake(attname), default_value)
            elif hasattr(root, 'data') and isinstance(root.data, YamlConfigDocument):
                if _camel_to_snake(attname) in root.data.doc:
                    return_value = root.data.doc[_camel_to_snake(attname)]
                else:
                    return_value = default_value
            else:
                return_value = getattr(root, _camel_to_snake(attname), default_value)
            if isinstance(info.return_type, GraphQLList) and isinstance(return_value, dict):
                # Deal with "Entry" types
                return [{"key": k, "value": v} for k, v in return_value.items()]
            return return_value

    def __init__(self, data):
        self.data = data

    attrs = {
        'Meta': Meta,
        '__init__': __init__

    }

    attrs.update(attributes)

    cls: Type[graphene.ObjectType] = type(namee, (graphene.ObjectType,), attrs)

    return cls


COMPARABLE, CALLABLE, VALIDATOR, TYPE, DICT, ITERABLE = range(6)


def _priority(s):
    """Return priority for a given object. Based on logic in schema."""
    if type(s) in (list, tuple, set, frozenset):
        return ITERABLE
    if type(s) is dict:
        return DICT
    if issubclass(type(s), type):
        return TYPE
    if hasattr(s, 'validate'):
        return VALIDATOR
    if callable(s):
        return CALLABLE
    else:
        return COMPARABLE


def _snake_to_camel(word):
    """Converts snake_case into camelCase"""
    words = word.split('_')
    return ''.join([words[0]] + [x.capitalize() for x in words[1:]])


def _camel_to_snake(attname):
    """Converts camelCase into snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', attname)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _first_upper(k):
    """Returns string k, with the first letter being upper-case"""
    return k[0].upper() + k[1:]
