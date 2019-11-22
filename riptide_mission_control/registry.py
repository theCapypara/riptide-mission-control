"""Global configuration registry"""

from typing import NamedTuple, Optional

from riptide.config.document.config import Config
from riptide.engine.abstract import AbstractEngine


class Registry(NamedTuple):
    system_config: Optional[Config]
    engine: Optional[AbstractEngine]


registry: Registry = Registry(system_config=None, engine=None)


def registry() -> Registry:
    return registry
