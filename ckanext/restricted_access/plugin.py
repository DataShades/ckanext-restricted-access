import ckan.plugins as plugins
import ckanext.restricted_access.middleware as middleware


class RestrictedAccessPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IMiddleware, inherit=True)

    def make_middleware(self, app, config):
        middleware.AuthMiddleware.init_app(app)
        return app
