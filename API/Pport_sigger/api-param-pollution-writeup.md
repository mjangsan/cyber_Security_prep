# Lab Write-up: API Testing — Server-Side Parameter Pollution in a REST URL

## Background: Server-Side Parameter Pollution (API Testing)

This is part of API testing: the application takes a client-supplied parameter (`username`) and uses it, unescaped, to build the path of an internal REST API call. Because the value isn't encoded before being inserted into the URL path, special characters like `#`, `?`, or `../` let an attacker change the structure of that internal API request — truncating it, appending a new path segment, or traversing to a different endpoint than the one intended.

## Study the Behavior

1. In Burp's browser, trigger a password reset for the `administrator` user.
2. In **Proxy > HTTP history**, notice the `POST /forgot-password` request and the related `/static/js/forgotPassword.js` JavaScript file.
3. Right-click the `POST /forgot-password` request and select **Send to Repeater**.
4. In the **Repeater** tab, resend the request to confirm that the response is consistent.
5. Send a variety of requests with a modified `username` parameter value to determine whether the input is placed in the URL path of a server-side request without escaping:

   1. Submit URL-encoded `administrator#` as the value of the `username` parameter.

      Notice that this returns an `Invalid route` error message. This suggests that the server may have placed the input in the path of a server-side request, and that the fragment (`#`) has truncated some trailing data. Observe that the message also refers to an API definition.

   2. Change the value of the `username` parameter from `administrator%23` to URL-encoded `administrator?`, then send the request.

      Notice that this also returns an `Invalid route` error message. This suggests that the input may be placed in a URL path, as the `?` character indicates the start of the query string and therefore truncates the URL path.

   3. Change the value of the `username` parameter from `administrator%3F` to `./administrator`, then send the request.

      Notice that this returns the original response. This suggests that the request may have accessed the same URL path as the original request. This further indicates that the input may be placed in the URL path.

   4. Change the value of the `username` parameter from `./administrator` to `../administrator`, then send the request.

      Notice that this returns an `Invalid route` error message. This suggests that the request may have accessed an invalid URL path.

## Observations So Far

- The `username` parameter is being concatenated into a server-side URL path without encoding.
- `#` and `?` truncate the path at different points (fragment vs. query string), confirming the input lands in the path segment of a URL used for a backend request.
- `./` is harmless (same directory), while `../` breaks the route — consistent with path traversal behavior, suggesting the backend request targets a path like `.../administrator` relative to some base.
- The error referencing an "API definition" hints that the backend makes a request to an internal REST API using the username as part of the path, which may be exploitable via path traversal to reach other internal endpoints (e.g., an API docs/definition endpoint, or another user's/admin's reset-token endpoint).

## Next Steps (to continue)

- Use `../` traversal to try to reach other internal paths (e.g., an internal API spec/definition endpoint revealed by the error, or a path that discloses the admin's reset token).
- Once the right internal endpoint is found, extract the administrator's password reset token and use it to reset the administrator's password and log in.

*This write-up will be updated with the remaining steps once the lab is completed.*
