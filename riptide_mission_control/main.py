import os
import click
import logging
import pkg_resources
from click import ClickException, echo

from riptide.config.document.config import Config
from riptide.config.files import riptide_main_config_file
from riptide.engine.loader import load_engine
from riptide.util import get_riptide_version_raw
from riptide_mission_control import LOGGER_NAME, PORT
from riptide_mission_control.privileges import drop_privileges

# Configure logger
logging.basicConfig()
logger = logging.getLogger(LOGGER_NAME)


def print_version():
    echo(f"riptide_lib: {get_riptide_version_raw()}")
    echo(f"riptide_mission_control: {pkg_resources.get_distribution('riptide_mission_control').version}")


@click.command()
@click.option('--user', '-u', default=os.environ.get('SUDO_USER'),
              help='Only on POSIX systems when running as root: '
                   'Specify user configuration to use. Ignored otherwise. '
                   'Defaults to environment variable SUDO_USER')
@click.option('--version', is_flag=True,
              help="Print version and exit.")
@click.option('--loglevel', '-l', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL']),
              default='INFO',
              help="Log level. Default: INFO")
@click.option('--port', '-p', default=PORT,
              help="Port, default: 8484")
def main(user, loglevel, port, version=False):
    """
    GraphQL API server for Riptide Projects.

    See the documentation at https://riptide-docs.readthedocs.io/
    """

    logger.setLevel(logging.getLevelName(loglevel))
    from riptide_mission_control.server.starter import run_apiserver

    # Version flag
    if version:
        print_version()
        exit()

    # Set privileges and drop back to user level
    try:
        if os.getuid() == 0:
            if not user:
                raise ClickException("--user parameter required when running as root.")
            logger.info(f"Was running as root. Changing user to {user}.")
            drop_privileges(user)
    except AttributeError:
        # Windows. Ignore.
        pass

    # Read system config
    try:
        config_path = riptide_main_config_file()
        system_config = Config.from_yaml(config_path)
        system_config.validate()
    except FileNotFoundError as e:
        raise ClickException("Main config file not found. Run riptide config-edit-user.") from e
    except Exception as e:
        raise ClickException("Error reading configuration.") from e

    # Read engine
    try:
        engine = load_engine(system_config["engine"])
    except NotImplementedError as ex:
        raise ClickException('Unknown engine specified in configuration.') from ex

    # Run API server
    run_apiserver(
        system_config,
        engine,
        port
    )
