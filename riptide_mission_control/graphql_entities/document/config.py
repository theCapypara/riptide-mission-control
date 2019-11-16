import graphene
from typing import Type

from riptide.config.document.config import Config
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document


def create_config_document() -> Type[graphene.ObjectType]:
    """
    Generates the SystemConfiguration GraphQL type
    """
    return create_graphl_document(Config, "SystemConfiguration", Config.__doc__, skip_keys=["project"])
