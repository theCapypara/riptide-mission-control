import time

from graphql import GraphQLError
from typing import Dict

from riptide.config.document.project import Project
from riptide.config.loader import load_config_by_project_name, load_projects, load_config
from riptide_mission_control import PROJECT_CACHE_TIMEOUT
from riptide_mission_control.graphql_entities.document.project import ProjectGraphqlDocument


class LoadedProjects:
    projects: Dict[str, Project] = {}
    time_last_loaded: Dict[str, float] = {}


_loaded_projects = LoadedProjects()
_project_files_list: Dict[str, str] = None
_project_files_last_loaded: int = 0


def flush_caches():
    global _project_files_list, _project_files_last_loaded, _loaded_projects
    _project_files_list = None
    _project_files_last_loaded = 0
    _loaded_projects = LoadedProjects()


def load_single_project(name: str):
    current_time = time.time()
    if name not in _loaded_projects.projects \
            or current_time - _loaded_projects.time_last_loaded[name] > PROJECT_CACHE_TIMEOUT:
        try:
            _loaded_projects.time_last_loaded[name] = current_time
            _loaded_projects.projects[name] = load_config_by_project_name(name)["project"]
        except Exception as ex:
            raise GraphQLError(f"Could not load project {name}. {ex}")

    return ProjectGraphqlDocument(_loaded_projects.projects[name])


def get_project_list() -> Dict[str, str]:
    global _project_files_list
    current_time = time.time()

    if current_time - _project_files_last_loaded > PROJECT_CACHE_TIMEOUT:
        _project_files_list = load_projects()
    return _project_files_list


def load_all_projects():
    project_files = get_project_list()
    current_time = time.time()

    projects = []
    errors = []
    for project_name, project_file in project_files.items():

        if project_name not in _loaded_projects.projects \
                or current_time - _loaded_projects.time_last_loaded[project_name] > PROJECT_CACHE_TIMEOUT:

            try:
                project_load_result = load_config(project_file)
                if "project" not in project_load_result:
                    errors.append({
                        "name": project_name,
                        "path": project_file,
                        "error": f"Could not load project {project_name} from {project_file}. "
                                 f"Unknown error. File missing?"
                    })
                    continue
                _loaded_projects.time_last_loaded[project_name] = current_time
                _loaded_projects.projects[project_name] = project_load_result["project"]
            except Exception as ex:
                errors.append({
                    "name": project_name,
                    "path": project_file,
                    "error": f"Could not load project {project_name} from {project_file}. {ex}"
                })

        if project_name in _loaded_projects.projects:
            projects.append(ProjectGraphqlDocument(_loaded_projects.projects[project_name]))

    return {"projects": projects, "errors": errors}
