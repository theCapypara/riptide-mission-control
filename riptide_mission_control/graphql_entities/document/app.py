import graphene
from typing import Union

from riptide.config.document.app import App as AppDoc
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document
from riptide_mission_control import PROJECT_CACHE_TIMEOUT

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
        required=True, description=f"Processed configuration as loaded from YAML files. "
                                   f"This may be cached for {PROJECT_CACHE_TIMEOUT}s. "
                                   f"See mutation flush_cache to clear."
    )

    def resolve_config(parent, info):
        return AppConfigurationGraphqlDocument(_get_app_doc(parent))


def _get_app_doc(inp: Union[AppGraphqlDocument, AppDoc]) -> AppDoc:
    if isinstance(inp, AppGraphqlDocument):
        return inp.config
    elif isinstance(inp, AppDoc):
        return inp
