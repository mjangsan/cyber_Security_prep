# Blind SQL Injection

> Lab write-up notes (PortSwigger Web Security Academy style).
> **Category:** SQL Injection · **Topic:** Blind SQLi — conditional responses, boolean inference, time delays, out-of-band (OAST)

## Overview

Blind SQL injection occurs when an application is vulnerable to SQL injection, but its responses do not contain the results of the query or any database error messages. This makes it harder to find and exploit than regular (visible) SQLi, but it is still exploitable.

Before trying payloads, it helps to identify the back-end database type, since that decides the syntax to use (string concatenation, comment style, time-delay functions, etc.).

There are three main techniques for exploiting blind SQLi:
1. **Boolean-based inference** — change the query's logical condition (`AND '1'='1'` vs `AND '1'='2'`) and watch for a difference in the response (e.g. a "Welcome back" message appearing or disappearing).
2. **Time-based (delay) inference** — trigger a conditional time delay (e.g. `IF(condition, SLEEP(5), 0)`) and measure the response time when there is no visible difference in content.
3. **Out-of-band (OAST)** — if neither of the above produces an observable difference, trigger a DNS/HTTP interaction to an external listener (e.g. Burp Collaborator) to confirm and extract data.

---

## Lab: Blind SQL injection with conditional responses

### Setup
The application sets a `TrackingId` cookie (used for session tracking / analytics) on the very first request. The value is inserted into a SQL query server-side. There is no visible error message and no query output reflected in the response — only a behavioural difference: a **"Welcome back"** message appears on the page when a particular condition is true.

### Steps to reproduce

1. Visit the shop's front page. Intercept the request in Burp Suite and note the `TrackingId` cookie (e.g. `TrackingId=xyz`).

2. Modify the cookie to test if the application is injectable:
   ```
   TrackingId=xyz' AND '1'='1
   ```
   The "Welcome back" message appears → the condition is true and the query executed.

3. Change it to a false condition:
   ```
   TrackingId=xyz' AND '1'='2
   ```
   The "Welcome back" message disappears → confirms the response changes based on the injected condition. This is the oracle used for every subsequent step.

4. Confirm the `users` table exists:
   ```
   TrackingId=xyz' AND (SELECT 'a' FROM users LIMIT 1)='a
   ```
   True → the table exists.

5. Confirm a user called `administrator` exists:
   ```
   TrackingId=xyz' AND (SELECT 'a' FROM users WHERE username='administrator')='a
   ```
   True → the user exists.

6. Determine the password length, one character threshold at a time:
   ```
   TrackingId=xyz' AND (SELECT 'a' FROM users WHERE username='administrator' AND LENGTH(password)>1)='a
   ```
   Then repeat with `>2`, `>3`, etc. (manually in Burp Repeater, since the length is short). When the "Welcome back" message stops appearing, the previous value was the correct length — in this lab, **20 characters**.

7. Extract the password character by character using `SUBSTRING()`:
   ```
   TrackingId=xyz' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='administrator')='a
   ```
   Send this request to **Burp Intruder**. Mark the final `a` as the payload position:
   ```
   TrackingId=xyz' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='administrator')='§a§
   ```

8. Configure the Intruder attack:
   - **Payloads:** Simple list, lowercase letters `a-z` and digits `0-9` (password is assumed lowercase alphanumeric).
   - **Grep - Match:** add `Welcome back` so Intruder flags which payload produced that string in the response.

9. Run the attack. The row with a tick in the **"Welcome back"** column gives the character at position 1.

10. Repeat for each position (change the `SUBSTRING(password,1,1)` offset from `1` to `2`, `3`, …) until all 20 characters are recovered. This can also be done in a single Intruder run using **Cluster bomb** with two payload positions (offset and character), instead of running the attack once per position.

11. Log in as `administrator` on the **My account** login page using the recovered password.

### Automating it
Wrote a Python script to automate the character-by-character extraction instead of doing it manually through Intruder — send a request per candidate character per position, check for `Welcome back` in the response, and move to the next position once a match is found.

### Note (from the lab)
A more elegant approach than iterating over every character is to perform a **binary search** of the character space (compare against `>` / `<` instead of `=`, halving the search space each request), which needs roughly `log2(36)` requests per character instead of up to 36.

---
### Findings

| Test | Purpose | Signal / observation |
|---|---|---|
| `'1'='1` | Establish a true condition | `Welcome back` appears |
| `'1'='2` | Establish a false condition | `Welcome back` disappears |
| Query `users` | Check for a returned row | True-condition response |
| Find `administrator` | Check for the account | True-condition response |
| `LENGTH(password)>n` | Infer password length | Response changes when condition becomes false |
| `SUBSTRING(password,n,1)` | Infer each character | Matching candidate produces true-condition response |
---

## Key concepts learned
- Blind SQL injection can exist even when database errors and query results are not displayed.
- A change in application behavior can act as a Boolean oracle.
- SQL conditions can be used to infer database information one question at a time.
- LENGTH() can help determine the length of a value.
- SUBSTRING() can help extract a value character by character.
- Burp Repeater is useful for manually validating conditions.
- Burp Intruder can automate candidate testing.
- Response matching with Grep - Match helps identify successful candidates.
- The extraction process can be automated, but the response signal must be reliable.

---
## Questions and answers

**Q1: How do I find out what the back-end DB type is before picking payloads?**
Depends on what the app allows me to probe. Options include: forcing a verbose DB error (if errors are visible) and reading the dialect-specific wording; trying DB-specific functions/syntax one at a time (e.g. `SLEEP()` for MySQL vs `pg_sleep()` for PostgreSQL vs `WAITFOR DELAY` for MSSQL) and seeing which one causes the expected delay; or using known string-concatenation/comment syntax differences (`||` vs `+` vs `CONCAT()`). In a fully blind context with no errors, time-based probing with DB-specific sleep functions is usually the most reliable way to fingerprint the database.

Important distinction:
- Input validation checks whether input meets the application's expected format or rules.
- Parameterized queries keep user-supplied data separate from SQL instructions.
The primary defence against SQL injection is to use parameterized queries (prepared statements), rather than relying only on input validation or filtering special characters.
**Q2: Why does the `TrackingId` cookie accept a query at all? It's an ID — shouldn't it be validated against a fixed format?**
Because the back end builds a SQL string by directly concatenating the cookie value into the query instead of treating it as a plain, opaque identifier. If the value had been validated against an expected format (e.g. a UUID/numeric pattern) and rejected otherwise, or passed as a bound parameter instead of being concatenated into SQL text, the injection would not be possible. This is the same root cause as most SQLi: **untrusted input reaching a query as code instead of as data.**

---

## Remediation

Use parameterized queries or prepared statements for database access.
Do not concatenate untrusted cookie values into SQL statements.
Validate cookie values against the expected format as an additional control.
Apply least-privilege permissions to the database account used by the application.
Avoid exposing database errors to users.
Add security tests for cookie-based input and other user-controlled request parameters.
---

## Key takeaways

| Technique | How it's detected | When to use |
|---|---|---|
| Boolean-based (conditional responses) | Response content/behaviour changes with a true/false condition | Default first approach when a visible behavioural "tell" exists |
| Time-based (delays) | Response time changes based on a conditional `SLEEP()`/`WAITFOR` | When there's no visible difference in the response content |
| OAST (out-of-band) | External DNS/HTTP interaction received on a listener | When neither boolean nor time-based differences are observable |
