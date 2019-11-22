import graphene

from riptide_mission_control.graphql_entities.document.config import create_config_document
from riptide_mission_control.graphql_entities.document.project import ProjectGraphqlDocument
from riptide_mission_control.project_loader import load_single_project, load_all_projects, get_project_list
from riptide_mission_control.registry import registry


ConfigGraphqlDocument = create_config_document()


class ProjectLoadError(graphene.ObjectType):
    name = graphene.Field(graphene.ID, required=True)
    error = graphene.Field(graphene.String, required=True)
    path = graphene.Field(graphene.String, required=True)


class MultiProjectsLoadResult(graphene.ObjectType):
    errors = graphene.Field(graphene.List(ProjectLoadError),
                            description="List of errors", required=True)
    projects = graphene.Field(graphene.List(ProjectGraphqlDocument),
                              description="List of successfully loaded projects", required=True)


# noinspection PyMethodParameters,PyMethodMayBeStatic
class Query(graphene.ObjectType):
    project = graphene.Field(ProjectGraphqlDocument, name=graphene.String(required=True),
                             description="Returns a project by name. Fails on error.")
    all_project_names = graphene.Field(graphene.List(graphene.String),
                                       description="Returns all projects names registered to Riptide. "
                                                   "Does not load projects.")
    all_projects = graphene.Field(MultiProjectsLoadResult,
                                  description="Returns all projects registered to Riptide.")
    config = graphene.Field(ConfigGraphqlDocument,
                            description="Returns the system configuration.")

    def resolve_config(parent, info):
        return ConfigGraphqlDocument(registry().system_config)

    def resolve_project(parent, info, name):
        return load_single_project(name)

    def resolve_all_project_names(parent, info):
        return get_project_list().keys()

    def resolve_all_projects(parent, info):
        return load_all_projects()
