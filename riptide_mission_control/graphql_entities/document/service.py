import graphene
from typing import Union

from riptide.config.document.service import Service as ServiceDoc, get_logging_path_for
from riptide.config.service.ports import get_existing_port_mapping
from riptide_mission_control.graphql_entities.document.converter import create_graphl_document
from riptide_mission_control import PROJECT_CACHE_TIMEOUT
from riptide_mission_control.registry import registry

ServiceConfigurationGraphqlDocument = create_graphl_document(ServiceDoc, "ServiceConfiguration", ServiceDoc.__doc__)


class ServiceBoundLogFile(graphene.ObjectType):
    type = graphene.Field(graphene.String,
                          description="Type of log file. Depends on where it was specified in the configuration. "
                                      "Can be 'stdout', 'stderr', 'path' or 'command'",
                          required=True)
    key = graphene.Field(graphene.String, description="Key of file, as specified in the configuration of the service. "
                                                      "Not set for stdout and stderr.")
    path = graphene.Field(graphene.String,
                          description="Path to the log file on the host system",
                          required=True)


class ServiceBoundAdditionalPort(graphene.ObjectType):
    key = graphene.Field(graphene.String,
                         description="Key of port, as specified in the configuration of the service.",
                         required=True)
    title = graphene.Field(graphene.String,
                           description="Human readable title, as specified in the configuration of the service.",
                           required=True)
    container = graphene.Field(graphene.Int,
                               description="Port number inside the container, "
                                           "as specified in the configuration of the service.",
                               required=True)
    host_start = graphene.Field(graphene.Int,
                                description="First port number on host that Riptide will try to reserve, on host, "
                                            "as specified in the configuration of the service.",
                                required=True)
    host_bound = graphene.Field(graphene.Int,
                                description="Actual bound port number on host. "
                                            "Is null if the service was never started before.",
                                required=False)


# noinspection PyMethodMayBeStatic,PyMethodParameters
class ServiceGraphqlDocument(graphene.ObjectType):
    """
    A service object. Represents the definition and specification for a running service container.
    """
    class Meta:
        name = "Service"

    config = graphene.Field(
        ServiceConfigurationGraphqlDocument,
        required=True, description=f"Processed configuration as loaded from YAML files. "
                                   f"This may be cached for {PROJECT_CACHE_TIMEOUT}s. "
                                   f"See mutation flush_cache to clear."
    )

    www = graphene.Field(
        graphene.String,
        required=False, description="Address to reach the service at, if applicable."
    )

    running = graphene.Field(
        graphene.Boolean,
        required=True, description="Whether or not the container for this service is currently running."
    )

    additional_ports = graphene.List(
        ServiceBoundAdditionalPort,
        required=True, description="List of bound additional ports for this service."
    )

    log_files = graphene.List(
        ServiceBoundLogFile,
        required=True, description="List of paths to log files for this service"
    )

    container_name = graphene.Field(
        graphene.String,
        required=False, description="Identifier that can be used to interact with the container for this service. "
                                    "The format of this identifier depends on the engine being used."
    )

    def resolve_config(parent, info):
        return ServiceConfigurationGraphqlDocument(_get_service_doc(parent))

    def resolve_www(parent, info):
        return "https://" + _get_service_doc(parent).domain()

    def resolve_running(parent, info):
        service: ServiceDoc = _get_service_doc(parent)
        return registry().engine.service_status(service.parent().parent(), service["$name"], registry().system_config)

    def resolve_additional_ports(parent, info):
        service: ServiceDoc = _get_service_doc(parent)
        project = service.parent().parent()
        # Collect Additional Ports
        additional_ports = []
        if "additional_ports" in service:
            for key, entry in service["additional_ports"].items():
                port_host = get_existing_port_mapping(project, service, entry["host_start"])
                additional_ports.append({
                    "key": key,
                    "title": entry["title"],
                    "container": entry["container"],
                    "host_start": entry["host_start"],
                    "host_bound": port_host
                })
        return additional_ports

    def resolve_log_files(parent, info):
        log_files =[]
        service: ServiceDoc = _get_service_doc(parent)

        if "logging" in service:
            if "stdout" in service["logging"] and service["logging"]["stdout"]:
                log_files.append({
                    "type": "stdout",
                    "path": get_logging_path_for(service, 'stdout'),
                    "key": None
                })
            if "stderr" in service["logging"] and service["logging"]["stderr"]:
                log_files.append({
                    "type": "stderr",
                    "path": get_logging_path_for(service, 'stderr'),
                    "key": None
                })
            if "paths" in service["logging"]:
                for name, path in service["logging"]["paths"].items():
                    log_files.append({
                        "type": "path",
                        "path": get_logging_path_for(service, name),
                        "key": name
                    })
            if "commands" in service["logging"]:
                for name in service["logging"]["commands"].keys():
                    log_files.append({
                        "type": "command",
                        "path": get_logging_path_for(service, name),
                        "key": name
                    })
        return log_files

    def resolve_container_name(parent, info):
        service: ServiceDoc = _get_service_doc(parent)
        return registry().engine.container_name_for(service.parent().parent(), service["$name"])


def _get_service_doc(inp: Union[ServiceGraphqlDocument, ServiceDoc]) -> ServiceDoc:
    if isinstance(inp, ServiceGraphqlDocument):
        return inp.config
    elif isinstance(inp, ServiceDoc):
        return inp
