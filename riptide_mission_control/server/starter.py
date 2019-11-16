import graphene
import logging

from riptide_mission_control import LOGGER_NAME
from riptide_mission_control.registry import registry

from tornadoql.tornadoql import TornadoQL

from riptide_mission_control.graphql_entities.query import Query
from riptide_mission_control.graphql_entities.mutation import Mutation
from riptide_mission_control.graphql_entities.subscription import Subscription

logger = logging.getLogger(LOGGER_NAME)


def run_apiserver(system_config, engine, http_port):
    """
    Run api server on the specified port.
    """

    registry().system_config = system_config
    registry().engine = engine

    schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)

    logger.info('Starting GraphQL server on %s' % http_port)
    logger.info('  GraphiQL:              http://localhost:%s/graphiql' % http_port)
    logger.info('  Queries and Mutations: http://localhost:%s/graphql' % http_port)
    logger.info('  Subscriptions:         ws://localhost:%s/subscriptions' % http_port)

    TornadoQL.start(schema, port=http_port)
