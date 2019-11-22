import asyncio
import graphene
from rx.subjects import ReplaySubject

from riptide_mission_control.graphql_entities.subscriptions.db import db_copy_impl, db_new_impl, \
    db_switch_subscriber_impl, db_drop_impl
from riptide_mission_control.graphql_entities.subscriptions.misc import update_repositories_impl, update_images_impl
from riptide_mission_control.graphql_entities.subscriptions.start_stop import project_start_impl, project_stop_impl
from riptide_mission_control.graphql_entities.subscriptions.utils import ResultStep, StartStopResultStep


# noinspection PyMethodMayBeStatic,PyMethodParameters
class Subscription(graphene.ObjectType):
    """
    Most subscriptions are used as "asynchronous" mutations (those returning ResultStep).
    They are used in places, where mutations might take too long.

    Generally, subscribing to any of the "asynchronous" mutations will start executing them. There are no
    checks for multiple processes for the same query running at the same time. Subscribing multiple times
    WILL execute the operation again.

    Each of these subscriptions sends progress reports and signals when it's done / an error occurred.
    """
    update_repositories = graphene.Field(
        ResultStep,
        description="Update all Riptide repositories and reload the system configuration. "
                    "Please note any error messages during the update!"
                    ""
                    "IMPORTANT: Currently updating repositories freezes when using repos"
                    "that require interactive authentification."
    )

    update_images = graphene.Field(
        ResultStep,
        project_name=graphene.String(required=True),
        description="Update all images used by the specified project"
    )

    project_db_copy = graphene.Field(
        ResultStep,
        project_name=graphene.String(required=True),
        source=graphene.String(required=True, description="DB environment to copy"),
        target=graphene.String(required=True, description="Name of the new database environment"),
        switch=graphene.Boolean(required=False,
                                description="Whether or not to switch to the new environment afterwards "
                                            "If not given: True"),
        description="Copy a database environment to a new destination, if database features are available for project"
    )

    project_db_new = graphene.Field(
        ResultStep,
        project_name=graphene.String(required=True),
        new_name=graphene.String(required=True, description="Name of the new database environment"),
        switch=graphene.Boolean(required=False,
                                description="Whether or not to switch to the new environment afterwards. "
                                            "If not given: True"),
        description="Create a new empty database environment, if database features are available for project"
    )

    project_db_switch = graphene.Field(
        ResultStep,
        project_name=graphene.String(required=True),
        name=graphene.String(required=True, description="Name of the database environment to switch to"),
        description="Switch to a database environment, if database features are available for project"
    )

    project_db_drop = graphene.Field(
        ResultStep,
        project_name=graphene.String(required=True),
        name=graphene.String(required=True, description="Name of the database environment to delete"),
        description="Deletes a database environment, if database features are available for project"
    )

    project_start = graphene.Field(
        StartStopResultStep,
        project_name=graphene.String(required=True),
        services=graphene.List(graphene.String, required=False,
                               description="List of services to start, if not given starts all"),
        description="Start services of a project. Services that are already started are NOT restarted."
    )

    project_stop = graphene.Field(
        StartStopResultStep,
        project_name=graphene.String(required=True),
        services=graphene.List(graphene.String, required=False,
                               description="List of services to stop, if not given stops all."),
        description="Stop services of a project."
    )

    def resolve_update_repositories(parent, info):
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, update_repositories_impl, subject)
        return subject

    def resolve_update_images(parent, info, project_name: str):
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, update_images_impl, subject, project_name)
        return subject

    def resolve_project_db_copy(parent, info, project_name: str, source: str, target: str, switch=True):
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, db_copy_impl, subject, project_name, source, target, switch)
        return subject

    def resolve_project_db_new(parent, info, project_name: str, new_name: str, switch=True):
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, db_new_impl, subject, project_name, new_name, switch)
        return subject

    def resolve_project_db_switch(parent, info, project_name: str, name: str):
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, db_switch_subscriber_impl, subject, project_name, name)
        return subject

    def resolve_project_db_drop(parent, info, project_name: str, name: str):
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, db_drop_impl, subject, project_name, name)
        return subject

    def resolve_project_start(parent, info, project_name: str, services=None):
        if services is None:
            services = []
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, project_start_impl, subject, project_name, services)
        return subject

    def resolve_project_stop(parent, info, project_name: str, services=None):
        if services is None:
            services = []
        subject = ReplaySubject()
        asyncio.get_event_loop().run_in_executor(None, project_stop_impl, subject, project_name, services)
        return subject
