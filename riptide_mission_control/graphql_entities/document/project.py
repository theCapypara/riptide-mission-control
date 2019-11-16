import graphene

from riptide.config.document.project import Project as ProjectDoc
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document


ProjectConfigurationGraphqlDocument = create_graphl_document(ProjectDoc, "ProjectConfiguration", ProjectDoc.__doc__)


# noinspection PyMethodMayBeStatic,PyMethodParameters
class ProjectGraphqlDocument(graphene.ObjectType):
    """
    A Riptide project
    """
    class Meta:
        name = "Project"

    config = graphene.Field(
        ProjectConfigurationGraphqlDocument,
        required=True, description="Processed configuration as loaded from YAML files"
    )

    def resolve_config(parent, info):
        if isinstance(parent, ProjectGraphqlDocument):
            return ProjectConfigurationGraphqlDocument(parent.config)
        elif isinstance(parent, ProjectDoc):
            return ProjectConfigurationGraphqlDocument(parent)
