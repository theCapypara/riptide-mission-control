import graphene

from riptide.config.loader import load_config, load_projects, load_config_by_project_name
from riptide_mission_control.graphql_entities.document.config import create_config_document
from riptide_mission_control.graphql_entities.document.project import ProjectGraphqlDocument
from riptide_mission_control.registry import registry


ConfigGraphqlDocument = create_config_document()


# noinspection PyMethodParameters,PyMethodMayBeStatic
class Query(graphene.ObjectType):
    project = graphene.Field(ProjectGraphqlDocument, name=graphene.String(required=True),
                             description="Returns a project by name")
    all_projects = graphene.Field(graphene.List(ProjectGraphqlDocument),
                                  description="Returns all projects registered to Riptide")
    config = graphene.Field(ConfigGraphqlDocument,
                            description="Returns the system configuration")

    def resolve_config(parent, info):
        return ConfigGraphqlDocument(registry().system_config)

    def resolve_project(parent, info, name):
        try:
            return ProjectGraphqlDocument(load_config_by_project_name(name)["project"])
        except Exception as ex:
            # todo exception
            raise Exception("project not found") from ex

    def resolve_all_projects(parent, info):
        project_files = load_projects()
        projects = []
        for project_file in project_files.values():
            try:
                project_load_result = load_config(project_file)
                if "project" not in project_load_result:
                    continue # TODO: Error?
                projects.append(ProjectGraphqlDocument(project_load_result["project"]))
            except Exception as ex:
                # todo: deal with project load errors
                pass

        return projects
