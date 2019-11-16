import graphene

from riptide.config.document.service import Service as ServiceDoc
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document


ServiceConfigurationGraphqlDocument = create_graphl_document(ServiceDoc, "ServiceConfiguration", ServiceDoc.__doc__)


# noinspection PyMethodMayBeStatic,PyMethodParameters
class ServiceGraphqlDocument(graphene.ObjectType):
    """
    A service object. Represents the definition and specification for a running service container.
    """
    class Meta:
        name = "Service"

    config = graphene.Field(
        ServiceConfigurationGraphqlDocument,
        required=True, description="Processed configuration as loaded from YAML files"
    )

    def resolve_config(parent, info):
        if isinstance(parent, ServiceGraphqlDocument):
            return ServiceConfigurationGraphqlDocument(parent.config)
        elif isinstance(parent, ServiceDoc):
            return ServiceConfigurationGraphqlDocument(parent)
