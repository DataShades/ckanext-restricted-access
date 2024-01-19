from __future__ import annotations

import re
import logging

from flask import jsonify, Response

import ckan.authz as authz
import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.restricted_access.config as conf
import ckanext.restricted_access.const as const


log = logging.getLogger(__name__)
ERROR_CODE = conf.get_restricted_paths_error_code()
ERROR_MESSAGE = conf.get_restricted_paths_error_message()


def before_request():
    if tk.request.endpoint in const.NON_RESTRICTABLE_ENDPOINTS:
        return

    if (
        conf.get_redirect_anon_to_login()
        and not tk.current_user.is_authenticated
        and tk.request.endpoint != const.LOGIN_ENDPOINT
    ):
        return tk.redirect_to(const.LOGIN_ENDPOINT)

    if not check_access_by_api_action():
        return invalid_request(), 400

    if not check_access_by_path():
        return tk.abort(
            ERROR_CODE,
            ERROR_MESSAGE or tk._(const.NOT_FOUND_MESSAGE)
            if ERROR_CODE == 404 else ERROR_MESSAGE
        )


def invalid_request() -> Response:
    """Return a response data for an invalid API request"""
    return jsonify({"success": False, "error": {"message": "Invalid request"}})


def check_access_by_path() -> bool:
    """Check a request path against a list of restricted paths regexs

    Returns:
        bool: False if access is restricted, otherwise True
    """

    user: model.User | model.AnonymousUser = tk.current_user

    for path_regex in conf.get_restricted_paths():
        if not re.match(path_regex, tk.request.path):
            continue

        if not user.is_authenticated or not authz.is_sysadmin(tk.g.user):
            log.info(
                f"An attempt to access a restricted path '{tk.request.path}'. "
                f"User: {tk.g.user or 'anonymous'}"
            )
            return False

    return True


def check_access_by_api_action() -> bool:
    """Check an api_action against a list of restricted API actions

    Returns:
        bool: False if access is restricted, otherwise True
    """
    args: dict[str, str] = tk.request.view_args or {}
    request_action: str | None = args.get("api_action") or args.get("logic_function")

    if not request_action:
        return True

    restricted: bool = False

    for api_action in conf.get_restricted_api_actions():
        restricted: bool = (
            request_action.startswith(api_action.rstrip("*"))
            if api_action.endswith("*")
            else api_action == request_action
        )

        if restricted and not authz.is_sysadmin(tk.g.user):
            log.info(
                f"An attempt to access a restricted endpoint '{request_action}'. "
                f"User: {tk.g.user or 'anonymous'}"
            )
            return False

    return True
