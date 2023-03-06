from typing import Optional
import ckan.authz as authz
import ckan.plugins.toolkit as tk
import json
from flask import jsonify
import logging


from ckan.common import _, config

log = logging.getLogger(__name__)

def get_api_action() -> Optional[str]:
    """Return the name of executed API action on api.action endpoint.
    """
    if tk.get_endpoint() == ("api", "action"):
        args = tk.request.view_args
        if args:
            return args["logic_function"]


def check_access_ui_path(username, ui_path):
    '''
    Check a UI path (URI) against a list of restricted paths set in the CKAN `.ini` file
    :param username:
    :param ui_path:
    :return:
    '''
    # @TODO: Improve this to handle wildcards such as /user/salsa (without restricting /user/XYZ/edit when required)
    restricted_ui_paths = config.get('ckan.restricted.ui_paths', []).split()
    if ui_path in restricted_ui_paths:
        if not username or not authz.is_sysadmin(username):
            return False
    return True


def check_access_api_action(api_user, api_action):
    '''
    Check an api_action against a list of restricted API actions
    :param api_user:
    :param api_action:
    :return: False if api_action is restricted and no user, or user not sysadmin, else True
    '''
    # @TODO: Improve this to handle wildcards such as `harvest_source*`
    restricted_api_actions = config.get('ckan.restricted.api_actions', [])
    if api_action in restricted_api_actions:
        if not api_user or not authz.is_sysadmin(api_user.name):
            return False
    return True


class AuthMiddleware(object):
    @classmethod
    def init_app(cls, app):
        app.before_request(cls.before_request)

    @classmethod
    def before_request(cls):
        api_action = get_api_action()

        username = tk.current_user.name
        ui_path = tk.request.path


        if not api_action:
            # Dealing with UI requests
            if not check_access_ui_path(username, ui_path):
                return tk.abort(403, f'<h1>Access Forbidden</h1> Path: {ui_path}')

        else:
            # Dealing with API requests
            # if the request is an api action, check against restricted actions
            if not check_access_api_action(username, api_action):
                return jsonify(unauthorised_api_response())


def unauthorised_api_response():
    '''
    Simple helper function to return a JSON response message
    :return: JSON response
    '''
    response_msg = {
        'success': False,
        'error': {
            'message': 'Invalid request'
        }
    }
    return json.dumps(response_msg)
