from rx.subjects import ReplaySubject

from riptide.config.document.project import Project
from riptide.db.environments import DbEnvironments
from riptide_mission_control.graphql_entities.subscriptions.utils import async_in_executor, try_loading_project, \
    ResultStep
from riptide_mission_control.registry import registry


@async_in_executor
async def db_copy_impl(subject: ReplaySubject, project_name: str, source: str, target:str, switch: bool):
    project = try_loading_project(project_name, subject, 1, 4)
    if not project:
        return

    engine = registry().engine
    dbenv = DbEnvironments(project, engine)

    try:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Copying database environment {source} to {target}..."
        ))
        dbenv.new(target, copy_from=source)
    except FileNotFoundError:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Environment {source} not found.",
            is_end=True,
            is_error=True
        ))
    except FileExistsError:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Environment with this name already exists.",
            is_end=True,
            is_error=True
        ))
    except NameError:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Invalid name for new environment, do not use special characters.",
            is_end=True,
            is_error=True
        ))
    except Exception as ex:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Error creating environment: {ex}",
            is_end=True,
            is_error=True
       ))
    else:
        if switch:
            await db_switch_impl(subject, project, target, 1, 1)
        else:
            subject.on_next(ResultStep(
                steps=4,
                current_step=4,
                text=f"Finished creating environment: {target}.",
                is_end=True
            ))


@async_in_executor
async def db_new_impl(subject: ReplaySubject, project_name: str, new_name: str, switch: bool):
    project = try_loading_project(project_name, subject, 1, 4)
    if not project:
        return

    engine = registry().engine
    dbenv = DbEnvironments(project, engine)

    try:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Creating database environment {new_name}..."
        ))
        dbenv.new(new_name, copy_from=None)
    except FileExistsError:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Environment with this name already exists.",
            is_end=True,
            is_error=True
        ))
    except NameError:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Invalid name for new environment, do not use special characters.",
            is_end=True,
            is_error=True
        ))
    except Exception as ex:
        subject.on_next(ResultStep(
            steps=4,
            current_step=1,
            text=f"Error creating environment: {ex}",
            is_end=True,
            is_error=True
        ))
    else:
        if switch:
            await db_switch_impl(subject, project, new_name, 1, 1)
        else:
            subject.on_next(ResultStep(
                steps=4,
                current_step=4,
                text=f"Finished creating environment: {new_name}.",
                is_end=True
            ))


@async_in_executor
async def db_switch_subscriber_impl(subject: ReplaySubject, project_name: str, name: str):
    project = try_loading_project(project_name, subject, 1, 3)
    if not project:
        return

    await db_switch_impl(subject, project, name)


@async_in_executor
async def db_drop_impl(subject: ReplaySubject,  project_name: str, name: str):
    project = try_loading_project(project_name, subject, 1, 4)
    if not project:
        return

    engine = registry().engine
    dbenv = DbEnvironments(project, engine)

    try:
        subject.on_next(ResultStep(
            steps=1,
            current_step=1,
            text=f"Deleting database environment {name}..."
        ))
        dbenv.drop(name)
    except FileNotFoundError:
        subject.on_next(ResultStep(
            steps=1,
            current_step=1,
            text=f"Environment with this name does not exist.",
            is_end=True,
            is_error=True
        ))
    except OSError:
        subject.on_next(ResultStep(
            steps=1,
            current_step=1,
            text=f"Can not delete the environment that is currently active.",
            is_end=True,
            is_error=True
        ))
    except Exception as ex:
        subject.on_next(ResultStep(
            steps=1,
            current_step=1,
            text=f"Error deleting environment: {ex}",
            is_end=True,
            is_error=True
        ))
    else:
        subject.on_next(ResultStep(
            steps=1,
            current_step=1,
            text=f"Finished deleting environment: {name}.",
            is_end=True
        ))


async def db_switch_impl(
        subject: ReplaySubject,
        project: Project,
        name: str,
        total_steps_from_ctx=0,
        current_step_in_ctx=0
):
    """Switches db env. Has 3 total steps and can be used in other db operations."""
    engine = registry().engine
    dbenv = DbEnvironments(project, engine)
    db_name = dbenv.db_service["$name"]

    subject.on_next(ResultStep(
        steps=total_steps_from_ctx + 3,
        current_step=current_step_in_ctx + 1,
        text="Switching database..."
    ))

    # 1. If running, stop database
    was_running = engine.service_status(project, db_name, registry().system_config)
    if was_running:
        subject.on_next(ResultStep(
            steps=total_steps_from_ctx + 3,
            current_step=current_step_in_ctx + 1,
            text="Stopping database service..."
        ))
        async for _ in registry().engine.stop_project(project, [db_name]):
            pass

    # 2. Switch environment
    try:
        subject.on_next(ResultStep(
            steps=total_steps_from_ctx + 3,
            current_step=current_step_in_ctx + 2,
            text=f"Switching environment to {name}..."
        ))
        dbenv.switch(name)
    except FileNotFoundError:
        subject.on_next(ResultStep(
            steps=total_steps_from_ctx + 3,
            current_step=current_step_in_ctx + 2,
            text=f"Environment {name} does not exist.",
            is_end=True,
            is_error=True
        ))
    except Exception as ex:
        subject.on_next(ResultStep(
            steps=total_steps_from_ctx + 3,
            current_step=current_step_in_ctx + 2,
            text=f"Error switching environment: {str(ex)}",
            is_end=True,
            is_error=True
        ))
    else:
        # 3. If was running: start database again
        if was_running:
            subject.on_next(ResultStep(
                steps=total_steps_from_ctx + 3,
                current_step=current_step_in_ctx + 3,
                text=f"Starting database...",
            ))
            async for _ in registry().engine.start_project(project, [db_name]):
                pass

        subject.on_next(ResultStep(
            steps=total_steps_from_ctx + 3,
            current_step=current_step_in_ctx + 3,
            text=f"Finished switching database environment to {name}.",
            is_end=True
        ))
