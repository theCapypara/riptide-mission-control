import traceback
from graphql import GraphQLError
from rx.subjects import ReplaySubject
from typing import List, Dict

from riptide.engine.results import EndResultQueue, ResultError
from riptide_mission_control.graphql_entities.subscriptions.utils import async_in_executor, StartStopEndStep, \
    StartStopProgressStep, ResultStep
from riptide_mission_control.project_loader import load_single_project
from riptide_mission_control.registry import registry


@async_in_executor
async def project_start_impl(subject: ReplaySubject, project_name: str, services: List[str]):
    try:
        project = load_single_project(project_name).config
    except GraphQLError as ex:
        subject.on_next(StartStopEndStep(
            error_string=str(ex),
            is_fatal_error=True
        ))
        subject.on_completed()
        return
    engine = registry().engine

    if len(services) < 1:
        services = project["app"]["services"].keys()

    last_steps: Dict[str, int] = {}

    try:
        async for service_name, status, finished in engine.start_project(project, services):
            _handle_update(finished, last_steps, service_name, status, subject, "Service started!")
    except Exception as err:
        print(traceback.format_exc())
        subject.on_next(StartStopEndStep(
            error_string="Error starting the services: " + str(err),
            is_fatal_error=True
        ))
    else:
        subject.on_next(StartStopEndStep())

    subject.on_completed()


@async_in_executor
async def project_stop_impl(subject: ReplaySubject, project_name: str, services: List[str]):
    try:
        project = load_single_project(project_name).config
    except GraphQLError as ex:
        subject.on_next(StartStopEndStep(
            error_string=str(ex),
            is_fatal_error=True
        ))
        subject.on_completed()
        return
    engine = registry().engine

    if len(services) < 1:
        services = project["app"]["services"].keys()

    last_steps: Dict[str, int] = {}

    try:
        async for service_name, status, finished in engine.stop_project(project, services):
            _handle_update(finished, last_steps, service_name, status, subject, "Service stopped!")
    except Exception as err:
        print(traceback.format_exc())
        subject.on_next(StartStopEndStep(
            error_string="Error stopping the services: " + str(err),
            is_fatal_error=True
        ))
    else:
        subject.on_next(StartStopEndStep())

    subject.on_completed()


def _handle_update(finished, last_steps, service_name, status, subject, default_end_msg):
    if status and not isinstance(status, EndResultQueue):
        # normal update
        steps = status.steps if status.steps is not None else 1
        subject.on_next(StartStopProgressStep(
            service=service_name,
            state=ResultStep(
                steps=steps,
                current_step=status.current_step,
                text=status.text
            )
        ))
        last_steps[service_name] = status.steps
    else:
        # end
        steps = last_steps[service_name] if service_name in last_steps else 1
        msg = default_end_msg
        is_error = isinstance(status, ResultError)
        if is_error:
            msg = status.message
        subject.on_next(StartStopProgressStep(
            service=service_name,
            state=ResultStep(
                steps=steps,
                current_step=steps,
                text=msg,
                is_end=finished,
                is_error=is_error
            )
        ))
