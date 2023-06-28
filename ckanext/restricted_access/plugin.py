import ckan.plugins as plugins
from ckanext.restricted_access.middleware import before_request


class RestrictedAccessPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IMiddleware, inherit=True)

    # IMiddleware

    def make_middleware(self, app, config):
        app.before_request(before_request)

        return app
