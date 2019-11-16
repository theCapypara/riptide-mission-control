import graphene

from riptide.config.document.app import App as AppDoc
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document


AppConfigurationGraphqlDocument = create_graphl_document(AppDoc, "AppConfiguration", AppDoc.__doc__)


# noinspection PyMethodMayBeStatic,PyMethodParameters
class AppGraphqlDocument(graphene.ObjectType):
    """
    An application that describes as set of commands and services for a Riptide project
    """
    class Meta:
        name = "App"

    config = graphene.Field(
        AppConfigurationGraphqlDocument,
        required=True, description="Processed configuration as loaded from YAML files"
    )

    def resolve_config(parent, info):
        if isinstance(parent, AppGraphqlDocument):
            return AppConfigurationGraphqlDocument(parent.config)
        elif isinstance(parent, AppDoc):
            return AppConfigurationGraphqlDocument(parent)
