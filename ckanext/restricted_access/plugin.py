import ckan.plugins as plugins
import ckanext.restricted_access.middleware as middleware


class RestrictedAccessPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IMiddleware, inherit=True)

    # IMiddleware

    def make_middleware(self, app, config):
        return middleware.RestrictAccessMiddleware(app)
