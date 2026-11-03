# Access Control: Vertical Privilege Escalation

> Lab write-up notes (PortSwigger Web Security Academy style).
> **Category:** Broken Access Control · **Topic:** Unprotected functionality, parameter-based access control, platform misconfiguration

## Overview

Vertical privilege escalation happens when a lower-privileged user (e.g. a normal user) can reach functionality reserved for a higher-privileged user (e.g. an admin). The common root cause is that the application hides or blocks the functionality in the **UI** but does not enforce the same check on the **server side**. Anything the client sends (cookies, hidden fields, headers, HTTP methods) can be modified, so it cannot be trusted for authorization decisions.

---

## 1. User role controlled by a request parameter (cookie)

### Summary
The application stores the user's privilege level in a client-controlled value (`Admin=false` in a cookie). Changing it to `true` grants access to the admin panel.

### Steps to reproduce
1. Log in as a normal user.
2. Intercept the request and observe the `Admin=false` parameter/cookie.
3. Change the value to `Admin=true`.
4. The admin panel is now accessible.
5. Locate the delete-user endpoint and send the request (e.g. `POST` with the target username).

### Learnings
- The admin panel looks restricted because every **UI action** checks whether the user is authorized, but the **backend requests** do not verify it, so they can be replayed and manipulated.
- Because the UI hid the controls, the action could not be performed from the browser, but it worked when sent directly to the backend.

### Remediation
- Never derive authorization from client-controlled data (cookies, hidden fields, query params).
- Store the role server-side (session store / database) and check it on **every** request.

---

## 2. User role can be modified in the user profile (mass assignment)

### Summary
The "update email" request returns the full user object in the response, including a `roleid` field. Sending an extra `roleid` parameter in the update request changes the user's role.

### Steps to reproduce
1. Log in as a normal user and update your email address.
2. In the response, notice additional parameters beyond the email, including `roleid`.
3. Resend the update request with the extra parameter, e.g. `{"email": "new@example.com", "roleid": 2}`.
4. The request succeeds; the account now has the admin role.
5. Access the admin panel and delete the target user.

### Learnings
- Responses often leak the data model. Any field visible in a response is worth trying in a request.
- The server blindly binds all supplied parameters to the user object (mass assignment / auto-binding).

### Remediation
- Use an allow-list of fields that may be updated by the user.
- Never bind request data directly to privileged model attributes.

---

## 3. Platform misconfiguration

Some applications enforce access control at a layer **above** the application (e.g. a front-end proxy, WAF or framework rule such as "deny `/admin` for non-admins"). This protects the front-end route but leaves the back end exposed if the underlying application accepts other ways of addressing the resource.

### 3.1 URL-based access control bypass

Some frameworks support non-standard headers such as `X-Original-URL` and `X-Rewrite-URL`, which override the URL used for routing.

**Steps to reproduce**
1. Log in as a normal user.
2. Request `/admin` directly. Result: `403` blocked.
3. Add the header `X-Original-URL: /invalid` and observe that the application reacts to `/invalid` (a "not found" response), proving the header overrides the path.
4. Set `X-Original-URL: /admin`. The admin panel loads, because the front-end rule only saw the request for `/`.
5. Read the response for the user list and delete links.
6. To delete a user: send the request with the real path/query string carrying the parameter (`?username=carlos`) and set `X-Original-URL: /admin/delete`.

### 3.2 Method-based access control bypass

Access control may be applied to specific HTTP methods only (e.g. it blocks `POST` to the upgrade endpoint but not `GET`, or vice versa).

**Steps to reproduce**
1. Log in as admin, open the admin panel and upgrade a user. Capture the `POST` request.
2. In another browser/tab, log in as a normal user and capture your session cookie.
3. Replay the admin's request with the **normal user's session cookie**. Result: `Unauthorized`.
4. Change the method to an unrecognised one (e.g. `POSTX`). Result: `Missing parameter 'username'`, which shows the access check was skipped.
5. Set the `username` to your own account, then convert the request to `GET` (right-click, "Change request method") and send it. The upgrade succeeds.

### Remediation
- Enforce authorization inside the application, on every route and every method, using deny-by-default.
- Disable or strip headers such as `X-Original-URL` and `X-Rewrite-URL` at the edge.
- Do not rely on URL/method matching in a proxy layer as the only control.

---

## Key takeaways
| Issue | Root cause | Fix |
|---|---|---|
| Role in cookie/param | Trusting client-supplied data | Server-side role lookup per request |
| `roleid` in profile update | Mass assignment | Allow-list updatable fields |
| `X-Original-URL` bypass | Platform layer only protects the front-end route | App-level checks; strip override headers |
| Method bypass | Check tied to specific HTTP methods | Method-agnostic, deny-by-default authorization |
