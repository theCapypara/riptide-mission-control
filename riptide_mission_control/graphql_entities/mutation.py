import graphene
from graphql import GraphQLError

from riptide.config.loader import remove_project
from riptide_mission_control.project_loader import flush_caches
from riptide_mission_control import PROJECT_CACHE_TIMEOUT


# noinspection PyMethodParameters,PyMethodMayBeStatic
class Mutation(graphene.ObjectType):
    flush_cache = graphene.Boolean(
        description=f"Flushes the project cache. Loaded projects are normally cached for {PROJECT_CACHE_TIMEOUT}s."
    )

    remove_project = graphene.Boolean(
        name=graphene.String(required=True),
        description=f"Remove a registered project from Riptide, by name. Flushes cache."
    )

    def resolve_flush_cache(parent, info):
        flush_caches()
        return True

    def resolve_remove_project(parent, info, name: str):
        try:
            remove_project(name)
        except KeyError:
            raise GraphQLError(f"Project {name} to remove not found")
        flush_caches()
        return True
