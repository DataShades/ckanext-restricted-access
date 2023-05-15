from __future__ import annotations

import json
from typing import Any, Optional

from factory.base import FactoryMetaClass
import pytest

from ckan.tests.helpers import CKANTestApp as App, CKANResponse as Response, call_action

from ckanext.restricted_access.middleware import invalid_request
from ckanext.restricted_access.config import (
    CONFIG_REDIRECT_ANON_TO_LOGIN,
    CONFIG_RESTRICTED_ACTIONS,
    CONFIG_RESTRICTED_PATHS,
)


@pytest.fixture()
def restricted_user(user_factory):
    yield user_factory(name="default")


class _App:
    """Custom app with a modified get method"""

    def __init__(self, app: App):
        self.app = app

    def get(
        self,
        url: str,
        json: Optional[dict[str, Any]] = None,
        user: Optional[str] = None,
        token: Optional[dict[str, bytes]] = None,
    ) -> Response:
        payload: dict[str, Any] = {
            "url": url,
            "json": json or {},
            "follow_redirects": False,
        }

        if user:
            payload["extra_environ"] = {"REMOTE_USER": user}
        elif token:
            payload["extra_environ"] = {"Authorization": token["token"].decode()}

        return self.app.get(**payload)  # type: ignore


@pytest.fixture()
def _app(app):
    yield _App(app)


@pytest.mark.usefixtures("with_plugins", "with_request_context", "clean_db")
class TestMiddlewareRestrictPath:
    @pytest.mark.ckan_config(CONFIG_RESTRICTED_PATHS, "^/user/default$")
    def test_as_sysadmin(
        self, _app: _App, sysadmin: dict[str, Any], restricted_user: dict[str, Any]
    ):
        resp: Response = _app.get(
            f"/user/{restricted_user['name']}", user=sysadmin["name"]
        )

        assert restricted_user["about"] in resp.body
        assert resp.status_code == 200

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_PATHS, "^/user/default$")
    def test_as_regular_user(
        self,
        _app: _App,
        restricted_user: dict[str, Any],
        user_factory: FactoryMetaClass,
    ):
        requester = user_factory()
        resp: Response = _app.get(f"/user/{restricted_user['name']}", requester["name"])

        assert restricted_user["about"] not in resp.body
        assert "404 Not Found" in resp.body
        assert resp.status_code == 404

        accessible_user = user_factory()
        resp: Response = _app.get(f"/user/{accessible_user['name']}", requester["name"])
        assert accessible_user["about"] in resp.body
        assert resp.status_code == 200

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_PATHS, "^/user/default$")
    def test_as_anonymous(
        self,
        _app: _App,
        restricted_user: dict[str, Any],
        user_factory: FactoryMetaClass,
    ):
        resp: Response = _app.get(f"/user/{restricted_user['name']}")
        assert restricted_user["about"] not in resp.body
        assert "404 Not Found" in resp.body
        assert resp.status_code == 404

        accessible_user = user_factory(name="test_user")
        resp: Response = _app.get(f"/user/{accessible_user['name']}")
        assert accessible_user["about"] in resp.body
        assert resp.status_code == 200

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_PATHS, "^/user/default$")
    def test_with_sysadmin_token(
        self, _app: _App, sysadmin: dict[str, Any], restricted_user: dict[str, Any]
    ):
        token_data = call_action("api_token_create", user=sysadmin["name"], name="test")

        resp: Response = _app.get(f"/user/{restricted_user['name']}", token=token_data)

        assert restricted_user["about"] in resp.body
        assert resp.status_code == 200

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_PATHS, "^/user/default$")
    def test_with_regular_user_token(
        self, _app: _App, user: dict[str, Any], restricted_user: dict[str, Any]
    ):
        token_data = call_action("api_token_create", user=user["name"], name="test")

        resp: Response = _app.get(f"/user/{restricted_user['name']}", token=token_data)

        assert restricted_user["about"] not in resp.body
        assert "404 Not Found" in resp.body
        assert resp.status_code == 404

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_PATHS, "(?!.*login)^/user/*")
    def test_regex_cases(self, _app: _App):
        assert _app.get("/user/login").status_code == 200
        assert _app.get("/user/reset").status_code == 404


@pytest.mark.usefixtures("with_plugins", "with_request_context", "clean_db")
class TestMiddlewareRestrictApiEndpoints:
    @pytest.mark.ckan_config(CONFIG_RESTRICTED_ACTIONS, "status_show")
    def test_as_sysadmin(self, _app: _App, sysadmin: dict[str, Any]):
        resp: Response = _app.get("/api/action/status_show", user=sysadmin["name"])
        result: dict[str, Any] = json.loads(resp.body)

        assert resp.status_code == 200
        assert result["result"]
        assert result["success"]

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_ACTIONS, "status_show")
    def test_with_sysadmin_token(self, _app: _App, sysadmin: dict[str, Any]):
        token_data = call_action("api_token_create", user=sysadmin["name"], name="test")

        resp: Response = _app.get("/api/action/status_show", token=token_data)

        result: dict[str, Any] = json.loads(resp.body)

        assert result["result"]["ckan_version"]
        assert result["success"]

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_ACTIONS, "status_show")
    def test_regular_user(self, _app: _App, user: dict[str, Any]):
        resp: Response = _app.get("/api/action/status_show", user=user["name"])
        assert resp.status_code == 400
        assert resp.data == invalid_request().data

        resp: Response = _app.get("/api/action/package_search", user=user["name"])
        result: dict[str, Any] = json.loads(resp.body)

        assert resp.status_code == 200
        assert result["result"]
        assert result["success"]

    @pytest.mark.ckan_config(CONFIG_RESTRICTED_ACTIONS, "status_show")
    def test_anonymous(self, _app: _App):
        resp: Response = _app.get("/api/action/status_show")
        assert resp.status_code == 400
        assert resp.data == invalid_request().data

        resp: Response = _app.get("/api/action/package_search")
        result: dict[str, Any] = json.loads(resp.body)

        assert resp.status_code == 200
        assert result["result"]
        assert result["success"]

    @pytest.mark.ckan_config(
        CONFIG_RESTRICTED_ACTIONS, "package_* vocabulary_list resource_*"
    )
    def test_with_wildcard_anon(self, _app: _App):
        api_actions = (
            "package_search",
            "package_show",
            "vocabulary_list" "resource_show",
            "resource_view_show",
        )

        for api_action in api_actions:
            resp: Response = _app.get(f"/api/action/{api_action}")
            assert resp.status_code == 400

        resp: Response = _app.get("/api/action/group_list")
        assert resp.status_code == 200

    @pytest.mark.ckan_config(
        CONFIG_RESTRICTED_ACTIONS, "package_* vocabulary_list user_*"
    )
    def test_with_wildcard_sysadmin(self, _app: _App, sysadmin: dict[str, Any]):
        api_actions = ("package_search", "vocabulary_list", "user_list")

        for api_action in api_actions:
            resp: Response = _app.get(
                f"/api/action/{api_action}", user=sysadmin["name"]
            )
            assert resp.status_code == 200


@pytest.mark.usefixtures("with_plugins", "with_request_context", "clean_db")
class TestMiddlewareRedirectAnon:
    @pytest.mark.ckan_config(CONFIG_REDIRECT_ANON_TO_LOGIN, "false")
    def test_anonymous(self, _app: _App):
        resp: Response = _app.get("/dataset")

        assert resp.status_code == 200
        assert not resp.location

    @pytest.mark.ckan_config(CONFIG_REDIRECT_ANON_TO_LOGIN, "true")
    def test_anonymous_redirect(self, _app: _App):
        resp: Response = _app.get("/dataset")

        assert resp.status_code == 302
        assert "user/login" in resp.location  # type: ignore

    @pytest.mark.ckan_config(CONFIG_REDIRECT_ANON_TO_LOGIN, "true")
    def test_regular_user(self, _app: _App, user: dict[str, Any]):
        resp: Response = _app.get("/dataset", user=user["name"])

        assert resp.status_code == 200
        assert not resp.location

    @pytest.mark.ckan_config(CONFIG_REDIRECT_ANON_TO_LOGIN, "true")
    def test_regular_user_by_api_token(self, _app: _App, user: dict[str, Any]):
        token_data = call_action("api_token_create", user=user["name"], name="test")
        resp: Response = _app.get("/dataset", token=token_data)

        assert resp.status_code == 200
        assert not resp.location
