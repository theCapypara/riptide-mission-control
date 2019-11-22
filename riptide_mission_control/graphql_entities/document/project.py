import os

import graphene
from typing import Union

from riptide.config.document.project import Project as ProjectDoc
from riptide.config.files import get_project_setup_flag_path
from riptide.db.environments import DbEnvironments
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document
from riptide_mission_control import PROJECT_CACHE_TIMEOUT
from riptide_mission_control.registry import registry

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
        required=True, description=f"Processed configuration as loaded from YAML files. "
                                   f"This may be cached for {PROJECT_CACHE_TIMEOUT}s. "
                                   f"See mutation flush_cache to clear."
    )

    path = graphene.Field(
        graphene.String,
        required=True, description="Path to the project file"
    )

    is_setup = graphene.Field(
        graphene.Boolean,
        description="Whether or not the project was set-up by running the 'setup' command on CLI. "
                    "Please note, that this server still allows you to perform all actions on projects, "
                    "even if they are not marked as set-up."
    )

    db_available = graphene.Field(
        graphene.Boolean,
        description="Whether or not database features are available"
    )

    db_list = graphene.List(
        graphene.String,
        description="List of database environments, if database features are available"
    )

    db_current = graphene.Field(
        graphene.String,
        description="Name of current database environments, if database features are available"
    )

    def resolve_config(parent, info):
        return ProjectConfigurationGraphqlDocument(_get_project_doc(parent))

    def resolve_path(parent, info):
        return _get_project_doc(parent)["$path"]

    def resolve_is_setup(parent, info):
        return os.path.exists(get_project_setup_flag_path(_get_project_doc(parent).folder()))

    def resolve_db_available(parent, info):
        return DbEnvironments.has_db(_get_project_doc(parent))

    def resolve_db_list(parent, info):
        if not DbEnvironments.has_db(_get_project_doc(parent)):
            return None
        dbenv = DbEnvironments(_get_project_doc(parent), registry().engine)
        return dbenv.list()

    def resolve_db_current(parent, info):
        if not DbEnvironments.has_db(_get_project_doc(parent)):
            return None
        dbenv = DbEnvironments(_get_project_doc(parent), registry().engine)
        return dbenv.currently_selected_name()


def _get_project_doc(inp: Union[ProjectGraphqlDocument, ProjectDoc]) -> ProjectDoc:
    if isinstance(inp, ProjectGraphqlDocument):
        return inp.config
    elif isinstance(inp, ProjectDoc):
        return inp
