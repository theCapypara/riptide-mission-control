from rx.subjects import ReplaySubject

from riptide.config import repositories
from riptide.config.document.config import Config
from riptide.config.files import riptide_main_config_file
from riptide_mission_control.graphql_entities.subscriptions.utils import async_in_executor, try_loading_project, \
    ResultStep
from riptide_mission_control.registry import registry


@async_in_executor
async def update_repositories_impl(subject: ReplaySubject):
    subject.on_next(ResultStep(
        steps=2,
        current_step=1,
        text="Starting repository update..."
    ))
    try:
        repositories.update(registry().system_config, lambda msg: subject.on_next(ResultStep(
            steps=2,
            current_step=1,
            text=msg
        )))
    except Exception as e:
        subject.on_next(ResultStep(
            steps=2,
            current_step=1,
            text="Fatal error during repository update: " + str(e),
            is_end=True,
            is_error=True
        ))
        subject.on_completed()
        return
    subject.on_next(ResultStep(
        steps=2,
        current_step=2,
        text="Reloading configuration..."
    ))

    # Reload system config
    try:
        config_path = riptide_main_config_file()
        system_config = Config.from_yaml(config_path)
        system_config.validate()
        registry.system_config = system_config
    except FileNotFoundError as e:
        subject.on_next(ResultStep(
            steps=2,
            current_step=2,
            text="Main config file not found! Could not reload system config.",
            is_end=True,
            is_error=True
        ))
    except Exception as e:
        subject.on_next(ResultStep(
            steps=2,
            current_step=2,
            text="Could not reload system config: " + str(e),
            is_end=True,
            is_error=True
        ))
    else:
        subject.on_next(ResultStep(
            steps=2,
            current_step=2,
            text="Repository update done!",
            is_end=True
        ))
    finally:
        subject.on_completed()


@async_in_executor
async def update_images_impl(subject: ReplaySubject, project_name: str):
    subject.on_next(ResultStep(
        steps=1,
        current_step=1,
        text="Starting image update..."
    ))

    project = try_loading_project(project_name, subject, 1, 1)
    if not project:
        return

    try:
        registry().engine.pull_images(project,
                                      line_reset="",
                                      update_func=lambda msg: subject.on_next(
                                          ResultStep(
                                            steps=1,
                                            current_step=1,
                                            text=msg
                                          )
                                      ))
        subject.on_next(ResultStep(
            steps=1,
            current_step=1,
            text="Done updating images!",
            is_end=True
        ))
    except Exception as ex:
        subject.on_next(ResultStep(
            steps=1,
            current_step=1,
            text="Error updating an image: " + str(ex),
            is_end=True,
            is_error=True
        ))
    finally:
        subject.on_completed()
    pass