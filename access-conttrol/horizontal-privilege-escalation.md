# Access Control: Horizontal Privilege Escalation (IDOR)

> Lab write-up notes (PortSwigger Web Security Academy style).
> **Category:** Broken Access Control · **Topic:** User ID controlled by request parameter / Insecure Direct Object References (IDOR)

## Overview

Horizontal privilege escalation occurs when a user can access resources belonging to **another user of the same privilege level**. In IDOR vulnerabilities, a user-controlled value (such as `id=wiener`) is used to look up an object directly, and the server never checks that the object actually belongs to the requester.

---

## Lab 5: User ID controlled by request parameter

### Walkthrough
1. Log in with the supplied credentials. The login request carries a CSRF token that was issued *before* login.
2. After login, the "My account" page shows an API key. The endpoint is `/my-account?id=wiener`.
3. Initially I overlooked that the URL contained `id=<username>` and considered generating a CSRF token for the victim to compromise the account.
4. The actual vulnerability is simpler: change `id=wiener` to the victim's username (`id=carlos`) and the victim's account page, including the API key, is returned.

### Learnings
- Always check URLs and request bodies for identifiers (`id`, `user`, `account`, `uid`). A CSRF token does not prevent IDOR; they are separate controls.

---

## Lab 6: User ID controlled by request parameter, with unpredictable user IDs

Applications sometimes use **GUIDs** (random unique IDs) instead of incremental numbers to stop attackers guessing or predicting other users' IDs.

This is only obscurity, not access control. GUIDs often leak elsewhere in the application, for example:
- in blog posts or comments (author links)
- in messages
- in profile URLs

**Approach:** find a post by the target user, grab their GUID from the author link, and use it as the `id` parameter.

---

## Lab 7: User ID controlled by request parameter, with data leakage in redirect

### Behaviour
The application detects that the user is not permitted to view the resource and responds with a **redirect** (`302`) to the login/home page. However, the redirect response **still contains the sensitive data in its body**.

### Steps to reproduce
1. Log in with the supplied credentials and open your account page.
2. Send the request to Burp Repeater.
3. Change the `id` parameter to `carlos`.
4. Observe that the response redirects to the home page, but the body contains Carlos's API key.
5. Submit the API key.

### Why a 302 with a body?
The server builds the full response (including the victim's page) *before* performing the authorization check, then adds a `Location` header to redirect. Browsers follow the `Location` header and never render the body, so it looks safe in the UI. Proxies like Burp, `curl` and scripts still see the body.

### How to secure it
- Perform the authorization check **before** loading or rendering the data.
- On failure, return a response with no sensitive content (a minimal `302`/`403`).
- Verify object ownership server-side: compare the requested object's owner with the authenticated session user.

---

## Lab 8: User ID controlled by request parameter, with password disclosure

### Steps to reproduce
1. Log in with the supplied credentials and open the account page.
2. Change `id` in the URL to `administrator`: `GET /my-account?id=administrator`.
3. In Burp, view the response and observe that it contains the administrator's password pre-filled in the change-password form:
   ```html
   <input required type="hidden" name="csrf" value="<administrator's csrf token>">
   <input required type="password" name="password" value="<REDACTED>"/>
   ```
4. Log in as `administrator` with the disclosed password and delete the target user (`carlos`).

### Why did the CSRF token not work? (`400 Bad Request: Invalid CSRF token (session does not contain a CSRF token)`)
My first idea was to reuse the CSRF token from that response to change the administrator's password from my own session. That fails because **CSRF tokens are bound to the session** they were issued for. The token in the response belongs to the *administrator's* server-side session, but my request carries *my* session cookie. The server looks up my session, finds no matching token, and rejects the request. In other words, CSRF protection worked as designed.

It didn't matter, because the password was already disclosed in the body, so there was no need to change it. Just log in.

### Vulnerabilities in this lab
1. **IDOR**: no check that `id` matches the logged-in user.
2. **Sensitive data exposure**: the password is rendered into the HTML (should never be sent back to the client, not even to the owner).

### Remediation
- Enforce object-level authorization on every request.
- Derive the user from the session, not from a request parameter.
- Never echo stored passwords; password forms should be blank. Store passwords only as salted hashes.

---

## Key takeaways
| Lab | Weakness | Fix |
|---|---|---|
| 5 | `id` parameter trusted as-is | Ownership check against session user |
| 6 | Unpredictable IDs treated as security | Authorization, not obscurity; avoid leaking GUIDs |
| 7 | Sensitive body returned in redirect | Check before rendering; no data in redirects |
| 8 | IDOR plus password in response | Ownership check; never return passwords |
