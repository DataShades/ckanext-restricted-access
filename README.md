# ckanext-restricted-access

Extension for restricting access to CKAN (API) actions.

Adds a middleware layer to intercept requests and check them against a list of restricted actions.

The benefit of implementing it this way rather than say using chained action or auth functions is that you don't have to create an override for every action or auth that you want to restrict.

__Note:__ this extension currently only restricts actions to sysadmin level users.

## Example

We have two CKAN instances: one private, the other public.

The public instance harvests from the private instance daily.

The harvest source configuration on the public instance contains the API key of a user on the private instance.

The `harvest_source_list` API action in `ckanext-harvest` exposes the full configuration of the harvest source, including the API key.

This is a security risk for us - therefore we want to restrict the `harvest_source_list` API action to `sysadmin` authenticated users.

## Configuration

Add the `restricted_access` plugin to your CKAN `.ini` file, e.g.

    ckan.plugins = ... restricted_access ...

### Config options
There are few config options you could use to manage the restrictions of paths and endpoints:
```
# A list of API endpoints to restrict. Use * to restrict all endpoints that starts from X
# (optional, default: None)
ckan.restricted.api_actions = harvest_* user_autocomplete status_show

# A list of paths to restrict. Use a regular expression here, to manage more complex rules
# (optional, default: None)
ckan.restricted.ui_paths = ^/user/default$ (?!.*login)/user/*

# An error code for the restricted paths. It also impacts on the error message content in case of trying to request the restricted path.
# (optional, default: 404)
ckan.restricted.ui_paths.error_code = 403

# Redirect anonymous users to login page
# (optional, default: false)
ckan.restricted.redirect_anon_to_login = true
```
Only sysadmins could visit the restricted endpoints.
You could provide `api_token` of a sysadmin and get an access.
