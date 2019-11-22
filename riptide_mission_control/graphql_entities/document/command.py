import graphene
from typing import Type

from riptide.config.document.command import Command as CommandDoc
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document
from riptide_mission_control import PROJECT_CACHE_TIMEOUT

ref: Type[graphene.ObjectType] = None
NormalCommandConfiguration = create_graphl_document(CommandDoc, "NormalCommandConfiguration", CommandDoc.__doc__, CommandDoc.schema_normal)
AliasCommandConfiguration = create_graphl_document(CommandDoc, "AliasCommandConfiguration", CommandDoc.__doc__, CommandDoc.schema_alias)


class CommandConfiguration(graphene.Union):
    class Meta:
        types = (NormalCommandConfiguration, AliasCommandConfiguration)


# noinspection PyMethodMayBeStatic,PyMethodParameters
class CommandGraphqlDocument(graphene.ObjectType):
    """
    A command object. Specifies a CLI command to be executable by the user.
    """
    class Meta:
        name = "Command"

    config = graphene.Field(
        CommandConfiguration,
        required=True, description=f"Processed configuration as loaded from YAML files. "
                                   f"This may be cached for {PROJECT_CACHE_TIMEOUT}s. "
                                   f"See mutation flush_cache to clear."
    )

    def resolve_config(parent, info):
        subject = None
        if isinstance(parent, CommandGraphqlDocument):
            subject = parent.config
        elif isinstance(parent, CommandDoc):
            subject = parent

        if "aliases" in subject:
            return AliasCommandConfiguration(subject)
        return NormalCommandConfiguration(subject)
