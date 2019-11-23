from typing import Union, Pattern

import tornado

import graphene
import logging

from riptide_mission_control import LOGGER_NAME
from riptide_mission_control.registry import registry

from tornadoql.tornadoql import TornadoQL, GraphQLSubscriptionHandler, GraphQLHandler, GraphiQLHandler, SETTINGS, \
    FallbackHandler

import tornado.web
import tornado.routing

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

    app_endpoints = [
        (r'/subscriptions', GraphQLSubscriptionHandler, dict(opts=SETTINGS)),
        (r'/graphql', GraphQLHandler),
        (r'/graphiql', GraphiQLHandler),
        (r'/.*', FallbackHandler)
    ]

    TornadoQL.schema = schema
    app = tornado.web.Application(app_endpoints, **SETTINGS)

    app.listen(http_port)
    tornado.ioloop.IOLoop.current().start()


def get_for_external(system_config, engine, hostname):
    """
    Return Tornado routes for use in external servers
    """

    registry().system_config = system_config
    registry().engine = engine
    
    schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)
    TornadoQL.schema = schema

    return [
        (HostnameMatcher(r'/subscriptions', hostname), GraphQLSubscriptionHandler, dict(opts=SETTINGS)),
        (HostnameMatcher(r'/graphql', hostname), GraphQLHandler),
        (HostnameMatcher(r'/graphiql', hostname), GraphiQLHandler),
        (HostnameMatcher(r'/.*', hostname), FallbackHandler)
    ]


class HostnameMatcher(tornado.routing.PathMatches):

    def __init__(self, path_pattern: Union[str, Pattern], hostname: str) -> None:
        self.hostname = hostname
        super().__init__(path_pattern)

    def match(self, request):
        """ Match path and hostname """
        if request.host_name != self.hostname:
            return None
        return super().match(request)
