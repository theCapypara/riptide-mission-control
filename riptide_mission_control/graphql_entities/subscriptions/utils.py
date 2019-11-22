import asyncio

import graphene
from graphql import GraphQLError
from typing import Union

from functools import update_wrapper

import traceback

from riptide.config.document.project import Project
from riptide_mission_control.main import logger
from riptide_mission_control.project_loader import load_single_project


def async_in_executor(f):
    f = asyncio.coroutine(f)

    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(f(*args, **kwargs))
        except Exception as ex:
            logger.critical("Uncaught async error! " + str(ex))
            logger.critical(traceback.format_exc())

    return update_wrapper(wrapper, f)


def try_loading_project(project_name, subject, total_steps, current_step) -> Union[None, Project]:
    try:
        return load_single_project(project_name).config
    except GraphQLError as ex:
        subject.on_next(ResultStep(
            steps=total_steps,
            current_step=current_step,
            text=str(ex),
            is_end=True,
            is_error=True
        ))
        subject.on_completed()
    return None


class ResultStep(graphene.ObjectType):
    """
    A single status update of an asynchronous mutation.

    Clients should stop subscribing when is_end is true!
    """
    def __init__(self, steps, current_step, text, is_end=False, is_error=False, *args, **kwargs):
        self.steps = steps
        self.current_steps = current_step
        self.text = text
        self.is_end = is_end
        self.is_error = is_error
        super().__init__(steps, current_step, text, is_end, is_error, *args, **kwargs)
    steps = graphene.Field(
        graphene.Int,
        description="Total number of steps, may change.",
        required=True
    )
    current_step = graphene.Field(
        graphene.Int,
        description="Current step number.",
        required=True
    )
    text = graphene.Field(
        graphene.String,
        description="Human-readable text describing the current state",
        required=True
    )
    is_end = graphene.Field(
        graphene.Boolean,
        description="Whether or not this is the last message",
        required=True
    )
    is_error = graphene.Field(
        graphene.Boolean,
        description="Whether or not this message indicates an error state. "
                    "Only true, if is_end is also true.",
        required=True
    )


class StartStopProgressStep(graphene.ObjectType):
    """
    A group of status update for starting multiple services. Each one has it's own progress step count.

    Clients should NOT stop subscribing if child ResultSteps is_end is true, this
    only indicates that single services started.

    """
    def __init__(self, service, state, *args, **kwargs):
        self.service = service
        self.state = state
        super().__init__(service, state, *args, **kwargs)
    service = graphene.Field(
        graphene.String,
        description="Name of the service, that the current state update belongs to",
        required=False
    )
    state = graphene.Field(
        ResultStep,
        description="State update for the service",
        required=False
    )


class StartStopEndStep(graphene.ObjectType):
    """
    The end of a start/stop project process.
    Services that could not be started have entries in the errors.
    """
    def __init__(self, error_string=None, is_fatal_error=False, *args, **kwargs):
        self.error_string = error_string
        self.is_fatal_error = is_fatal_error
        super().__init__(error_string, is_fatal_error, *args, **kwargs)

    error_string = graphene.Field(
        graphene.String,
        description="Error message on fatal errors.",
        required=False
    )
    is_fatal_error = graphene.Field(
        graphene.Boolean,
        description="If true, the service starting failed fatally. "
                    "Even services that are not in errors may not be started.",
        required=True
    )


class StartStopResultStep(graphene.Union):
    """
    A status update for the project start/stop subscriptions

    Usually StartStopProgressStep is sent, to indicate progress starting a single service.

    StartStopEndStep is sent as last update. After that the client should stop subscribing.
    """
    class Meta:
        types = (StartStopProgressStep, StartStopEndStep)
